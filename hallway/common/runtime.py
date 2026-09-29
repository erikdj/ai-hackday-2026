"""Construct the documented Band adapter with room-bound, least-privilege tools."""
import asyncio
import json
import logging
import os
import re
from pathlib import Path
from band import Agent
from band.adapters.langgraph import LangGraphAdapter
from band.core.types import Emit
from band.runtime.tools.agent import AgentTools
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from hallway.common.band_cfg import configure_timeouts, credentials, identities
from hallway.common.brief import Brief, digest
from hallway.common.llm import llm
from hallway.common.room import (action_event, approved_payload, case_state, post,
                                recruit, review, room_records, raw_messages, submit_brief)


def make_tools(role: str, holder: dict, ids: dict[str,str]) -> list:
    locks = {}

    def bound(config: RunnableConfig) -> AgentTools:
        room_id = config.get('configurable', {}).get('thread_id')
        if not isinstance(room_id, str) or not room_id:
            raise ValueError('Missing Band room execution context')
        agent = holder['agent']
        return AgentTools(room_id, agent.runtime.link.rest, agent_id=ids[role])

    def lock(tools):
        # Process-local serialization prevents duplicate tool calls racing in a room.
        # All durable facts and handoffs remain exclusively in Band.
        return locks.setdefault(tools.room_id, asyncio.Lock())

    @tool
    async def band_read_case(config: RunnableConfig) -> dict:
        """Read authenticated Band protocol records for the CURRENT room. No room argument."""
        tools = bound(config)
        records = await room_records(tools, ids)
        if role in ('grapher','closer'):
            return approved_payload(records)
        if role == 'researcher':
            briefs = [r for r in records if r['kind'] == 'BRIEF']
            return briefs[-1] if briefs else {'status':'waiting for Scribe brief'}
        if role == 'desk':
            return {'records':records}
        return case_state(records)

    result = [band_read_case]
    if role == 'desk':
        @tool
        async def band_ingest_fixture(fixture: str, config: RunnableConfig) -> dict:
            """Create a Band case from an explicitly requested fixture ID, e.g. transcript_1. The authenticated human request is loaded from Band, not supplied by the model."""
            tools = bound(config)
            if fixture not in ('transcript_1','transcript_2','transcript_alias'):
                raise ValueError('Unknown fixture ID')
            async with lock(tools):
                await tools.get_participants()
                humans = [p for p in tools.participants if str(p.get('type','')).casefold() == 'user']
                human_ids = {p['id'] for p in humans}
                requests = []
                for message in await raw_messages(tools):
                    if str(message.get('sender_type','')).casefold() != 'user' or message.get('sender_id') not in human_ids:
                        continue
                    match = re.fullmatch(r'/ingest fixture:(transcript_1|transcript_2|transcript_alias)(?: run:([a-zA-Z0-9_-]{1,100}))?', message.get('content','').strip())
                    if match:
                        requests.append((message, match))
                if not requests:
                    raise ValueError('No authenticated human /ingest fixture request in this lobby')
                initiating, match = requests[-1]
                if match.group(1) != fixture:
                    raise ValueError('Fixture differs from latest authenticated human request')
                request_id = match.group(2) or initiating['id']
                existing = await room_records(tools, ids)
                matches = [r for r in existing if r['kind']=='CASE_CREATED' and r.get('initiating_message_id')==initiating['id']]
                if matches:
                    return matches[-1]
                human = next(p for p in humans if p['id']==initiating['sender_id'])
                recording = json.loads((Path(__file__).parents[1]/'fixtures'/f'{fixture}.json').read_text())
                recording['human_id'] = human['id']
                recording['source'] = 'synthetic fixture; not a live Plaud recording'
                await action_event(tools, 'Creating a synthetic-fixture case in Band')
                room_id = await tools.create_chatroom()
                case = AgentTools(room_id, tools.rest, agent_id=ids['desk'])
                await case.add_participant(human['id'])
                for participant in ('scribe','critic'):
                    await recruit(case, participant, ids)
                await post(case,'TRANSCRIPT',{'recording':recording},['scribe','critic'],ids)
                payload = {'fixture':fixture, 'request_id':request_id, 'initiating_message_id':initiating['id'], 'room_id':room_id}
                await post(tools,'CASE_CREATED',payload,[],ids)
                return payload
        result.append(band_ingest_fixture)
    if role == 'scribe':
        @tool
        async def band_publish_brief(brief: Brief, config: RunnableConfig) -> dict:
            """Publish BRIEF, recruit Researcher only for companies, and request Critic review. Revision is runtime controlled."""
            tools = bound(config)
            async with lock(tools):
                return await submit_brief(tools, ids, brief)
        result.append(band_publish_brief)
    if role == 'critic':
        @tool
        async def band_review_brief(approve: bool, reasons: list[str], config: RunnableConfig) -> dict:
            """Judge CURRENT Scribe brief. Runtime adds non-overridable quote/owner/source checks; passing approval admits downstream workers."""
            tools = bound(config)
            async with lock(tools):
                return await review(tools, ids, approve, reasons)
        result.append(band_review_brief)
    if role == 'researcher':
        @tool
        async def band_report_research_unavailable(config: RunnableConfig) -> dict:
            """Honestly report external enrichment is not implemented; supplies no invented facts or sources."""
            tools = bound(config)
            async with lock(tools):
                records = await room_records(tools, ids)
                briefs = [r for r in records if r['kind']=='BRIEF']
                if not briefs or not briefs[-1]['brief'].get('companies'):
                    raise ValueError('No authenticated company-bearing Scribe brief')
                companies_digest = digest({'companies':briefs[-1]['brief']['companies']})
                existing = [r for r in records if r['kind']=='ENRICHMENT' and r.get('companies_digest')==companies_digest]
                if existing:
                    return existing[-1]
                payload = {'facts':[], 'companies_digest':companies_digest, 'status':'NOT_IMPLEMENTED', 'tools':['Similarweb','Brave']}
                await action_event(tools, 'Research integrations pending; reporting no external facts')
                await post(tools,'ENRICHMENT',payload,['critic','scribe'],ids)
                return payload
        result.append(band_report_research_unavailable)
    if role in ('grapher','closer'):
        @tool
        async def band_report_output_unavailable(config: RunnableConfig) -> dict:
            """Verify authentic Critic approval and report pending graph/CRM integration. Never claims a write succeeded."""
            tools = bound(config)
            payload = approved_payload(await room_records(tools, ids))
            result = {'role':role, 'revision':payload['revision'], 'status':'NOT_IMPLEMENTED',
                      'integration':'Neo4j/Nebius' if role=='grapher' else 'Merge CRM/follow-up'}
            await action_event(tools, 'Approval verified; downstream integration not implemented')
            await post(tools,'OUTPUT',result,['critic'],ids)
            return result
        result.append(band_report_output_unavailable)
    return result


def build_agent(role: str, instructions: str):
    configure_timeouts()
    ids = identities()
    holder = {}
    tools = make_tools(role, holder, ids)
    adapter = LangGraphAdapter(llm=llm(role), additional_tools=tools,
        include_tools=[], capabilities=set(), emit={Emit.TOOL_CALLS, Emit.USAGE},
        recursion_limit=16, custom_section=instructions)
    agent = Agent.create(adapter=adapter, agent_id=ids[role], api_key=credentials(role)[1])
    holder['agent'] = agent
    return agent


def run(role: str, instructions: str):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    asyncio.run(build_agent(role, instructions).run())
