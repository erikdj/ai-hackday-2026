"""Explicit unit-test harness. Never called by the live runtime or as a fallback."""
import argparse
import os
import sys
import unittest

from dotenv import load_dotenv


def mode() -> str:
    """Reject mixed transports, including flags loaded from the local .env."""
    load_dotenv()
    flags = (os.getenv('MOCK_CRUSOE', '0'), os.getenv('MOCK_BAND', '0'))
    if flags == ('1', '1'):
        return 'offline'
    if flags == ('0', '0'):
        return 'live'
    raise ValueError('MOCK_CRUSOE and MOCK_BAND must BOTH be 1 for the offline harness or BOTH 0 for live; mixed modes are prohibited')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', action='store_true', help='Print validated mode for Makefile routing only')
    args = parser.parse_args()
    try:
        selected = mode()
    except ValueError as exc:
        parser.exit(2, str(exc) + '\n')
    if args.mode:
        print(selected)
        return 0
    if selected != 'offline':
        parser.exit(2, 'OFFLINE HARNESS requires MOCK_CRUSOE=1 and MOCK_BAND=1\n')
    print('OFFLINE HARNESS — NO REAL BAND OR CRUSOE CALLS', flush=True)
    print('Runs synthetic unit-test examples against actual deterministic validators and FakeBand.', flush=True)
    print('Does not process the live fixture; no graph writes, approved boundary room, or sponsor proof.', flush=True)
    # Test-only imports remain inside this explicit offline branch. No live agent
    # imports this module, and no error in the live demo can select this runner.
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'hallway.tests.test_spine.ValidationTests',
        'hallway.tests.test_spine.ProtocolTests',
        'hallway.tests.test_llm.ModelBoundaryTests',
    ])
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    if not result.wasSuccessful() or result.testsRun == 0:
        print('OFFLINE HARNESS FAILED; live demo remains unverified.', flush=True)
        return 1
    print(f'OFFLINE HARNESS PASS ({result.testsRun} tests). LIVE DEMO NOT VERIFIED.', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
