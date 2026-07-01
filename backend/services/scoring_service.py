import json
import logging
import re
from pathlib import Path
from uuid import UUID

import anthropic
from sqlalchemy.orm import Session

from config import settings
from models.client import Client
from models.company import Company
from models.score import Score

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "scoring.txt"
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1024

# Strip markdown code fences Claude sometimes wraps JSON in
_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class ScoringService:
    def __init__(self, db: Session, anthropic_client=None):
        self.db = db
        self._claude = anthropic_client or anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._prompt_template = _PROMPT_PATH.read_text()

    def score_company(self, company_id: UUID, client_id: UUID) -> dict:
        company = (
            self.db.query(Company)
            .filter(Company.id == company_id, Company.client_id == client_id)
            .one()
        )
        client = self.db.query(Client).filter(Client.id == client_id).one()

        prompt = self._build_prompt(company, client)
        raw_response = self._call_claude(prompt)
        result = self._parse_response(raw_response)

        score = self._write_score(company_id, client_id, result)

        return {
            "score_id": str(score.id),
            "company_id": str(company_id),
            "client_id": str(client_id),
            "total_score": result["total_score"],
            "dimension_scores": result["dimension_scores"],
            "scoring_notes": result["scoring_notes"],
            "recommendation": result["recommendation"],
        }

    # ── private ───────────────────────────────────────────────────────────────

    def _build_prompt(self, company: Company, client: Client) -> str:
        company_data = {
            "name": company.name,
            "sector": company.sector,
            "stage": company.stage,
            "funding_total": company.funding_total,
            "latest_round_size": company.latest_round_size,
            "source": company.source,
            "source_url": company.source_url,
            "raw_data": company.raw_data,
        }
        # Use replace() instead of .format() — the prompt template contains
        # literal JSON braces in the example output block
        return (
            self._prompt_template
            .replace("{thesis_json}", json.dumps(client.thesis_json, indent=2))
            .replace("{company_data}", json.dumps(company_data, indent=2))
        )

    def _call_claude(self, prompt: str) -> str:
        message = self._claude.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def _parse_response(self, text: str) -> dict:
        match = _CODE_FENCE_RE.search(text)
        json_str = match.group(1) if match else text.strip()
        return json.loads(json_str)

    def _write_score(self, company_id: UUID, client_id: UUID, result: dict) -> Score:
        score = Score(
            company_id=company_id,
            client_id=client_id,
            total_score=result["total_score"],
            dimension_scores=result["dimension_scores"],
            scoring_notes=result["scoring_notes"],
            recommendation=result.get("recommendation"),
        )
        self.db.add(score)
        self.db.commit()
        return score
