"""Thin wrappers around the official Band credential loader."""
import os
from uuid import UUID
from band.config.loader import load_agent_config
from band.client.rest import DEFAULT_REQUEST_OPTIONS
from hallway.common.llm import ROLES


def credentials(role: str) -> tuple[str, str]:
    if role not in ROLES:
        raise ValueError('Unknown role')
    agent_id, key = load_agent_config(role, config_path=os.getenv('BAND_CONFIG_PATH', 'agent_config.yaml'))
    UUID(agent_id)
    return agent_id, key


def identities() -> dict[str, str]:
    result = {role: credentials(role)[0] for role in ROLES}
    if len(set(result.values())) != 6:
        raise ValueError('Six different Band agent IDs are required')
    return result


def configure_timeouts() -> None:
    # SDK tools import this shared dict, so update it before constructing agents.
    DEFAULT_REQUEST_OPTIONS.update(timeout_in_seconds=10, max_retries=2)
