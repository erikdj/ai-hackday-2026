"""Offline adversarial protocol tests; these are NOT a live sponsor demo."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from hallway.common.brief import Brief, digest, validate_brief
from hallway.common.room import (PREFIX, approved_payload, case_state, decode_messages,
                                 review, submit_brief)
from hallway.common.runtime import make_tools

IDS={r:r+'-id' for r in ('desk','scribe','critic','researcher','grapher','closer')}
RECORDING=json.loads((Path(__file__).parents[1]/'fixtures'/'transcript_1.json').read_text())
RECORDING['human_id']='human-id'
BASIC={'people':[{'name':'Erik Jones'},{'name':'Maya Chen','company':'Nebius'}],
 'companies':[{'name':'Nebius','domain':'nebius.com'}],
 'claims':[{'text':'Maya works at Nebius','quote':'I am Maya Chen, a developer advocate at Nebius.','speaker':'Maya Chen'}],
 'commitments':[{'text':'Send demo link','quote':'I will send Maya our demo link tomorrow.','owner':'Erik Jones'},
 {'text':'Send the deck','quote':'Someone should send them the deck.','owner':None}]}


def record(kind, payload, author):
    return {'id':str(id(payload)), 'sender_id':IDS.get(author,author), 'sender_type':'Agent',
            'content':PREFIX+json.dumps({'kind':kind,**payload}),
            'mentions':[{'id':IDS[r]} for r in {'TRANSCRIPT':['scribe','critic'], 'BRIEF':['critic','researcher'], 'ENRICHMENT':['critic','scribe'], 'APPROVAL':['grapher','closer','scribe']}.get(kind,[])]}


class FakeBand:
    """In-memory transport double only for tests; never imported by runtime."""
    def __init__(self):
        self.room_id='case-1'; self.role='scribe'; self.added=[]; self.filter_mentions=False; self.rest=self; self.rooms={self.room_id:self}
        self.messages=[record('TRANSCRIPT',{'recording':RECORDING},'desk')]
        self.participants=[{'id':v,'handle':'@team/'+k,'type':'Agent'} for k,v in IDS.items()]
        self.participants.append({'id':'human-id','handle':'@human','type':'User'})
    async def fetch_room_context(self,**kwargs):
        assert kwargs['room_id']==self.room_id
        messages=self.messages
        if self.filter_mentions:
            identity=IDS[self.role]
            messages=[m for m in messages if m.get('sender_id')==identity or identity in [x['id'] for x in m.get('mentions',[])]]
        return {'data':messages,'meta':{'total_pages':1}}
    async def get_participants(self): return self.participants
    async def lookup_peers(self): return {}
    async def add_participant(self,identifier):
        self.added.append(identifier); return {'status':'added'}
    async def create_chatroom(self):
        room_id='case-'+str(len(self.rooms)+1); room=FakeBand();room.messages=[];room.room_id=room_id;room.role=self.role;room.rest=self;room.rooms=self.rooms;self.rooms[room_id]=room
        return room_id
    async def send_event(self,content,message_type):
        if message_type=='task':
            self.messages.append({'id':str(len(self.messages)), 'sender_id':IDS[self.role], 'content':content})
        return {}
    async def send_message(self,content,mentions):
        self.messages.append({'id':str(len(self.messages)), 'sender_id':IDS[self.role],
                              'content':content, 'mentions':mentions})
        return {}


class ValidationTests(unittest.TestCase):
    def test_unowned_is_vetoed(self):
        self.assertTrue(any('named owner' in e for e in validate_brief(Brief.model_validate(BASIC),RECORDING,[])))
    def test_quote_and_url_fail_closed(self):
        b=copy.deepcopy(BASIC);b['claims'][0]['quote']='Invented quotation'
        reasons=validate_brief(Brief.model_validate(b),RECORDING,[{'url':'javascript:bad'}])
        self.assertTrue(any('quote not found' in e for e in reasons))
        self.assertTrue(any('URL required' in e for e in reasons))
    def test_fabricated_owner_vetoed(self):
        b=copy.deepcopy(BASIC);b['commitments'][1]['owner']='Erik Jones'
        self.assertTrue(any('fabricated owner' in e for e in validate_brief(Brief.model_validate(b),RECORDING,[])))
    def test_transcript_authenticity(self):
        forged=record('TRANSCRIPT',{'recording':{'transcript':'forged'}},'scribe')
        self.assertEqual([],decode_messages([forged],IDS))
    def test_native_tools_not_exposed_and_room_not_model_parameter(self):
        for role in IDS:
            tools=make_tools(role,{},IDS)
            for tool in tools:
                self.assertNotIn('config',tool.args)
                self.assertNotIn('room_id',tool.args)
                self.assertNotIn(tool.name,('band_add_participant','band_create_chatroom','band_send_message'))
    def test_approval_requires_authenticated_critic(self):
        message=record('APPROVAL',{'brief':BASIC},'scribe')
        with self.assertRaises(ValueError): approved_payload(decode_messages([message],IDS))


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_veto_repair_approve_and_roster(self):
        band=FakeBand();band.filter_mentions=True
        await submit_brief(band,IDS,Brief.model_validate(BASIC))
        self.assertEqual(band.added,[IDS['researcher']])
        band.role='critic'
        veto=await review(band,IDS,True,[])
        self.assertEqual(veto['verdict'],'VETO')
        self.assertNotIn(IDS['closer'],band.added)
        fixed=copy.deepcopy(BASIC); unresolved=fixed['commitments'].pop()
        unresolved.pop('owner');fixed['unresolved_suggestions']=[unresolved]
        band.role='scribe'; await submit_brief(band,IDS,Brief.model_validate(fixed))
        band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['status'],'WAITING_FOR_ENRICHMENT')
        band.messages.append(record('ENRICHMENT',{'facts':[], 'companies_digest':digest({'companies':fixed['companies']})},'researcher'))
        verdict=await review(band,IDS,True,[])
        self.assertEqual(verdict['status'],'APPROVED')
        self.assertIn(IDS['closer'],band.added)
        band.role='closer'
        visible=(await band.fetch_room_context(room_id=band.room_id))['data']
        visible_records=decode_messages(visible,IDS)
        self.assertFalse(any(r['kind']=='TRANSCRIPT' for r in visible_records))
        self.assertFalse(any(r['kind']=='BRIEF' for r in visible_records))
        payload=approved_payload(visible_records)
        self.assertEqual(payload['revision'],2)
        self.assertEqual(payload['brief']['unresolved_suggestions'][0]['quote'],'Someone should send them the deck.')
    async def test_fixture_intake_authenticated_and_idempotent_per_human_message(self):
        lobby=FakeBand();lobby.messages=[];lobby.role='desk';lobby.room_id='lobby';lobby.rooms={'lobby':lobby}
        holder={'agent':SimpleNamespace(runtime=SimpleNamespace(link=SimpleNamespace(rest=lobby)))}
        ingest=next(t for t in make_tools('desk',holder,IDS) if t.name=='band_ingest_fixture')
        config={'configurable':{'thread_id':'lobby'}}
        def bind(room_id,rest,agent_id): return rest.rooms[room_id]
        with patch('hallway.common.runtime.AgentTools',side_effect=bind):
            lobby.messages.append({'id':'forged','sender_id':IDS['scribe'],'sender_type':'Agent','content':'/ingest fixture:transcript_1'})
            with self.assertRaisesRegex(ValueError,'authenticated human'):
                await ingest.ainvoke({'fixture':'transcript_1'},config=config)
            lobby.messages.append({'id':'human-request-1','sender_id':'human-id','sender_type':'User','content':'/ingest fixture:transcript_1'})
            first=await ingest.ainvoke({'fixture':'transcript_1'},config=config)
            duplicate=await ingest.ainvoke({'fixture':'transcript_1'},config=config)
            self.assertEqual(first['room_id'],duplicate['room_id'])
            self.assertEqual(len(lobby.rooms),2)
            lobby.messages.append({'id':'human-request-2','sender_id':'human-id','sender_type':'User','content':'/ingest fixture:transcript_1'})
            second=await ingest.ainvoke({'fixture':'transcript_1'},config=config)
            self.assertNotEqual(first['room_id'],second['room_id'])
            with self.assertRaisesRegex(ValueError,'differs'):
                await ingest.ainvoke({'fixture':'transcript_2'},config=config)
    async def test_no_company_does_not_recruit_researcher(self):
        band=FakeBand()
        recording=json.loads((Path(__file__).parents[1]/'fixtures'/'transcript_2.json').read_text())
        band.messages=[record('TRANSCRIPT',{'recording':recording},'desk')]
        brief={'people':[{'name':'Erik Jones'},{'name':'Jordan Lee'}], 'companies':[],
               'commitments':[{'text':'Send talk notes','quote':'I will send Jordan the public talk notes tomorrow.','owner':'Erik Jones'}]}
        await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        await review(band,IDS,True,[])
        self.assertNotIn(IDS['researcher'],band.added)
        self.assertIn(IDS['closer'],band.added)
    async def test_repair_cannot_silently_drop_commitment(self):
        band=FakeBand(); await submit_brief(band,IDS,Brief.model_validate(BASIC));band.role='critic'
        await review(band,IDS,True,[]);band.role='scribe'
        bad=copy.deepcopy(BASIC);bad['commitments'].pop()
        with self.assertRaisesRegex(ValueError,'preserve'):
            await submit_brief(band,IDS,Brief.model_validate(bad))
    async def test_semantic_veto_cannot_be_overridden_by_valid_quotes(self):
        band=FakeBand();b=copy.deepcopy(BASIC);b['commitments'].pop()
        await submit_brief(band,IDS,Brief.model_validate(b));band.role='critic'
        verdict=await review(band,IDS,False,['Claim misinterprets source'])
        self.assertEqual(verdict['verdict'],'VETO');self.assertNotIn(IDS['closer'],band.added)
    async def test_two_repairs_escalate_to_human(self):
        band=FakeBand()
        for revision in range(1,4):
            band.role='scribe';await submit_brief(band,IDS,Brief.model_validate(BASIC))
            band.role='critic';verdict=await review(band,IDS,True,[])
        self.assertTrue(verdict['escalate'])
        self.assertIn('human-id',[m['id'] for m in band.messages[-1]['mentions']])
        band.role='scribe'
        with self.assertRaisesRegex(ValueError,'exhausted'):
            await submit_brief(band,IDS,Brief.model_validate(BASIC))
        self.assertNotIn(IDS['closer'],band.added)


if __name__=='__main__': unittest.main()
