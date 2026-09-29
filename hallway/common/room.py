"""Band is the durable protocol: no shared local state or out-of-band handoffs."""
import asyncio
import json
import logging
from band.runtime.tools.agent import AgentTools
from hallway.common.brief import Brief, digest, normalize, validate_brief

PREFIX = 'HALLWAY/1\n'
AUTHORS = {'TRANSCRIPT': 'desk', 'BRIEF': 'scribe', 'ENRICHMENT': 'researcher',
           'VERDICT': 'critic', 'APPROVAL': 'critic', 'HANDOFF': 'scribe',
           'CASE_CREATED': 'desk', 'OUTPUT': None}


def decode_messages(messages: list[dict], ids: dict[str, str]) -> list[dict]:
    records = []
    for message in messages:
        content = message.get('content', '')
        if not isinstance(content, str) or not content.startswith(PREFIX):
            continue
        try:
            value = json.loads(content[len(PREFIX):])
        except (ValueError, TypeError):
            continue
        if not isinstance(value, dict):
            continue
        author = AUTHORS.get(value.get('kind'))
        if not author or message.get('sender_id') != ids[author]:
            continue
        value = dict(value, message_id=message.get('id'))
        records.append(value)
    return records


async def raw_messages(tools: AgentTools) -> list[dict]:
    messages = []
    page = 1
    while True:
        data = await tools.fetch_room_context(room_id=tools.room_id, page=page, page_size=100)
        messages.extend(data['data'])
        if page >= data['meta'].get('total_pages', 1):
            break
        page += 1
        if page > 20:
            raise ValueError('Case context exceeded safe size; escalate to human')
    return messages


async def room_records(tools: AgentTools, ids: dict[str, str]) -> list[dict]:
    return decode_messages(await raw_messages(tools), ids)


def case_state(records: list[dict]) -> dict:
    sources = [r for r in records if r['kind'] == 'TRANSCRIPT']
    if not sources:
        raise ValueError('No authenticated Desk transcript in this room')
    source = sources[0]
    if any(r['recording'] != source['recording'] for r in sources):
        raise ValueError('Conflicting source transcripts; human review required')
    briefs = [r for r in records if r['kind'] == 'BRIEF']
    for revision, brief in enumerate(briefs, 1):
        if brief.get('revision') != revision:
            raise ValueError('Invalid or duplicate revision sequence; human review required')
    verdicts = [r for r in records if r['kind'] == 'VERDICT']
    enrichments = [r for r in records if r['kind'] == 'ENRICHMENT']
    return {'recording':source['recording'], 'brief': briefs[-1] if briefs else None,
            'verdicts':verdicts, 'enrichment': enrichments[-1] if enrichments else None,
            'approved': any(r['kind'] == 'APPROVAL' for r in records)}


async def post(tools: AgentTools, kind: str, payload: dict, roles: list[str], ids: dict[str, str]):
    content = PREFIX + json.dumps({'kind':kind, **payload}, ensure_ascii=False)
    if not roles:
        # SDK messages require recipients; status is a durable Band task event.
        return await tools.send_event(content=content, message_type='task')
    await tools.get_participants()
    participants = {p['id']:p for p in tools.participants}
    mentions = []
    for role in roles:
        participant = participants.get(ids[role])
        if not participant or not participant.get('handle'):
            raise ValueError(f'Missing actual Band participant handle for {role}')
        mentions.append({'id':ids[role], 'handle':participant['handle']})
    return await tools.send_message(content, mentions=mentions)


async def action_event(tools: AgentTools, summary: str):
    await tools.send_event(content=summary, message_type='thought')


async def recruit(tools: AgentTools, role: str, ids: dict[str,str]):
    await tools.send_event(content=json.dumps({'name':'band_add_participant','role':role}), message_type='tool_call')
    result = await tools.add_participant(ids[role])
    await tools.send_event(content=json.dumps({'name':'band_add_participant','role':role,'status':result.get('status')}), message_type='tool_result')
    return result


async def submit_brief(tools: AgentTools, ids: dict[str,str], brief: Brief) -> dict:
    state = case_state(await room_records(tools, ids))
    if state['approved']:
        raise ValueError('Case already approved; start a new case to revise it')
    if not (brief.people or brief.claims or brief.commitments or brief.unresolved_suggestions):
        raise ValueError('Empty brief is not a faithful extraction')
    previous = state['brief']
    revision = previous['revision'] + 1 if previous else 1
    if previous:
        matching = [v for v in state['verdicts'] if v['revision'] == previous['revision']]
        if not matching or matching[-1]['verdict'] != 'VETO':
            raise ValueError('A revision requires Critic VETO of the current brief')
        old = Brief.model_validate(previous['brief'])
        retained = brief.commitments + brief.unresolved_suggestions + brief.next_steps
        for commitment in old.commitments + old.next_steps:
            if not any(normalize(item.text) == normalize(commitment.text) for item in retained):
                raise ValueError('Repair must preserve each commitment as an owned action or unresolved suggestion')
            if commitment.owner is None and normalize(commitment.quote) in normalize(state['recording']['transcript']):
                if not any(normalize(item.quote) == normalize(commitment.quote) for item in retained):
                    raise ValueError('Repair must retain authentic quote of unowned suggestion')
        if {normalize(c.name) for c in old.companies} - {normalize(c.name) for c in brief.companies}:
            raise ValueError('Repair cannot silently remove a named company')
        if revision > 3:
            raise ValueError('Two repair rounds exhausted; human intervention required')
    recipients = ['critic']
    if brief.companies:
        await tools.send_event(content='{"name":"band_lookup_peers"}', message_type='tool_call')
        await tools.lookup_peers()
        await recruit(tools, 'researcher', ids)
        recipients.append('researcher')
    payload = {'revision':revision,'brief':brief.model_dump(), 'digest':digest(brief.model_dump())}
    await action_event(tools, f'Publishing transcript-grounded brief revision {revision}')
    await post(tools, 'BRIEF', payload, recipients, ids)
    return payload


async def review(tools: AgentTools, ids: dict[str,str], approve: bool, judgment_reasons: list[str]) -> dict:
    state = case_state(await room_records(tools, ids))
    current = state['brief']
    if not current:
        raise ValueError('No authenticated Scribe brief')
    if state['approved']:
        return {'status':'already approved'}
    prior = [v for v in state['verdicts'] if v['revision'] == current['revision']]
    if prior and prior[-1]['verdict'] == 'VETO':
        return {'status':'already reviewed', 'verdict':prior[-1]}
    brief = Brief.model_validate(current['brief'])
    enrichment = state['enrichment']
    if enrichment and enrichment.get('companies_digest') != digest({'companies':current['brief'].get('companies', [])}):
        enrichment = None
    facts = enrichment.get('facts', []) if enrichment else []
    reasons = validate_brief(brief, state['recording'], facts)
    if not approve:
        reasons.extend(judgment_reasons or ['Critic judgment rejected unsupported interpretation'])
    if reasons:
        verdict = {'verdict':'VETO','revision':current['revision'],'reasons':reasons,
                   'escalate':current['revision'] >= 3}
        await action_event(tools, 'Vetoing unsupported or unowned material; downstream roster remains closed')
        recipients = ['scribe']
        if verdict['escalate']:
            human_id = state['recording'].get('human_id')
            if not human_id:
                raise ValueError('Human escalation recipient missing; room remains blocked')
            ids = dict(ids, human=human_id)
            recipients.append('human')
        await post(tools,'VERDICT', verdict, recipients, ids)
        return verdict
    if brief.companies and enrichment is None:
        return {'status':'WAITING_FOR_ENRICHMENT', 'instruction':'Wait for Researcher; do not approve yet'}
    # Publish VERDICT before roster change. Workers receive the exact authenticated
    # APPROVAL after joining because Band only delivers mentioned context.
    payload = {'revision':current['revision'], 'digest':current['digest'],
               'brief':current['brief'], 'enrichment':facts, 'recording':state['recording']}
    if not prior:
        await post(tools,'VERDICT',{'verdict':'APPROVE','revision':current['revision'],'reasons':[]},['scribe'],ids)
    await action_event(tools, 'Validated quotes, owners and sources; admitting Grapher and Closer')
    for role in ('grapher','closer'):
        await recruit(tools, role, ids)
    await post(tools,'APPROVAL',payload,['grapher','closer','scribe'],ids)
    return {'status':'APPROVED', 'revision':current['revision']}


def approved_payload(records: list[dict]) -> dict:
    approvals = [r for r in records if r['kind'] == 'APPROVAL']
    if not approvals:
        raise ValueError('No authenticated Critic APPROVAL; execution forbidden')
    payload = approvals[-1]
    brief = Brief.model_validate(payload['brief'])
    if digest(brief.model_dump()) != payload['digest']:
        raise ValueError('Approval digest mismatch')
    reasons = validate_brief(brief, payload['recording'], payload['enrichment'])
    if reasons:
        raise ValueError('Approval failed deterministic revalidation')
    return payload
