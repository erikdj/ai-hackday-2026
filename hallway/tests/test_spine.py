"""Offline synthetic protocol tests, not a live sponsor or clinical validation."""
import copy
import os
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock
from hallway.common.brief import Brief,digest,extract_identifiers,identifier_violations,validate_brief
from hallway.common.room import PREFIX,approved_payload,decode_messages,review,submit_brief,request_owner,raw_messages
from hallway.common.runtime import make_tools, build_agent
from hallway.common.band_cfg import credentials,identities
from hallway.common.llm import InferenceUnavailable
from langchain_openai import ChatOpenAI

IDS={r:r+'-id' for r in ('desk','scribe','critic','researcher','grapher','closer')}
RECORDING={'transcript':'Patient name: Taylor Example\nDOB: 1974-04-03\nMRN: ABC123456\nPhone: 415-555-0123\nAddress: 42 Example Street\nStable overnight. Someone should call the daughter about discharge.','pseudo_id':'pseudonym-123','human_id':'human-id'}
BASIC={'patient':{'pseudo_id':'pseudonym-123'},'findings':[{'text':'Stable overnight','quote':'Stable overnight.'}],
       'follow_ups':[{'id':'call-daughter','text':'Call daughter about discharge','quote':'Someone should call the daughter about discharge.','status':'pending'}]}


def record(kind,payload,author):
    return {'id':str(id(payload)),'sender_id':IDS.get(author,author),'sender_type':'Agent',
            'content':PREFIX+json.dumps({'kind':kind,**payload}),
            'mentions':[{'id':IDS[r]} for r in {'TRANSCRIPT':['scribe','critic'],'BRIEF':['critic'], 'OWNER_REQUEST':['critic'],'APPROVAL':['scribe']}.get(kind,[])]}


class FakeBand:
    def __init__(self):
        self.room_id='case-1';self.role='scribe';self.added=[];self.filter_mentions=False
        self.rest=self;self.rooms={self.room_id:self}
        self.messages=[record('TRANSCRIPT',{'recording':RECORDING},'desk')]
        self.participants=[{'id':v,'handle':'@team/'+k,'type':'Agent'} for k,v in IDS.items()]
        self.participants.append({'id':'human-id','handle':'@human','type':'User','name':'Charge Nurse'})
    async def fetch_room_context(self,**kwargs):
        assert kwargs['room_id']==self.room_id
        messages=self.messages
        if self.filter_mentions:
            identity=IDS[self.role]
            messages=[m for m in messages if m.get('sender_id')==identity or identity in [x['id'] for x in m.get('mentions',[])]]
        return {'data':messages,'meta':{'total_pages':1}}
    async def get_participants(self): return self.participants
    async def lookup_peers(self): raise AssertionError('No phase1 research recruitment')
    async def add_participant(self,identifier): self.added.append(identifier);return {'status':'added'}
    async def create_chatroom(self):
        room_id='case-'+str(len(self.rooms)+1);room=FakeBand();room.messages=[];room.room_id=room_id
        room.role=self.role;room.rest=self;room.rooms=self.rooms;self.rooms[room_id]=room
        return room_id
    async def send_event(self,content,message_type):
        if message_type=='task': self.messages.append({'id':str(len(self.messages)),'sender_id':IDS[self.role],'content':content})
        return {}
    async def send_message(self,content,mentions):
        self.messages.append({'id':str(len(self.messages)),'sender_id':IDS[self.role],'sender_type':'Agent','content':content,'mentions':mentions})
        return {}
    def human(self,content,name='Charge Nurse',sender='human-id',sender_type='User'):
        message={'id':'reply-'+str(len(self.messages)),'sender_id':sender,'sender_type':sender_type,
                 'sender_name':name,'content':content,'mentions':[{'id':IDS['scribe']},{'id':IDS['critic']}]}
        self.messages.append(message);return message


class ValidationTests(unittest.TestCase):
    def test_identifier_gate_scans_all_fields(self):
        for value in ('Taylor Example','Taylor','1974-04-03','ABC123456','415-555-0123','42 Example Street'):
            self.assertTrue(identifier_violations({'nested':{'quote':value}},RECORDING))
        self.assertEqual([],identifier_violations({'quote':'Stable overnight.'},RECORDING))
    def test_spoken_fixture_name_and_dob(self):
        source={'transcript':'This is Robert Callahan, date of birth March fourth, nineteen fifty-two. Stable overnight.'}
        for value in ('Robert Callahan','Robert','Callahan','March fourth, nineteen fifty-two'):
            self.assertTrue(identifier_violations({'quote':value},source),value)
    def test_actual_fixture_identity_forms_are_stable(self):
        first='Okay, handing off ED bay four. Robert Callahan, date of birth March fourth, nineteen fifty-two.'
        second='Okay, bed twelve. This is Robert Callahan, date of birth March fourth, nineteen fifty-two. Seventy-four year old male.'
        self.assertEqual(extract_identifiers(first),extract_identifiers(second))
        self.assertIn('Robert Callahan',extract_identifiers(first))
    def test_spoken_stress_identifiers(self):
        source={'transcript':'Dolores Whitfield, medical record number four four seven one nine two three. Phone number is five five five, zero one nine, two two four seven.'}
        for value in ('Dolores Whitfield','four four seven one nine two three','five five five zero one nine two two four seven'):
            self.assertTrue(identifier_violations({'quote':value},source),value)
    def test_real_full_stress_fixture_phone_and_mrn(self):
        transcript=(Path(__file__).parents[1]/'fixtures'/'handoff_3.txt').read_text()
        identifiers=extract_identifiers(transcript)
        phone='five five five, zero one nine, two two four seven'
        self.assertIn(phone,identifiers)
        self.assertIn('5550192247',identifiers)
        self.assertIn('4471923',identifiers)
        self.assertNotIn('four',identifiers)
        for value in (phone,'five five five zero one nine two two four seven','5550192247','4471923'):
            self.assertTrue(identifier_violations({'nested':{'quote':value}},{'transcript':transcript}),value)
        # A clinical mention of a digit word must not pass only because the MRN
        # parser mistakenly extracted the single word "four".
        self.assertEqual([],identifier_violations({'quote':'four'},{'transcript':transcript}))
    def test_compact_phone(self):
        self.assertTrue(identifier_violations({'phone':'4155550123'},RECORDING))
    def test_quote_with_identifier_is_vetoed_even_when_verbatim(self):
        brief=copy.deepcopy(BASIC);brief['findings'][0]={'text':'Patient detail','quote':'Taylor Example'}
        self.assertTrue(any('identifier' in x for x in validate_brief(Brief.model_validate(brief),RECORDING,[])))
    def test_pseudonym_cannot_be_changed(self):
        b=copy.deepcopy(BASIC);b['patient']['pseudo_id']='invented'
        self.assertTrue(any('pseudo_id' in x for x in validate_brief(Brief.model_validate(b),RECORDING,[])))
    def test_quotes_and_urls(self):
        b=copy.deepcopy(BASIC);b['findings'][0]['quote']='Never spoken'
        reasons=validate_brief(Brief.model_validate(b),RECORDING,[{'url':'javascript:bad'}])
        self.assertTrue(any('quote not found' in x for x in reasons));self.assertTrue(any('URL' in x for x in reasons))
    def test_spoofed_transcript_ignored(self):
        self.assertEqual([],decode_messages([record('TRANSCRIPT',{'recording':RECORDING},'scribe')],IDS))
    def test_no_raw_platform_tools_or_model_room_argument(self):
        for role in IDS:
            for tool in make_tools(role,{},IDS):
                self.assertNotIn('config',tool.args);self.assertNotIn('room_id',tool.args)
                self.assertNotIn(tool.name,('band_add_participant','band_create_chatroom','band_send_message'))
    def test_unconfigured_author_is_ignored(self):
        core={role:IDS[role] for role in ('desk','scribe','critic')}
        self.assertEqual([],decode_messages([record('ENRICHMENT',{'facts':[]},'researcher')],core))
    def test_case_approval_not_downstream_authorization(self):
        with self.assertRaisesRegex(ValueError,'boundary'): approved_payload([])


class CredentialTests(unittest.TestCase):
    def env(self):
        return {f'BAND_{role.upper()}_AGENT_ID':f'00000000-0000-0000-0000-{i:012d}' for i,role in enumerate(('desk','scribe','critic'),1)}
    def test_own_key_only_and_peer_ids(self):
        env=self.env();env['BAND_SCRIBE_API_KEY']='own-key'
        with patch.dict(os.environ,env,clear=True),patch('hallway.common.band_cfg.load_agent_config') as yaml:
            self.assertEqual(set(identities()),{'desk','scribe','critic'})
            self.assertEqual(credentials('scribe')[1],'own-key')
            yaml.assert_not_called()
    def test_partial_pair_no_yaml_fallback(self):
        for env in ({'BAND_SCRIBE_AGENT_ID':self.env()['BAND_SCRIBE_AGENT_ID']},{'BAND_SCRIBE_API_KEY':'key'},{'BAND_SCRIBE_AGENT_ID':' ','BAND_SCRIBE_API_KEY':' '}):
            with patch.dict(os.environ,env,clear=True),patch('hallway.common.band_cfg.load_agent_config') as yaml:
                with self.assertRaises(ValueError):credentials('scribe')
                yaml.assert_not_called()
    def test_yaml_only_if_env_pair_absent(self):
        with patch.dict(os.environ,{},clear=True),patch('hallway.common.band_cfg.load_agent_config',return_value=(self.env()['BAND_SCRIBE_AGENT_ID'],'yaml-key')) as yaml:
            self.assertEqual(credentials('scribe')[1],'yaml-key');yaml.assert_called_once()
    def test_optional_peer_blank_allowed_malformed_rejected(self):
        env=self.env();env['BAND_RESEARCHER_AGENT_ID']=''
        with patch.dict(os.environ,env,clear=True):self.assertNotIn('researcher',identities())
        env['BAND_RESEARCHER_AGENT_ID']='not-a-uuid'
        with patch.dict(os.environ,env,clear=True):
            with self.assertRaises(ValueError):identities()
    def test_duplicate_and_bad_own_uuid_rejected(self):
        env=self.env();env['BAND_CRITIC_AGENT_ID']=env['BAND_SCRIBE_AGENT_ID']
        with patch.dict(os.environ,env,clear=True):
            with self.assertRaises(ValueError):identities()
        with patch.dict(os.environ,{'BAND_SCRIBE_AGENT_ID':'bad','BAND_SCRIBE_API_KEY':'key'},clear=True):
            with self.assertRaises(ValueError):credentials('scribe')


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def initial_veto(self,band,brief=None):
        band.role='scribe';await submit_brief(band,IDS,Brief.model_validate(brief or BASIC));band.role='critic'
        verdict=await review(band,IDS,True,[])
        self.assertEqual(verdict['verdict'],'VETO')
        band.role='scribe';return verdict
    async def repaired(self,band,owner=None,reply=None):
        request=await request_owner(band,IDS,'call-daughter')
        brief=copy.deepcopy(BASIC);item=brief['follow_ups'][0]
        item['request_message_id']=request['message_id']
        item['status']='pending' if owner else 'unresolved';item['owner']=owner
        item['owner_message_id']=reply['id'] if reply else None
        return brief,request
    async def test_unresolved_after_explicit_request_approved_without_recruitment(self):
        band=FakeBand();band.filter_mentions=True;await self.initial_veto(band)
        brief,_=await self.repaired(band);await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        result=await review(band,IDS,True,[])
        self.assertEqual(result['status'],'APPROVED');self.assertEqual(result['unresolved_follow_ups'],['call-daughter'])
        self.assertEqual([],band.added)
        approval=[r for r in decode_messages(band.messages,IDS) if r['kind']=='APPROVAL'][-1]
        self.assertNotIn('recording',approval);self.assertEqual(approval['scope'],'case_only_phase1')
        self.assertEqual([],identifier_violations(approval,RECORDING))
    async def test_unresolved_cannot_skip_human_request(self):
        band=FakeBand();b=copy.deepcopy(BASIC);b['follow_ups'][0]['status']='unresolved'
        verdict=await self.initial_veto(band,b)
        self.assertTrue(any('request required' in r for r in verdict['reasons']))
    async def test_real_human_ill_own_it_uses_sender_name(self):
        band=FakeBand();band.filter_mentions=True;await self.initial_veto(band);brief,request=await self.repaired(band)
        reply=band.human("I'll own it",name='Erik Jones')
        brief['follow_ups'][0].update(status='pending',owner='Erik Jones',owner_message_id=reply['id'])
        await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['status'],'APPROVED')
    async def test_reply_not_visible_to_critic_is_not_provenance(self):
        band=FakeBand();band.filter_mentions=True;await self.initial_veto(band);brief,_=await self.repaired(band)
        reply=band.human("I'll own it",name='Erik Jones')
        reply['mentions']=[{'id':IDS['scribe']}]
        brief['follow_ups'][0].update(status='pending',owner='Erik Jones',owner_message_id=reply['id'])
        await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['verdict'],'VETO')
    async def test_verified_reply_handle_prefixes_only(self):
        for prefix,expected in [('@team/scribe @team/critic ','APPROVED'),('@team/critic\t@team/scribe\n','APPROVED'),('@impostor @team/scribe ','VETO'),('@team/scribe-extra ','VETO')]:
            band=FakeBand();band.filter_mentions=True;await self.initial_veto(band);brief,_=await self.repaired(band)
            reply=band.human(prefix+"I'll own it",name='Erik Jones')
            brief['follow_ups'][0].update(status='pending',owner='Erik Jones',owner_message_id=reply['id'])
            await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
            result=await review(band,IDS,True,[])
            self.assertEqual(result.get('status',result.get('verdict')),expected,prefix)
    async def test_forged_agent_ownership_rejected(self):
        band=FakeBand();await self.initial_veto(band);brief,_=await self.repaired(band)
        reply=band.human("I'll own it",name='Erik Jones',sender=IDS['scribe'],sender_type='Agent')
        brief['follow_ups'][0].update(status='pending',owner='Erik Jones',owner_message_id=reply['id'])
        await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['verdict'],'VETO')
    async def test_named_human_assignment(self):
        band=FakeBand();await self.initial_veto(band);brief,_=await self.repaired(band)
        reply=band.human('/own call-daughter Maria Lopez')
        brief['follow_ups'][0].update(status='pending',owner='Maria Lopez',owner_message_id=reply['id'])
        await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['status'],'APPROVED')
    async def test_owner_must_match_actual_human(self):
        band=FakeBand();await self.initial_veto(band);brief,_=await self.repaired(band)
        reply=band.human("I'll own it",name='Erik Jones')
        brief['follow_ups'][0].update(status='pending',owner='Invented Nurse',owner_message_id=reply['id'])
        await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['verdict'],'VETO')
    async def test_hallucinated_followup_removable_but_backed_preserved(self):
        band=FakeBand();bad=copy.deepcopy(BASIC)
        bad['follow_ups'].append({'id':'invented','text':'Invented procedure','quote':'Never spoken'})
        await self.initial_veto(band,bad)
        revised=await submit_brief(band,IDS,Brief.model_validate(BASIC))
        self.assertEqual(revised['removed_unsupported_follow_ups'],['invented'])
        band=FakeBand();await self.initial_veto(band)
        dropped=copy.deepcopy(BASIC);dropped['follow_ups']=[]
        with self.assertRaisesRegex(ValueError,'preserve'):await submit_brief(band,IDS,Brief.model_validate(dropped))
    async def test_followup_id_cannot_hide_replaced_quote(self):
        band=FakeBand();await self.initial_veto(band)
        changed=copy.deepcopy(BASIC);changed['follow_ups'][0]['quote']='Stable overnight.'
        with self.assertRaisesRegex(ValueError,'original source-backed'):
            await submit_brief(band,IDS,Brief.model_validate(changed))
    async def test_two_repairs_escalate(self):
        band=FakeBand()
        for _ in range(3): verdict=await self.initial_veto(band)
        self.assertTrue(verdict['escalate'])
        self.assertIn('human-id',[m['id'] for m in band.messages[-1]['mentions']])
        with self.assertRaisesRegex(ValueError,'exhausted'):await submit_brief(band,IDS,Brief.model_validate(BASIC))
    async def test_semantic_veto_not_overridden(self):
        band=FakeBand();b=copy.deepcopy(BASIC);b['follow_ups']=[]
        await submit_brief(band,IDS,Brief.model_validate(b));band.role='critic'
        self.assertEqual((await review(band,IDS,False,['Unsupported meaning']))['verdict'],'VETO')
    async def test_identifier_veto_then_repair(self):
        band=FakeBand();bad=copy.deepcopy(BASIC);bad['follow_ups']=[]
        bad['findings'].append({'text':'Identifying name','quote':'Taylor Example'})
        verdict=await self.initial_veto(band,bad)
        self.assertTrue(any('identifier' in x for x in verdict['reasons']))
        fixed=copy.deepcopy(BASIC);fixed['follow_ups']=[]
        await submit_brief(band,IDS,Brief.model_validate(fixed));band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['status'],'APPROVED')
    async def test_transcript_named_and_role_owners_accepted(self):
        for owner,quote in [('Maria','Maria should check the result.'),('night nurse','The night nurse will check the result.'),('receiving nurse',"Check the result, that's yours.")]:
            band=FakeBand();source=dict(RECORDING,transcript=RECORDING['transcript']+' '+quote)
            band.messages=[record('TRANSCRIPT',{'recording':source},'desk')]
            brief=copy.deepcopy(BASIC);brief['follow_ups']=[{'id':'result','text':'Check result','quote':quote,'owner':owner}]
            await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
            self.assertEqual((await review(band,IDS,True,[]))['status'],'APPROVED')
    async def test_quote_retention_tolerates_renumbering(self):
        band=FakeBand();await self.initial_veto(band);revised=copy.deepcopy(BASIC)
        revised['follow_ups'][0]['id']='renumbered'
        self.assertEqual((await submit_brief(band,IDS,Brief.model_validate(revised)))['revision'],2)
    async def test_provider_failure_emits_safe_pause_event(self):
        fake_tools=SimpleNamespace(send_event=AsyncMock())
        with patch('hallway.common.runtime.identities',return_value=IDS),patch('hallway.common.runtime.credentials',return_value=(IDS['critic'],'test')),patch('hallway.common.runtime.llm',return_value=ChatOpenAI(api_key='test',model='test')),patch('band.adapters.langgraph.LangGraphAdapter.on_message',new=AsyncMock(side_effect=InferenceUnavailable('inference unavailable, case paused'))):
            agent=build_agent('critic','test')
            with self.assertRaises(InferenceUnavailable):
                await agent._adapter.on_message(None,fake_tools,[],None,None,is_session_bootstrap=True,room_id='test-room')
        fake_tools.send_event.assert_awaited_once_with(content='inference unavailable, case paused',message_type='error')
    async def test_wire_protocol_prefix_is_normalized_only_for_current_roster(self):
        band=FakeBand()
        for kind,author in [('TRANSCRIPT','desk'),('BRIEF','scribe'),('OWNER_REQUEST','scribe'),('VERDICT','critic')]:
            message=record(kind,{},author)
            message['content']='@[['+IDS['critic']+']] @[['+IDS['scribe']+']] '+message['content']
            band.messages=[message]
            self.assertEqual(decode_messages(await raw_messages(band),IDS)[0]['kind'],kind)
            message['content']='@[[unknown-uuid]] '+message['content']
            self.assertEqual([],decode_messages(await raw_messages(band),IDS))
        # A configured peer not in this room is not a verified leading mention.
        band.participants=[p for p in band.participants if p['id']!=IDS['researcher']]
        band.messages=[record('BRIEF',{},'scribe')]
        band.messages[0]['content']='@[['+IDS['researcher']+']] '+band.messages[0]['content']
        self.assertEqual([],decode_messages(await raw_messages(band),IDS))
    async def test_raw_wire_normalization_preserves_sender_metadata(self):
        band=FakeBand();band.messages=[]
        original=band.human('@[['+IDS['scribe']+']] @[['+IDS['critic']+']] '+"I'll own it")
        before=copy.deepcopy(original)
        cleaned=await raw_messages(band)
        self.assertEqual(cleaned[0]['content'],"I'll own it")
        for key in ('id','sender_id','sender_type','sender_name','mentions'):
            self.assertEqual(cleaned[0][key],before[key])
        self.assertEqual(original,before)
        band.messages=[dict(original,content='@[[unknown-uuid]] '+original['content'])]
        self.assertTrue((await raw_messages(band))[0]['content'].startswith('@[[unknown-uuid]]'))
    async def test_wire_prefix_protocol_and_owner_reply_end_to_end(self):
        band=FakeBand();await self.initial_veto(band);brief,_=await self.repaired(band)
        reply=band.human('@[['+IDS['scribe']+']] @[['+IDS['critic']+']] '+"I'll own it",name='Erik Jones')
        brief['follow_ups'][0].update(status='pending',owner='Erik Jones',owner_message_id=reply['id'])
        for message in band.messages:
            if message['content'].startswith(PREFIX):
                message['content']='@[['+IDS['critic']+']] '+message['content']
        await submit_brief(band,IDS,Brief.model_validate(brief));band.role='critic'
        self.assertEqual((await review(band,IDS,True,[]))['status'],'APPROVED')
    async def test_authenticated_intake_and_repeated_fixture(self):
        lobby=FakeBand();lobby.messages=[];lobby.role='desk';lobby.room_id='lobby';lobby.rooms={'lobby':lobby}
        holder={'agent':SimpleNamespace(runtime=SimpleNamespace(link=SimpleNamespace(rest=lobby)))}
        ingest=next(t for t in make_tools('desk',holder,IDS) if t.name=='band_ingest_fixture')
        config={'configurable':{'thread_id':'lobby'}}
        with patch('hallway.common.runtime.AgentTools',side_effect=lambda room_id,rest,agent_id:rest.rooms[room_id]),patch('hallway.ingest.fixture.load_recording',return_value=copy.deepcopy(RECORDING)):
            lobby.human('/ingest fixture:handoff_2',sender=IDS['scribe'],sender_type='Agent')
            with self.assertRaisesRegex(ValueError,'authenticated human'): await ingest.ainvoke({'fixture':'handoff_2'},config=config)
            lobby.human('@[[unknown-uuid]] /ingest fixture:handoff_2')
            with self.assertRaisesRegex(ValueError,'authenticated human'): await ingest.ainvoke({'fixture':'handoff_2'},config=config)
            lobby.human('@[['+IDS['desk']+']] /ingest fixture:handoff_2')
            first=await ingest.ainvoke({'fixture':'handoff_2'},config=config)
            duplicate=await ingest.ainvoke({'fixture':'handoff_2'},config=config)
            self.assertEqual(first['room_id'],duplicate['room_id'])
            lobby.human('/ingest fixture:handoff_2')
            second=await ingest.ainvoke({'fixture':'handoff_2'},config=config)
            self.assertNotEqual(first['room_id'],second['room_id'])
            with self.assertRaisesRegex(ValueError,'differs'): await ingest.ainvoke({'fixture':'handoff_1'},config=config)

if __name__=='__main__':unittest.main()
