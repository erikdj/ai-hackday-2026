"""Band-compatible Crusoe primary → Crusoe fallback → pause, for every role."""
import logging
import os
from langchain_openai import ChatOpenAI
from pydantic import Field

CRUSOE = 'https://api.inference.crusoecloud.com/v1/'
ROLES = ('desk', 'scribe', 'researcher', 'critic', 'grapher', 'closer')


class InferenceUnavailable(RuntimeError):
    """Safe room-facing error; never includes model input or provider response bodies."""


class CrusoeChat(ChatOpenAI):
    """Retain ChatOpenAI's real bind_tools contract while guarding generation.

    Band's documented LangGraphAdapter requires a BaseChatModel, so a top-level
    RunnableWithFallbacks is incompatible. This narrow subclass preserves that
    interface; both clients use only the verified Crusoe endpoint. Streaming is
    disabled so no partial answer escapes before fallback finishes.
    """
    crusoe_fallback: ChatOpenAI = Field(exclude=True, repr=False)
    hallway_role: str = Field(exclude=True)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        try:
            return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            logging.warning('Crusoe inference failed role=%s model=%s error=%s; trying Crusoe fallback',
                            self.hallway_role, self.model_name, type(exc).__name__)
        try:
            return self.crusoe_fallback._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            logging.error('Crusoe fallback failed role=%s model=%s error=%s; case paused',
                          self.hallway_role, self.crusoe_fallback.model_name, type(exc).__name__)
            raise InferenceUnavailable('inference unavailable, case paused') from None

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        try:
            return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            logging.warning('Crusoe inference failed role=%s model=%s error=%s; trying Crusoe fallback',
                            self.hallway_role, self.model_name, type(exc).__name__)
        try:
            return await self.crusoe_fallback._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            logging.error('Crusoe fallback failed role=%s model=%s error=%s; case paused',
                          self.hallway_role, self.crusoe_fallback.model_name, type(exc).__name__)
            raise InferenceUnavailable('inference unavailable, case paused') from None


def llm(role: str) -> ChatOpenAI:
    if role not in ROLES:
        raise ValueError('Unknown role')
    kind = 'CRITIC' if role == 'critic' else 'FAST' if role in ('desk', 'grapher') else 'STRONG'
    model = os.environ.get(f'CRUSOE_MODEL_{kind}', '').strip()
    fallback = os.environ.get(f'CRUSOE_MODEL_{kind}_FALLBACK', '').strip() or os.environ.get('CRUSOE_MODEL_FALLBACK', '').strip()
    key = os.environ.get('CRUSOE_API_KEY', '').strip()
    if not model or not key or not fallback or fallback == model:
        raise ValueError(f'CRUSOE_API_KEY, catalog-verified CRUSOE_MODEL_{kind} and a distinct Crusoe fallback are required')
    # Never let an environment override silently route transcript-bearing calls elsewhere.
    endpoint = os.getenv('CRUSOE_BASE_URL', CRUSOE).rstrip('/')
    if endpoint != CRUSOE.rstrip('/'):
        raise ValueError('Only the Crusoe managed inference endpoint is permitted')
    if role == 'critic':
        strong = os.environ.get('CRUSOE_FAMILY_STRONG', '').strip().casefold()
        critic = os.environ.get('CRUSOE_FAMILY_CRITIC', '').strip().casefold()
        if not strong or not critic or strong == critic:
            raise ValueError('Set different verified CRUSOE_FAMILY_STRONG and CRUSOE_FAMILY_CRITIC')
    logging.info('brain role=%s provider=Crusoe model=%s fallback=%s', role, model, fallback)
    options = dict(base_url=endpoint, api_key=key, timeout=10, max_retries=2,
                   disable_streaming=True, use_responses_api=False,
                   max_tokens=2048 if role in ('scribe', 'researcher', 'closer') else 1024)
    # GLM-5.3 is always reasoning-enabled; upstream recommends low for latency:
    # https://docs.z.ai/guides/llm/glm-5.3 (also probed on Crusoe managed inference).
    primary_options=dict(options)
    fallback_options=dict(options)
    if model == 'zai-org/GLM-5.3':
        primary_options['reasoning_effort']='low'
    if fallback == 'zai-org/GLM-5.3':
        fallback_options['reasoning_effort']='low'
    # Only explicitly opted-in catalog IDs receive this provider extension.
    disable_thinking = {value.strip() for value in
                        os.getenv('CRUSOE_DISABLE_THINKING_MODELS', '').split(',') if value.strip()}
    if model in disable_thinking:
        primary_options['extra_body'] = {'chat_template_kwargs': {'enable_thinking': False}}
    if fallback in disable_thinking:
        fallback_options['extra_body'] = {'chat_template_kwargs': {'enable_thinking': False}}
    return CrusoeChat(model=model, hallway_role=role,
                      crusoe_fallback=ChatOpenAI(model=fallback, **fallback_options), **primary_options)
