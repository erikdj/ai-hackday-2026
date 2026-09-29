"""One Crusoe model factory; catalog IDs must be configured, never guessed."""
import logging
import os
from langchain_openai import ChatOpenAI

CRUSOE = 'https://api.inference.crusoecloud.com/v1/'
ROLES = ('desk', 'scribe', 'researcher', 'critic', 'grapher', 'closer')


def llm(role: str) -> ChatOpenAI:
    if role not in ROLES:
        raise ValueError('Unknown role')
    kind = 'CRITIC' if role == 'critic' else 'FAST' if role in ('desk', 'grapher') else 'STRONG'
    model = os.environ.get(f'CRUSOE_MODEL_{kind}', '').strip()
    key = os.environ.get('CRUSOE_API_KEY', '').strip()
    if not model or not key:
        raise ValueError(f'CRUSOE_API_KEY and catalog-verified CRUSOE_MODEL_{kind} required')
    if role == 'critic':
        strong = os.environ.get('CRUSOE_FAMILY_STRONG', '').strip().casefold()
        critic = os.environ.get('CRUSOE_FAMILY_CRITIC', '').strip().casefold()
        if not strong or not critic or strong == critic:
            raise ValueError('Set different verified CRUSOE_FAMILY_STRONG and CRUSOE_FAMILY_CRITIC')
    logging.info('brain role=%s provider=Crusoe model=%s', role, model)
    # Fail visibly on exhaustion. No implicit provider substitution or fabricated output.
    return ChatOpenAI(base_url=os.getenv('CRUSOE_BASE_URL', CRUSOE), api_key=key, model=model, timeout=10, max_retries=2)
