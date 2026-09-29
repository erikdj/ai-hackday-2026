"""Offline drug-room boundary checks; no live Band or Brave claims."""
import copy
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from hallway.common.brief import Brief
from hallway.common.room import PREFIX
from hallway.common import research_room as research

IDS={role:role+'-id' for role in ('desk','scribe','critic','researcher','grapher','closer')}
RECORDING={'transcript':'Patient name: Taylor Example\nDOB: 1974-04-03\nOn warfarin and ciprofloxacin.', 'pseudo_id':'p-test'}
BRIEF={'patient':{'pseudo_id':'p-test'},'meds':[{'text':'Warfarin and ciprofloxacin','quote':'On warfarin and ciprofloxacin.'}]}
CASE='10000000-0000-4000-8000-000000000001'
FACT={'title':'Public drug information','url':'https://drugs.test/drug','snippet':'Drug information for professional review.','source':'brave','mock':False}


class Backend:
    def __init__(self):
        self.rooms={CASE:{'participants':['desk','scribe','critic'], 'messages':[]}}
        self.agent_api_chats=SimpleNamespace(rename_agent_chat=AsyncMock())
        self.serial=0
        self.rooms[CASE]['messages'].append({'id':'transcript','sender_id':IDS['desk'],'sender_type':'Agent',
            'content':PREFIX+json.dumps({'kind':'TRANSCRIPT','recording':RECORDING}),
            'mentions':[{'id':IDS['scribe']},{'id':IDS['critic']}]})
    def bound(self,room_id,rest=None,agent_id=None):
        role=next(role for role,value in IDS.items() if value==agent_id)
        return Room(self,room_id,role)


class Room:
    def __init__(self,backend,room_id,role):
        self.rest=backend;self.room_id=room_id;self.role=role
    @property
    def participants(self):
        return [{'id':IDS[role],'handle':'@team/'+role,'type':'Agent'} for role in self.rest.rooms[self.room_id]['participants']]
    async def get_participants(self): return self.participants
    async def lookup_peers(self,**kwargs):
        return SimpleNamespace(data=[SimpleNamespace(id=IDS['researcher'])],metadata=SimpleNamespace(total_pages=1))
    async def create_chatroom(self):
        name='research-'+str(len(self.rest.rooms))
        self.rest.rooms[name]={'participants':[self.role],'messages':[]}
        return name
    async def add_participant(self,identifier):
        role=next(role for role,value in IDS.items() if value==identifier)
        self.rest.rooms[self.room_id]['participants'].append(role)
    async def fetch_room_context(self,**kwargs):
        messages=[m for m in self.rest.rooms[self.room_id]['messages'] if m['sender_id']==IDS[self.role]
                  or IDS[self.role] in [p['id'] for p in m['mentions']]]
        return {'data':messages,'meta':{'total_pages':1}}
    async def send_message(self,content,mentions):
        self.rest.serial+=1
        self.rest.rooms[self.room_id]['messages'].append({'id':str(self.rest.serial),'sender_id':IDS[self.role],
            'sender_type':'Agent','content':content,'mentions':mentions})


class ResearchBoundaryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.backend=Backend()
        self.case=Room(self.backend,CASE,'scribe')
        self.brief=Brief.model_validate(BRIEF)
        self.patch=patch.object(research,'AgentTools',side_effect=self.backend.bound)
        self.patch.start();self.addCleanup(self.patch.stop)
        self.env=patch.dict(os.environ,{'MOCK_BRAVE':'0','BRAVE_API_KEY':'test-only'});self.env.start();self.addCleanup(self.env.stop)
    async def recruit(self):
        result=await research.request_research(self.case,IDS,self.brief,RECORDING)
        return Room(self.backend,result['room_id'],'researcher')
    async def test_runtime_recruitment_sends_only_drug_names_and_routing(self):
        room=await self.recruit()
        request=await research.read_research(room,IDS)
        self.assertEqual(request['drugs'],['ciprofloxacin','warfarin'])
        self.assertEqual(set(request),{'kind','case_room_id','drugs','drugs_digest','message_id'})
        serialized=json.dumps(self.backend.rooms[room.room_id]['messages'])
        for private in ('Taylor','1974','p-test','On warfarin'):
            self.assertNotIn(private,serialized)
        self.assertEqual(self.backend.rooms[room.room_id]['participants'],['scribe','researcher'])
        self.assertNotIn('researcher',self.backend.rooms[CASE]['participants'])
        again=await research.request_research(self.case,IDS,self.brief,RECORDING)
        self.assertEqual(again['room_id'],room.room_id)
        self.assertEqual(len(self.backend.rooms),2)
    async def test_no_drug_and_unknown_drug_never_recruit(self):
        for meds,status in [([], 'skipped'),([{'text':'Unknown drug','quote':'Patient name: Taylor Example'}],'unavailable')]:
            brief=Brief.model_validate({'patient':{'pseudo_id':'p-test'},'meds':meds})
            result=await research.request_research(self.case,IDS,brief,RECORDING)
            self.assertEqual(result['status'],status)
        self.assertEqual(len(self.backend.rooms),1)
    async def test_live_source_handoff_requires_researcher_then_scribe_relay(self):
        room=await self.recruit()
        messages=self.backend.rooms[CASE]['messages']
        self.assertEqual(research.research_for_review(messages,IDS,self.brief,RECORDING)['status'],'pending')
        with patch.object(research,'_lookup_fact',new=AsyncMock(return_value=FACT)) as lookup:
            result=await research.research_drugs(room,IDS)
        self.assertEqual({call.args[0] for call in lookup.call_args_list},{'warfarin','ciprofloxacin'})
        self.assertEqual(result['status'],'ready')
        # Researcher result cannot directly authorize a case it never joined.
        self.assertEqual(research.research_for_review(messages,IDS,self.brief,RECORDING)['status'],'pending')
        await research.relay_research(Room(self.backend,room.room_id,'scribe'),IDS)
        ready=research.research_for_review(messages,IDS,self.brief,RECORDING)
        self.assertEqual(ready['status'],'ready');self.assertEqual(len(ready['facts']),2)
        size=len(messages)
        await research.relay_research(Room(self.backend,room.room_id,'scribe'),IDS)
        self.assertEqual(len(messages),size)
    async def test_checkpoint_retries_invitation_and_request_without_duplicate_room(self):
        original=Room.add_participant
        with patch.object(Room,'add_participant',new=AsyncMock(side_effect=RuntimeError('interrupted'))):
            with self.assertRaises(RuntimeError):
                await self.recruit()
        self.assertEqual(len(self.backend.rooms),2)
        with patch.object(research,'_send',wraps=research._send) as send:
            room=await self.recruit()
        self.assertEqual(len(self.backend.rooms),2)
        self.assertEqual(self.backend.rooms[room.room_id]['participants'],['scribe','researcher'])
        self.assertEqual(sum(call.args[1]=='RESEARCH_REQUEST' for call in send.call_args_list),1)
        await self.recruit()
        messages=self.backend.rooms[room.room_id]['messages']
        self.assertEqual(sum(r['kind']=='RESEARCH_REQUEST' for r in research.decode_research(messages,IDS)),1)
    async def test_missing_key_mock_result_can_be_retried_live(self):
        room=await self.recruit()
        with patch.dict(os.environ,{'BRAVE_API_KEY':''}),patch.object(research,'_lookup_fact',new=AsyncMock()) as lookup:
            result=await research.research_drugs(room,IDS)
            lookup.assert_not_awaited()
        self.assertEqual(result['mode'],'mock');self.assertEqual(result['facts'],[])
        with patch.object(research,'_lookup_fact',new=AsyncMock(return_value=FACT)) as lookup:
            result=await research.research_drugs(room,IDS)
        self.assertEqual(result['mode'],'live');self.assertEqual(lookup.await_count,2)
    async def test_case_routing_must_be_uuid(self):
        room=await self.recruit()
        message=self.backend.rooms[room.room_id]['messages'][0]
        payload=json.loads(message['content'].split(research.MARKER)[1])
        payload['case_room_id']='patient-name-or-free-text'
        message['content']=research.MARKER+json.dumps(payload)
        with self.assertRaisesRegex(ValueError,'invalid case routing'):
            await research.read_research(room,IDS)
    async def test_external_failure_is_explicit_not_fabricated(self):
        room=await self.recruit()
        with patch.object(research,'_lookup_fact',new=AsyncMock(side_effect=RuntimeError('private body'))):
            result=await research.research_drugs(room,IDS)
        self.assertEqual(result['status'],'unavailable');self.assertEqual(result['facts'],[])
        await research.relay_research(Room(self.backend,room.room_id,'scribe'),IDS)
        self.assertEqual(research.research_for_review(self.backend.rooms[CASE]['messages'],IDS,self.brief,RECORDING)['status'],'unavailable')
    async def test_bad_urls_and_mock_facts_are_not_live_evidence(self):
        room=await self.recruit()
        with patch.dict(os.environ,{'MOCK_BRAVE':'1'}),patch.object(research,'_lookup_fact',new=AsyncMock(return_value=FACT)):
            await research.research_drugs(room,IDS)
        await research.relay_research(Room(self.backend,room.room_id,'scribe'),IDS)
        checked=research.research_for_review(self.backend.rooms[CASE]['messages'],IDS,self.brief,RECORDING)
        self.assertEqual(checked['facts'],[]);self.assertEqual(checked['status'],'unavailable')
        self.assertIsNone(research._clean_fact(dict(FACT,url='javascript:alert(1)'),'warfarin'))
    async def test_wrapper_mock_is_rejected_even_with_key_and_live_flags(self):
        room=await self.recruit()
        fake=dict(FACT,mock=True,source='mock',url='https://example.invalid/mock-brave')
        with patch.object(research,'_lookup_fact',new=AsyncMock(return_value=fake)):
            result=await research.research_drugs(room,IDS)
        self.assertEqual(result['status'],'unavailable')
        self.assertEqual(result['facts'],[])
        await research.relay_research(Room(self.backend,room.room_id,'scribe'),IDS)
        checked=research.research_for_review(self.backend.rooms[CASE]['messages'],IDS,self.brief,RECORDING)
        self.assertEqual(checked['facts'],[])
        self.assertIsNone(research._clean_fact({key:value for key,value in FACT.items() if key!='mock'},'warfarin'))
    async def test_forged_source_and_extra_transcript_field_are_rejected(self):
        room=await self.recruit()
        request=self.backend.rooms[room.room_id]['messages'][0]
        forged=dict(request,sender_id=IDS['critic'])
        self.assertEqual(research.decode_research([forged],IDS),[])
        data=json.loads(request['content'].split(research.MARKER)[1]);data['transcript']='PRIVATE'
        request['content']=research.MARKER+json.dumps(data)
        with self.assertRaisesRegex(ValueError,'Unexpected research fields'):
            await research.research_drugs(room,IDS)
    async def test_case_roster_and_unbacked_medication_cannot_be_searched(self):
        room=await self.recruit()
        self.backend.rooms[room.room_id]['participants'].append('critic')
        with self.assertRaisesRegex(ValueError,'only Scribe and Researcher'):
            await research.research_drugs(room,IDS)
        changed=copy.deepcopy(BRIEF);changed['meds'][0]['quote']='Not in transcript'
        with self.assertRaisesRegex(ValueError,'not backed'):
            research.drug_names(Brief.model_validate(changed),RECORDING)

if __name__=='__main__':unittest.main()
