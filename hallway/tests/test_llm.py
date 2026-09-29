"""Offline provider-boundary and real installed Band-adapter compatibility tests."""
import os
import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from band.adapters.langgraph import LangGraphAdapter
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from hallway.common.llm import InferenceUnavailable, llm
from hallway.ingest import fixture

ENV = {'CRUSOE_API_KEY': 'test-only', 'CRUSOE_MODEL_STRONG': 'primary',
       'CRUSOE_MODEL_FAST': 'fast', 'CRUSOE_MODEL_CRITIC': 'critic',
       'CRUSOE_MODEL_FALLBACK': 'secondary', 'CRUSOE_FAMILY_STRONG': 'family-a',
       'CRUSOE_FAMILY_CRITIC': 'family-b'}


def answer():
    return ChatResult(generations=[ChatGeneration(message=AIMessage(content='test response'))])


class ModelBoundaryTests(IsolatedAsyncioTestCase):
    async def test_band_adapter_binds_tools_and_falls_back_on_crusoe(self):
        calls = []
        @tool
        def inspect_case() -> str:
            """Read an offline synthetic case marker."""
            return 'marker'
        async def generate(client, messages, **kwargs):
            calls.append((client.model_name, kwargs, str(client.openai_api_base)))
            if client.model_name == 'primary':
                raise RuntimeError('provider response must stay private')
            return answer()
        with patch.dict(os.environ, ENV, clear=True), patch.object(ChatOpenAI, '_agenerate', autospec=True, side_effect=generate):
            adapter = LangGraphAdapter(llm=llm('scribe'), additional_tools=[inspect_case])
            graph = adapter.graph_factory([])
            events = [event async for event in graph.astream_events(
                {'messages': [HumanMessage(content='synthetic')]},
                config={'configurable': {'thread_id': 'offline-compatibility'}}, version='v2')]
            result = events[-1]['data']['output']
        self.assertEqual(result['messages'][-1].content, 'test response')
        self.assertEqual([call[0] for call in calls], ['primary', 'secondary'])
        for _, kwargs, endpoint in calls:
            self.assertEqual(kwargs['tools'][0]['function']['name'], 'inspect_case')
            self.assertEqual(endpoint, 'https://api.inference.crusoecloud.com/v1')

    async def test_both_fail_raises_safe_pause_without_external_provider(self):
        async def generate(client, messages, **kwargs):
            raise RuntimeError('private synthetic identifier + API error body')
        with patch.dict(os.environ, ENV, clear=True), patch.object(ChatOpenAI, '_agenerate', autospec=True, side_effect=generate) as request:
            with self.assertRaisesRegex(InferenceUnavailable, '^inference unavailable, case paused$'):
                await llm('critic').ainvoke('synthetic')
        self.assertEqual(request.call_count, 2)

    async def test_truncated_primary_falls_back_to_valid_completion(self):
        calls=[]
        async def generate(client,messages,**kwargs):
            calls.append(client.model_name)
            if client.model_name=='primary':
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=''),generation_info={'finish_reason':'length'})])
            return answer()
        with patch.dict(os.environ,ENV,clear=True),patch.object(ChatOpenAI,'_agenerate',autospec=True,side_effect=generate):
            self.assertEqual((await llm('scribe').ainvoke('synthetic')).content,'test response')
        self.assertEqual(calls,['primary','secondary'])

    async def test_both_truncated_fail_closed(self):
        async def generate(client,messages,**kwargs):
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=''),generation_info={'finish_reason':'length'})])
        with patch.dict(os.environ,ENV,clear=True),patch.object(ChatOpenAI,'_agenerate',autospec=True,side_effect=generate) as request:
            with self.assertRaises(InferenceUnavailable):await llm('scribe').ainvoke('synthetic')
        self.assertEqual(request.call_count,2)

    def test_invalid_tool_call_sync_falls_back(self):
        calls=[]
        def generate(client,messages,**kwargs):
            calls.append(client.model_name)
            if client.model_name=='primary':
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content='',invalid_tool_calls=[{'name':'publish','args':'{','id':'bad','error':'invalid JSON','type':'invalid_tool_call'}]),generation_info={'finish_reason':'tool_calls'})])
            return answer()
        with patch.dict(os.environ,ENV,clear=True),patch.object(ChatOpenAI,'_generate',autospec=True,side_effect=generate):
            self.assertEqual(llm('scribe').invoke('synthetic').content,'test response')
        self.assertEqual(calls,['primary','secondary'])

    def test_valid_empty_stop_is_not_rejected(self):
        result=ChatResult(generations=[ChatGeneration(message=AIMessage(content=''),generation_info={'finish_reason':'stop'})])
        with patch.dict(os.environ,ENV,clear=True),patch.object(ChatOpenAI,'_generate',return_value=result) as request:
            self.assertEqual(llm('critic').invoke('synthetic').content,'')
        self.assertEqual(request.call_count,1)

    def test_sync_fallback(self):
        def generate(client, messages, **kwargs):
            if client.model_name == 'primary':
                raise RuntimeError('unavailable')
            return answer()
        with patch.dict(os.environ, ENV, clear=True), patch.object(ChatOpenAI, '_generate', autospec=True, side_effect=generate):
            self.assertEqual(llm('scribe').invoke('synthetic').content, 'test response')

    def test_reject_external_endpoint_for_every_role(self):
        from hallway.common.llm import ROLES
        with patch.dict(os.environ, {**ENV, 'CRUSOE_BASE_URL': 'https://external.example/v1'}, clear=True):
            for role in ROLES:
                with self.subTest(role=role), self.assertRaisesRegex(ValueError, 'Only the Crusoe'):
                    llm(role)

    def test_role_output_budgets_apply_to_both_crusoe_clients(self):
        with patch.dict(os.environ, ENV, clear=True):
            for role,expected in {'scribe':4096,'researcher':2048,'closer':2048,'desk':1024,'critic':1024,'grapher':1024}.items():
                model=llm(role)
                for client in (model,model.crusoe_fallback):
                    self.assertEqual(client.max_tokens,expected)
                    self.assertEqual(client.request_timeout,30)
                    self.assertEqual(client.max_retries,1)
                    self.assertEqual(str(client.openai_api_base),'https://api.inference.crusoecloud.com/v1')

    def test_low_reasoning_only_for_exact_verified_glm_in_either_position(self):
        for primary,secondary in [('zai-org/GLM-5.3','secondary'),('primary','zai-org/GLM-5.3'),('primary','secondary')]:
            env={**ENV,'CRUSOE_MODEL_STRONG':primary,'CRUSOE_MODEL_FALLBACK':secondary}
            with patch.dict(os.environ,env,clear=True):
                model=llm('scribe')
                self.assertEqual(model.reasoning_effort,'low' if primary=='zai-org/GLM-5.3' else None)
                self.assertEqual(model.crusoe_fallback.reasoning_effort,'low' if secondary=='zai-org/GLM-5.3' else None)

    def test_disable_thinking_applies_independently_to_listed_models(self):
        expected = {'chat_template_kwargs': {'enable_thinking': False}}
        for listed, primary_enabled, fallback_enabled in [
            ('primary', True, False), ('secondary', False, True),
            (' primary , secondary ,, ', True, True),
        ]:
            with self.subTest(listed=listed), patch.dict(os.environ, {
                **ENV, 'CRUSOE_DISABLE_THINKING_MODELS': listed,
            }, clear=True):
                model = llm('scribe')
                self.assertEqual(model.extra_body, expected if primary_enabled else None)
                self.assertEqual(model.crusoe_fallback.extra_body, expected if fallback_enabled else None)
                for client in (model, model.crusoe_fallback):
                    self.assertEqual(client.request_timeout, 30)
                    self.assertEqual(client.max_retries, 1)
                    self.assertEqual(client.max_tokens, 4096)

    def test_disable_thinking_requires_exact_case_sensitive_model_match(self):
        for listed in (None, '', ' , ', 'Primary,secondary-extra,other/primary'):
            env = dict(ENV)
            if listed is not None:
                env['CRUSOE_DISABLE_THINKING_MODELS'] = listed
            with self.subTest(listed=listed), patch.dict(os.environ, env, clear=True):
                model = llm('scribe')
                for client in (model, model.crusoe_fallback):
                    self.assertIsNone(client.extra_body)

    def test_distinct_secondary_is_required(self):
        with patch.dict(os.environ, {**ENV, 'CRUSOE_MODEL_FALLBACK': 'primary'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'distinct Crusoe fallback'):
                llm('scribe')


class FixtureBoundaryTests(TestCase):
    def test_reject_traversal_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'fixtures'
            root.mkdir()
            outside = Path(directory) / 'outside.txt'
            outside.write_text('unit test input')
            (root / 'escape.txt').symlink_to(outside)
            with patch.object(fixture, 'FIXTURES', root):
                for name in ('../outside', '/tmp/outside', 'escape', 'name.json'):
                    with self.subTest(name=name), self.assertRaises(ValueError):
                        fixture.fixture_path(name)

    def test_stable_private_pseudonym_and_no_identifier_map(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'unit.txt').write_text('Unit-only input; not a demonstration transcript.')
            salt = root / 'private' / 'salt'
            with patch.object(fixture, 'FIXTURES', root), patch.dict(os.environ, {'HANDOFF_PSEUDONYM_SALT_FILE': str(salt)}), \
                 patch('hallway.common.brief.extract_identifiers', return_value=['UNIT-IDENTIFIER'], create=True):
                first = fixture.load_recording('unit')
                second = fixture.load_recording('unit.txt')
                self.assertEqual(first['pseudo_id'], second['pseudo_id'])
                self.assertEqual(set(first), {'transcript', 'pseudo_id', 'source', 'at'})
                self.assertNotIn('UNIT-IDENTIFIER', first['pseudo_id'])
                self.assertEqual(salt.stat().st_mode & 0o777, 0o600)
                salt.write_bytes(b'x' * 32)
                self.assertNotEqual(first['pseudo_id'], fixture.load_recording('unit')['pseudo_id'])

    def test_no_recognized_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'unit.txt').write_text('Unit-only input')
            with patch.object(fixture, 'FIXTURES', root), patch('hallway.common.brief.extract_identifiers', return_value=[], create=True):
                with self.assertRaisesRegex(ValueError, 'without recognized direct identifiers'):
                    fixture.load_recording('unit')
