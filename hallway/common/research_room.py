"""Drug-only Band research rooms; Scribe alone relays results into the case."""
import asyncio
import inspect
import json
import logging
import os
import re
from urllib.parse import urlparse
from uuid import UUID

from band.client.rest import DEFAULT_REQUEST_OPTIONS
from band.runtime.tools.agent import AgentTools
from band_rest.agent_api_chats import RenameAgentChatRequestChat
from hallway.common.brief import Brief, digest, identifier_violations, normalize

MARKER = 'SAFESCRIBE-RESEARCH/1\n'
AUTHORS = {'RESEARCH_LINK': 'scribe', 'RESEARCH_REQUEST': 'scribe',
           'RESEARCH_RESULT': 'researcher', 'RESEARCH_ENRICHMENT': 'scribe'}
# A deliberately bounded medication vocabulary, not a free-text outbound query.
# Unknown medications are reported as unsupported, never sent as arbitrary text.
DRUGS = ('warfarin', 'ciprofloxacin', 'enoxaparin', 'furosemide', 'metformin',
         'empagliflozin', 'lisinopril', 'aspirin', 'heparin', 'insulin', 'apixaban',
         'rivaroxaban', 'atorvastatin', 'amlodipine', 'metoprolol', 'amoxicillin',
         'doxycycline', 'acetaminophen', 'ibuprofen', 'omeprazole')


def drug_names(brief: Brief, recording: dict) -> list[str]:
    transcript=normalize(recording['transcript'])
    names=set()
    for item in brief.meds:
        quote=normalize(item.quote)
        if not quote or quote not in transcript:
            raise ValueError('Medication quote is not backed by the transcript')
        for drug in DRUGS:
            if re.search(r'\b'+re.escape(drug)+r'\b',quote):
                names.add(drug)
        if re.search(r'\bcipro\b',quote):
            names.add('ciprofloxacin')
    result=sorted(names)
    if identifier_violations({'drugs':result},recording):
        raise ValueError('Drug-only request matched a direct identifier; research blocked')
    return result


def decode_research(messages: list[dict], ids: dict) -> list[dict]:
    records=[]
    for message in messages:
        content=message.get('content','')
        if not isinstance(content,str):
            continue
        markers=list(re.finditer(r'(?m)^SAFESCRIBE-RESEARCH/1$',content))
        if len(markers)!=1:
            continue
        try:
            payload=json.loads(content[markers[0].end():])
        except ValueError:
            continue
        if not isinstance(payload,dict):
            continue
        role=AUTHORS.get(payload.get('kind'))
        if (not role or not ids.get(role) or message.get('sender_id')!=ids[role]
            or str(message.get('sender_type','')).casefold()!='agent' or not message.get('id')):
            continue
        records.append(dict(payload,message_id=message['id']))
    return records


async def _records(tools,ids):
    from hallway.common.room import raw_messages
    return decode_research(await raw_messages(tools),ids)


async def _send(tools,kind,payload,recipient,ids):
    await tools.get_participants()
    peer=next((p for p in tools.participants if p['id']==ids.get(recipient)),None)
    if not peer or not peer.get('handle'):
        raise ValueError('Missing actual research recipient in Band roster')
    content=f'**{kind}** — Drug research status.\n\n'+MARKER+json.dumps({'kind':kind,**payload})
    await tools.send_message(content,mentions=[{'id':peer['id'],'handle':peer['handle']}])


async def request_research(case_tools,ids,brief: Brief,recording: dict) -> dict:
    """Scribe: recruit only into a new separate room and send names, no clinical text."""
    drugs=drug_names(brief,recording)
    if not drugs:
        return {'status':'unavailable' if brief.meds else 'skipped','facts':[],
                'reason':'No supported drug names' if brief.meds else 'No medications'}
    key=digest({'drugs':drugs})
    links=[r for r in await _records(case_tools,ids) if r['kind']=='RESEARCH_LINK' and r.get('drugs_digest')==key]
    if not ids.get('researcher'):
        raise ValueError('Drug research requires a configured Researcher identity')
    await case_tools.get_participants()
    if ids['researcher'] in {p['id'] for p in case_tools.participants}:
        raise ValueError('Researcher must never be a case-room participant')
    if links:
        room_id=links[-1]['research_room_id']
    else:
        found=False
        for page in range(1,21):
            peers=await case_tools.lookup_peers(page=page,page_size=100)
            if any(p.id==ids['researcher'] for p in (peers.data or [])):
                found=True;break
            if page>=((peers.metadata.total_pages if peers.metadata else None) or 1):
                break
        if not found:
            raise ValueError('Researcher not found through Band peer discovery')
        room_id=await case_tools.create_chatroom()
        # Durable Band checkpoint precedes all remaining room setup operations.
        await _send(case_tools,'RESEARCH_LINK',{'research_room_id':room_id,'drugs_digest':key},'critic',ids)
    await case_tools.rest.agent_api_chats.rename_agent_chat(room_id,
        chat=RenameAgentChatRequestChat(title=f'Safe Scribe research {room_id[:8]}'),request_options=DEFAULT_REQUEST_OPTIONS)
    room=AgentTools(room_id,case_tools.rest,agent_id=ids['scribe'])
    await room.get_participants()
    roster={p['id'] for p in room.participants}
    if ids['scribe'] not in roster or not roster<={ids['scribe'],ids['researcher']}:
        raise ValueError('Research room has unexpected participants')
    if ids['researcher'] not in roster:
        await room.add_participant(ids['researcher'])
    request={'case_room_id':str(UUID(case_tools.room_id)),'drugs':drugs,'drugs_digest':key}
    previous=[r for r in await _records(room,ids) if r['kind']=='RESEARCH_REQUEST']
    if previous:
        if len(previous)!=1 or any(previous[0].get(field)!=value for field,value in request.items()):
            raise ValueError('Conflicting research request in checkpointed room')
    else:
        await _send(room,'RESEARCH_REQUEST',request,'researcher',ids)
    return {'status':'pending','room_id':room_id,'drugs_digest':key}


async def read_research(tools,ids) -> dict:
    """Read only an authenticated Scribe drug request in a Scribe/Researcher room."""
    await tools.get_participants()
    if {p['id'] for p in tools.participants}!={ids.get('scribe'),ids.get('researcher')}:
        raise ValueError('Research room must contain only Scribe and Researcher')
    requests=[r for r in await _records(tools,ids) if r['kind']=='RESEARCH_REQUEST']
    if len(requests)!=1:
        raise ValueError('Exactly one authenticated research request is required')
    request=requests[0]
    if set(request)!={'kind','case_room_id','drugs','drugs_digest','message_id'}:
        raise ValueError('Unexpected research fields; refusing possible clinical context')
    drugs=request['drugs']
    if (not isinstance(drugs,list) or not drugs or drugs!=sorted(set(drugs))
        or any(drug not in DRUGS for drug in drugs) or request['drugs_digest']!=digest({'drugs':drugs})):
        raise ValueError('Research request must contain supported drug names only')
    try:
        valid_case=str(UUID(request['case_room_id']))
    except (ValueError,TypeError,AttributeError):
        raise ValueError('Research request has invalid case routing') from None
    if valid_case!=request['case_room_id'] or valid_case==tools.room_id:
        raise ValueError('Research request has invalid case routing')
    return request


def _clean_fact(value,drug):
    if not isinstance(value,dict):
        return None
    if not all(isinstance(value.get(key),str) and value[key].strip() for key in ('title','url','snippet')):
        return None
    url=urlparse(value['url'])
    if url.scheme not in ('http','https') or not url.netloc or url.username or url.password:
        return None
    return {key:value[key] for key in ('title','url','snippet')} | {'drug':drug}


async def _lookup_fact(drug):
    from hallway.research.brave import fact
    if inspect.iscoroutinefunction(fact):
        return await fact(drug)
    return await asyncio.to_thread(fact,drug)


async def research_drugs(tools,ids) -> dict:
    """Researcher: search authenticated drug names only and report sources or failure."""
    request=await read_research(tools,ids)
    mode='live' if os.getenv('BRAVE_API_KEY','').strip() and os.getenv('MOCK_BRAVE','0')!='1' else 'mock'
    existing=[r for r in await _records(tools,ids) if r['kind']=='RESEARCH_RESULT' and r.get('drugs_digest')==request['drugs_digest'] and r.get('mode')==mode]
    if existing:
        return existing[-1]
    facts=[]
    async def lookup(drug):
        try:
            return _clean_fact(await _lookup_fact(drug),drug)
        except Exception as exc:
            logging.warning('Brave fact failed error=%s',type(exc).__name__)
            return None
    # No synthetic search facts may enter the live evidence path. Missing keys
    # are explicitly mock/unavailable, even if the wrapper has an implicit mock.
    if mode=='live':
        facts=[value for value in await asyncio.gather(*(lookup(drug) for drug in request['drugs'])) if value]
    payload={'drugs_digest':request['drugs_digest'],'facts':facts,
             'status':'ready' if facts else 'unavailable','mode':mode}
    await _send(tools,'RESEARCH_RESULT',payload,'scribe',ids)
    return payload


async def relay_research(research_tools,ids) -> dict:
    """Scribe: validate Researcher's room result, then relay through the case room."""
    from hallway.common.room import raw_messages,decode_messages,case_state
    request=await read_research(research_tools,ids)
    results=[r for r in await _records(research_tools,ids) if r['kind']=='RESEARCH_RESULT' and r.get('drugs_digest')==request['drugs_digest']]
    if not results:
        return {'status':'pending','facts':[]}
    case=AgentTools(request['case_room_id'],research_tools.rest,agent_id=ids['scribe'])
    messages=await raw_messages(case)
    links=[r for r in decode_research(messages,ids) if r['kind']=='RESEARCH_LINK' and r.get('research_room_id')==research_tools.room_id and r.get('drugs_digest')==request['drugs_digest']]
    if not links:
        raise ValueError('Research room has no authenticated link from target case')
    state=case_state(decode_messages(messages,ids))
    result=results[-1]
    facts=result.get('facts')
    if not isinstance(facts,list) or any(not isinstance(f,dict) or f.get('drug') not in request['drugs'] or _clean_fact(f,f.get('drug'))!=f for f in facts):
        raise ValueError('Research result lacks valid drug/source fields')
    if result.get('mode') not in ('live','mock') or result.get('status') not in ('ready','unavailable'):
        raise ValueError('Research result lacks explicit completion status')
    if identifier_violations({'facts':facts},state['recording']):
        raise ValueError('Research facts contain case identifiers; relay blocked')
    payload={'drugs_digest':request['drugs_digest'],'research_room_id':research_tools.room_id,
             'source_message_id':result['message_id'],'facts':facts,'status':result['status'],'mode':result['mode']}
    previous=[r for r in decode_research(messages,ids) if r['kind']=='RESEARCH_ENRICHMENT' and r.get('source_message_id')==result['message_id'] and r.get('research_room_id')==research_tools.room_id]
    if not previous:
        await _send(case,'RESEARCH_ENRICHMENT',payload,'critic',ids)
    return payload


def research_for_review(messages,ids,brief: Brief,recording: dict) -> dict:
    """Critic: require sourced enrichment or an explicit failure before approval."""
    drugs=drug_names(brief,recording)
    if not drugs:
        return {'status':'unavailable' if brief.meds else 'skipped','facts':[]}
    key=digest({'drugs':drugs})
    records=decode_research(messages,ids)
    links={r.get('research_room_id') for r in records if r['kind']=='RESEARCH_LINK' and r.get('drugs_digest')==key}
    relays=[r for r in records if r['kind']=='RESEARCH_ENRICHMENT' and r.get('drugs_digest')==key and r.get('research_room_id') in links]
    if not relays:
        return {'status':'pending','facts':[]}
    result=relays[-1]
    if result.get('mode')=='mock':
        return {'status':'unavailable','facts':[],'reason':'Mock research is not live evidence'}
    if result.get('mode')!='live' or result.get('status') not in ('ready','unavailable'):
        raise ValueError('Research completion metadata is invalid')
    facts=result.get('facts')
    if not isinstance(facts,list) or any(not isinstance(f,dict) or f.get('drug') not in drugs or _clean_fact(f,f.get('drug'))!=f for f in facts):
        raise ValueError('Research source validation failed')
    if identifier_violations({'facts':facts},recording):
        raise ValueError('Research contains direct identifiers')
    return {'status':result['status'],'facts':facts}
