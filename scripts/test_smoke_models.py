"""Offline checks for live-model smoke safety; these are not live smoke evidence."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as S
import unittest
from unittest.mock import MagicMock, patch

import smoke_models


class SmokeSafetyTests(unittest.TestCase):
    def run_smoke(self, client, candidates):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            stream = io.StringIO()
            with patch.dict(os.environ, {'CRUSOE_API_KEY': 'secret-marker'}, clear=True), \
                 patch.object(smoke_models, 'load_dotenv'), \
                 patch.object(smoke_models, 'OpenAI') as factory, \
                 patch('sys.argv', ['smoke_models.py', *candidates, '--output', str(output)]), \
                 redirect_stdout(stream), redirect_stderr(stream):
                factory.return_value.__enter__.return_value = client
                status = smoke_models.main()
                factory.assert_called_once_with(api_key='secret-marker', base_url='https://api.inference.crusoecloud.com/v1', timeout=10.0, max_retries=2)
            return status, json.loads(output.read_text()), stream.getvalue()

    def test_unknown_catalog_id_never_calls_inference(self):
        client = MagicMock()
        client.models.list.return_value = S(data=[S(id='known')])
        status, report, _ = self.run_smoke(client, ['known', 'invented'])
        self.assertEqual(status, 1)
        self.assertFalse(report['ok'])
        client.chat.completions.create.assert_not_called()

    def test_exception_content_is_not_logged_or_recorded(self):
        client = MagicMock()
        client.models.list.side_effect = RuntimeError('secret-marker response body')
        status, report, logs = self.run_smoke(client, ['a', 'b'])
        self.assertEqual(status, 1)
        self.assertNotIn('secret-marker', logs + json.dumps(report))
        self.assertEqual(report['error'], 'RuntimeError')

    def test_plain_text_response_cannot_pass_tool_smoke(self):
        client = MagicMock()
        client.models.list.return_value = S(data=[S(id='a'), S(id='b')])
        client.chat.completions.create.return_value = S(choices=[S(message=S(tool_calls=[]))])
        status, report, _ = self.run_smoke(client, ['a', 'b'])
        self.assertEqual(status, 1)
        self.assertEqual(len(report['results']), 4)
        self.assertFalse(any(result['ok'] for result in report['results']))

    def test_forced_success_does_not_mask_auto_failure(self):
        client = MagicMock()
        client.models.list.return_value = S(data=[S(id='a'), S(id='b')])
        def complete(**kwargs):
            calls = [] if kwargs['tool_choice'] == 'auto' else [
                S(function=S(name='record_probe', arguments='{"value":"hallway"}'))]
            return S(choices=[S(message=S(tool_calls=calls))])
        client.chat.completions.create.side_effect = complete
        status, report, _ = self.run_smoke(client, ['a', 'b'])
        self.assertEqual(status, 1)
        self.assertEqual([(r['mode'], r['ok']) for r in report['results']],
                         [('forced', True), ('auto', False)] * 2)
        for call in client.chat.completions.create.call_args_list:
            self.assertEqual(call.kwargs['max_tokens'], 128)

    def test_wrong_arguments_fail_even_when_function_name_is_correct(self):
        client = MagicMock()
        client.models.list.return_value = S(data=[S(id='a'), S(id='b')])
        client.chat.completions.create.return_value = S(choices=[S(message=S(tool_calls=[
            S(function=S(name='record_probe', arguments='{"value":"wrong"}'))]))])
        status, report, _ = self.run_smoke(client, ['a', 'b'])
        self.assertEqual(status, 1)
        self.assertFalse(any(r['ok'] for r in report['results']))


if __name__ == '__main__':
    unittest.main()
