"""Approved-room boundary tests: transport and graph mocked explicitly, never live claims."""
import copy
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch,Mock
from hallway.tests.test_spine import FakeBand,IDS,BASIC,RECORDING
from hallway.common.brief import Brief,digest
from hallway.common.room import review,submit_brief,room_records,approved_payload,decode_messages
from hallway.common.runtime import make_tools


class BoundaryBand(FakeBand):
    async def add_participant(self,identifier):
        self.added.append(identifier)
        if not any(p['id']==identifier for p in self.participants):
            self.participants.append({'id':identifier,'handle':'@'+identifier,'type':'User' if identifier=='human-id' else 'Agent'})
        return {'status':'added'}
    async def create_chatroom(self):
        room=BoundaryBand();room.room_id='approved-'+str(len(self.rooms));room.messages=[]
        room.role='critic';room.rest=self;room.rooms=self.rooms
        room.participants=[{'id':IDS['critic'],'handle':'@team/critic','type':'Agent'}]
        self.rooms[room.room_id]=room
        return room.room_id


def bind(room_id,rest,agent_id):
    room=rest.rooms[room_id]
    room.role=next(k for k,v in IDS.items() if v==agent_id)
    return room


class BoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def approved_case(self):
        case=BoundaryBand();case.participants=[p for p in case.participants if p['id'] in {IDS['desk'],IDS['scribe'],IDS['critic'],'human-id'}]
        case.messages[0]['id']='source-transcript-evidence'
        brief=copy.deepcopy(BASIC);brief['follow_ups']=[]
        await submit_brief(case,IDS,Brief.model_validate(brief));case.role='critic'
        result=await review(case,IDS,True,[])
        return case,case.rooms[result['approved_room_id']]
    def enabled(self):return patch.dict(os.environ,{'ENABLE_APPROVED_ROOM':'1'})
    async def test_approve_creates_separate_redacted_room_and_retry_reuses(self):
        with self.enabled(),patch('hallway.common.room.AgentTools',side_effect=bind):
            case,boundary=await self.approved_case()
            self.assertNotIn(IDS['grapher'],case.added)
            self.assertIn(IDS['grapher'],boundary.added)
            content=str(boundary.messages)
            self.assertNotIn(RECORDING['transcript'],content);self.assertNotIn('Taylor Example',content)
            payload=approved_payload(await room_records(boundary,IDS),boundary.room_id)
            self.assertEqual(payload['case_id'],case.room_id)
            self.assertEqual({r['agent'] for r in payload['manifest']},{'desk','scribe','critic'})
            self.assertTrue(all(r['source_message_id'] for r in payload['manifest']))
            case.role='critic';await review(case,IDS,True,[])
            self.assertEqual(len(case.rooms),2)
            self.assertEqual(sum(r['kind']=='APPROVAL' for r in await room_records(boundary,IDS)),1)
    async def test_veto_does_not_create_room(self):
        case=BoundaryBand()
        with self.enabled(),patch('hallway.common.room.AgentTools',side_effect=bind):
            await submit_brief(case,IDS,Brief.model_validate(BASIC));case.role='critic'
            self.assertEqual((await review(case,IDS,True,[]))['verdict'],'VETO')
            self.assertEqual(len(case.rooms),1)
    async def test_wrong_room_digest_and_sender_are_blocked(self):
        with self.enabled(),patch('hallway.common.room.AgentTools',side_effect=bind):case,boundary=await self.approved_case()
        records=await room_records(boundary,IDS)
        with self.assertRaises(ValueError):approved_payload(records,case.room_id)
        broken=copy.deepcopy(records);broken[-1]['digest']='tampered'
        with self.assertRaises(ValueError):approved_payload(broken,boundary.room_id)
        forged=copy.deepcopy(boundary.messages);forged[-1]['sender_id']=IDS['scribe']
        with self.assertRaises(ValueError):approved_payload(decode_messages(forged,IDS),boundary.room_id)
    async def test_graph_reads_authenticated_payload_and_replay_does_not_rewrite(self):
        with self.enabled(),patch('hallway.common.room.AgentTools',side_effect=bind):case,boundary=await self.approved_case()
        holder={'agent':SimpleNamespace(runtime=SimpleNamespace(link=SimpleNamespace(rest=case)))}
        tool=next(t for t in make_tools('grapher',holder,IDS) if t.name=='band_write_approved_graph')
        self.assertEqual(tool.args,{})
        config={'configurable':{'thread_id':boundary.room_id}}
        write=Mock(return_value={'merged':False,'encounter':case.room_id})
        with patch('hallway.common.runtime.AgentTools',side_effect=bind),patch.dict(os.environ,{'MOCK_NEO4J':'1'}),patch('hallway.graph.store.write_approved',write),patch('hallway.graph.store.who_saw_identifiers',return_value=[]):
            first=await tool.ainvoke({},config=config);second=await tool.ainvoke({},config=config)
        self.assertEqual(first['status'],'MOCK_GRAPH_WRITTEN');self.assertEqual(second['status'],first['status'])
        write.assert_called_once()
        self.assertNotIn('recording',write.call_args.args[0]);self.assertEqual(write.call_args.args[3],case.room_id)
    async def test_mock_receipt_does_not_suppress_later_live_write(self):
        with self.enabled(),patch('hallway.common.room.AgentTools',side_effect=bind):case,boundary=await self.approved_case()
        holder={'agent':SimpleNamespace(runtime=SimpleNamespace(link=SimpleNamespace(rest=case)))}
        tool=next(t for t in make_tools('grapher',holder,IDS) if t.name=='band_write_approved_graph')
        config={'configurable':{'thread_id':boundary.room_id}}
        write=Mock(return_value={'merged':True,'encounter':case.room_id})
        with patch('hallway.common.runtime.AgentTools',side_effect=bind),patch('hallway.graph.store.write_approved',write),patch('hallway.graph.store.who_saw_identifiers',return_value=[]):
            with patch.dict(os.environ,{'MOCK_NEO4J':'1'}):await tool.ainvoke({},config=config)
            with patch.dict(os.environ,{'MOCK_NEO4J':'0','NEO4J_URI':'neo4j+s://unit-test.invalid'}):
                result=await tool.ainvoke({},config=config)
        self.assertEqual(write.call_count,2);self.assertEqual(result['status'],'GRAPH_WRITTEN')
    async def test_unexpected_roster_member_blocks_graph(self):
        with self.enabled(),patch('hallway.common.room.AgentTools',side_effect=bind):case,boundary=await self.approved_case()
        boundary.participants.append({'id':'unexpected-agent','handle':'@unexpected','type':'Agent'})
        holder={'agent':SimpleNamespace(runtime=SimpleNamespace(link=SimpleNamespace(rest=case)))}
        tool=next(t for t in make_tools('grapher',holder,IDS) if t.name=='band_write_approved_graph')
        with patch('hallway.common.runtime.AgentTools',side_effect=bind),patch.dict(os.environ,{'MOCK_NEO4J':'1'}):
            with self.assertRaisesRegex(ValueError,'Unexpected participant'):
                await tool.ainvoke({},config={'configurable':{'thread_id':boundary.room_id}})
    async def test_missing_live_graph_config_fails_closed(self):
        with self.enabled(),patch('hallway.common.room.AgentTools',side_effect=bind):case,boundary=await self.approved_case()
        holder={'agent':SimpleNamespace(runtime=SimpleNamespace(link=SimpleNamespace(rest=case)))}
        tool=next(t for t in make_tools('grapher',holder,IDS) if t.name=='band_write_approved_graph')
        with patch('hallway.common.runtime.AgentTools',side_effect=bind),patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'implicit memory fallback'):
                await tool.ainvoke({},config={'configurable':{'thread_id':boundary.room_id}})

if __name__=='__main__':unittest.main()
