"""Live Band fixture trigger. Never substitutes local execution for Band coordination."""
import argparse
import asyncio
import os
import time
import uuid
from band.client.rest import AsyncRestClient, DEFAULT_REQUEST_OPTIONS, aclose_rest_client
from band.runtime.tools.agent import AgentTools
from band_rest import ChatMessageRequest, ChatMessageRequestMentionsItem
from hallway.common.band_cfg import configure_timeouts, credentials, identities
from hallway.common.room import room_records
from hallway.ingest.fixture import fixture_path
from hallway.common.llm import llm


async def demo(args):
    fixture_path(args.fixture)
    for role in ("desk", "scribe", "critic"):
        llm(role)  # Validate live Crusoe configuration before opening any Band connection.
    print("SYNTHETIC PATIENT — live Band/Crusoe demo; no clinical data", flush=True)
    configure_timeouts()
    ids = identities()
    room = args.room or os.getenv('BAND_LOBBY_ROOM_ID')
    if not room:
        raise ValueError('Set BAND_LOBBY_ROOM_ID to an existing lobby with Desk')
    clients = []
    try:
        observer = AsyncRestClient(api_key=credentials('desk')[1], timeout=10)
        clients.append(observer)
        lobby = AgentTools(room, observer, agent_id=ids['desk'])
        before = {r['message_id'] for r in await room_records(lobby, ids)}
        request_id=uuid.uuid4().hex
        if args.watch_only:
            print(f'Waiting: in the Band lobby mention Desk with /ingest fixture:{args.fixture} run:{request_id}', flush=True)
        else:
            key = os.getenv('BAND_HUMAN_API_KEY')
            if not key:
                raise ValueError('BAND_HUMAN_API_KEY required to message Desk; alternatively use --watch-only and send in Band')
            human = AsyncRestClient(api_key=key, timeout=10)
            clients.append(human)
            roster = await human.human_api_participants.list_my_chat_participants(chat_id=room,request_options=DEFAULT_REQUEST_OPTIONS)
            desk = next((p for p in roster.data if p.id==ids['desk']), None)
            if not desk or not desk.handle:
                raise ValueError('Desk is not a participant with a valid handle in this lobby')
            await human.human_api_messages.send_my_chat_message(chat_id=room,
                message=ChatMessageRequest(content=f'/ingest fixture:{args.fixture} run:{request_id}',
                  mentions=[ChatMessageRequestMentionsItem(id=desk.id, handle=desk.handle)]),
                request_options=DEFAULT_REQUEST_OPTIONS)
        deadline = time.monotonic()+90
        case_id = None
        while time.monotonic()<deadline:
            records = await room_records(lobby, ids)
            matches = [r for r in records if r['kind']=='CASE_CREATED' and r.get('request_id')==request_id and r['message_id'] not in before]
            if matches:
                case_id = matches[-1]['room_id']
                break
            await asyncio.sleep(1)
        if not case_id:
            raise RuntimeError('No new Band case within 90 seconds; check Desk process and room events')
        print(f'Band case ID: {case_id}', flush=True)
        template = os.getenv('BAND_ROOM_URL_TEMPLATE')
        if template:
            print('Band room URL: '+template.format(room_id=case_id), flush=True)
        else:
            print('Open this case in https://app.band.ai/ (direct room URL format not verified)', flush=True)
        critic_client = AsyncRestClient(api_key=credentials('critic')[1], timeout=10)
        clients.append(critic_client)
        case = AgentTools(case_id, critic_client, agent_id=ids['critic'])
        while time.monotonic()<deadline:
            records = await room_records(case, ids)
            approvals = [r for r in records if r['kind']=='APPROVAL']
            if approvals:
                print('Spine APPROVED. Veto count:',sum(r['kind']=='VERDICT' and r['verdict']=='VETO' for r in records))
                raise RuntimeError('Full demo incomplete: lineage query and approved boundary room evidence are not implemented in this slice')
            await asyncio.sleep(1)
        raise RuntimeError('Case did not approve within 90-second demo budget')
    finally:
        for client in clients:
            await aclose_rest_client(client)


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixture', default='handoff_2', help='Safe name of an existing hallway/fixtures/<name>.txt')
    parser.add_argument('--room')
    parser.add_argument('--watch-only',action='store_true')
    args=parser.parse_args()
    try:
        asyncio.run(demo(args))
    except Exception as exc:
        parser.exit(1, f'DEMO NOT GREEN: {exc}\n')


if __name__=='__main__':
    main()
