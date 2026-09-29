"""Thin wrappers around the official Band credential loader."""
import os
from uuid import UUID
from band.config.loader import load_agent_config
from band.client.rest import DEFAULT_REQUEST_OPTIONS
from hallway.common.llm import ROLES


def credentials(role: str) -> tuple[str, str]:
    if role not in ROLES:
        raise ValueError('Unknown role')
    id_var=f'BAND_{role.upper()}_AGENT_ID'
    key_var=f'BAND_{role.upper()}_API_KEY'
    if id_var in os.environ or key_var in os.environ:
        agent_id=os.environ.get(id_var,'').strip()
        key=os.environ.get(key_var,'').strip()
        if not agent_id or not key:
            raise ValueError(f'{id_var} and {key_var} must both be nonempty; YAML fallback disabled for partial environment credentials')
    else:
        agent_id,key=load_agent_config(role,config_path=os.getenv('BAND_CONFIG_PATH','agent_config.yaml'))
        agent_id=agent_id.strip();key=key.strip()
        if not agent_id or not key:
            raise ValueError(f'Nonempty Band credentials required for {role}')
    return str(UUID(agent_id)),key


def identities() -> dict[str, str]:
    required=('desk','scribe','critic')
    result={}
    # Peer identities are public routing configuration. An env-configured process
    # needs its OWN credential only; never load or require another agent's key.
    env_mode=any(f'BAND_{role.upper()}_{suffix}' in os.environ
                 for role in ROLES for suffix in ('AGENT_ID','API_KEY'))
    for role in ROLES:
        if env_mode:
            raw=os.environ.get(f'BAND_{role.upper()}_AGENT_ID','').strip()
            if not raw:
                if role in required:
                    raise ValueError(f'BAND_{role.upper()}_AGENT_ID is required')
                continue
        else:
            try:
                raw,_=load_agent_config(role,config_path=os.getenv('BAND_CONFIG_PATH','agent_config.yaml'))
            except FileNotFoundError:
                if role in required: raise
                continue
            except ValueError as exc:
                if role not in required and (str(exc).startswith(f"Agent '{role}' not found") or str(exc).startswith(f"Missing required fields for agent '{role}'")):
                    continue
                raise
        result[role]=str(UUID(raw))
    if len(set(result.values())) != len(result):
        raise ValueError('Configured Band agent IDs must be different')
    return result


def configure_timeouts() -> None:
    # SDK tools import this shared dict, so update it before constructing agents.
    DEFAULT_REQUEST_OPTIONS.update(timeout_in_seconds=10, max_retries=2)
