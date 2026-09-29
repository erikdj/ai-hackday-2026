"""Transcript-grounded schema and deterministic veto checks."""
import hashlib
import json
import unicodedata
from urllib.parse import urlparse
from pydantic import BaseModel, ConfigDict, Field


class Person(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    company: str | None = None


class Company(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    domain: str | None = None


class Claim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    quote: str
    speaker: str | None = None


class Commitment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    quote: str
    owner: str | None = None


class Brief(BaseModel):
    model_config = ConfigDict(extra='forbid')
    people: list[Person] = Field(default_factory=list)
    companies: list[Company] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    commitments: list[Commitment] = Field(default_factory=list)
    unresolved_suggestions: list[Claim] = Field(default_factory=list)
    next_steps: list[Commitment] = Field(default_factory=list)


def normalize(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_brief(brief: Brief, recording: dict, enrichment: list[dict]) -> list[str]:
    transcript = normalize(recording['transcript'])
    reasons = []
    people = {normalize(person.name) for person in brief.people}
    for person in brief.people:
        if not normalize(person.name) or normalize(person.name) not in transcript:
            reasons.append(f'person {person.name!r}: name absent from transcript')
    for company in brief.companies:
        if not normalize(company.name) or normalize(company.name) not in transcript:
            reasons.append(f'company {company.name!r}: name absent from transcript')
    for group in ('claims', 'commitments', 'unresolved_suggestions', 'next_steps'):
        for i, item in enumerate(getattr(brief, group), 1):
            if not normalize(item.quote) or normalize(item.quote) not in transcript:
                reasons.append(f'{group} #{i}: quote not found verbatim in transcript')
            if group in ('commitments', 'next_steps'):
                if item.owner and any(term in normalize(item.quote) for term in ('someone should', 'somebody should')):
                    reasons.append(f'{group} #{i}: generic suggestion cannot have a fabricated owner')
                if not item.owner or normalize(item.owner) not in people:
                    reasons.append(f'{group} #{i}: commitment needs a named owner present in people')
    for i, fact in enumerate(enrichment, 1):
        url = urlparse(str(fact.get('url', '')))
        if url.scheme not in ('http', 'https') or not url.netloc:
            reasons.append(f'enrichment #{i}: source URL required')
    return reasons
