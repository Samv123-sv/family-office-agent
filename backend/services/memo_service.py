import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import anthropic
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from models.client import Client
from models.company import Company
from models.memo import Memo
from models.score import Score

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "memo_generation.txt"
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 2000
_CACHE_DAYS = 7

_CODE_FENCE_RE = re.compile(r"```(?:\w+)?\s*(.*?)\s*```", re.DOTALL)


class MemoService:
    def __init__(self, db: Session, anthropic_client=None):
        self.db = db
        self._claude = anthropic_client or anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._prompt_template = _PROMPT_PATH.read_text()

    def generate_memo(self, company_id: UUID, client_id: UUID) -> dict:
        cached = self._get_cached_memo(company_id, client_id)
        if cached:
            logger.info("memo cache hit company=%s", company_id)
            return self._format_result(cached, cached=True)

        company = (
            self.db.query(Company)
            .filter(Company.id == company_id, Company.client_id == client_id)
            .one()
        )
        client = self.db.query(Client).filter(Client.id == client_id).one()
        score = (
            self.db.query(Score)
            .filter(Score.company_id == company_id, Score.client_id == client_id)
            .order_by(Score.scored_at.desc())
            .first()
        )

        prompt = self._build_prompt(company, client, score)
        content = self._call_claude(prompt)
        memo = self._write_memo(company_id, client_id, content)

        return self._format_result(memo, cached=False)

    # ── private ───────────────────────────────────────────────────────────────

    def _get_cached_memo(self, company_id: UUID, client_id: UUID) -> Memo | None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=_CACHE_DAYS)
        return (
            self.db.query(Memo)
            .filter(
                Memo.company_id == company_id,
                Memo.client_id == client_id,
                Memo.generated_at >= cutoff,
            )
            .order_by(Memo.generated_at.desc())
            .first()
        )

    def _build_prompt(self, company: Company, client: Client, score: Score | None) -> str:
        thesis = client.thesis_json

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

        check_size = thesis.get("check_size", {})
        if check_size:
            cs_str = f"${check_size.get('min', 0):,.0f}–${check_size.get('max', 0):,.0f}"
        else:
            cs_str = "Not specified"

        base = (
            self._prompt_template
            .replace("{client_name}", client.name)
            .replace("{thesis_description}", self._thesis_description(thesis))
            .replace("{sectors}", ", ".join(thesis.get("sectors", ["Not specified"])))
            .replace("{stage_range}", " / ".join(thesis.get("stages", ["Not specified"])))
            .replace("{geography}", ", ".join(thesis.get("geography", ["Not specified"])))
            .replace("{check_size}", cs_str)
            .replace("{company_data}", json.dumps(company_data, indent=2))
            .replace("{total_score}", str(score.total_score) if score else "Not yet scored")
            .replace("{scoring_notes}", score.scoring_notes if score else "No scoring data available.")
        )
        return base + self._document_context(company.id, client.id)

    def _document_context(self, company_id: UUID, client_id: UUID) -> str:
        from db import queries
        docs = queries.list_documents_for_company(self.db, company_id, client_id)
        parts = []
        for doc in docs:
            excerpt = (doc.content_text or "").strip()[:2000]
            if excerpt:
                parts.append(f"[{doc.filename}]\n{excerpt}")
        if not parts:
            return ""
        return "\n\nADDITIONAL CONTEXT FROM CLIENT DOCUMENTS:\n" + "\n\n".join(parts)

    def _thesis_description(self, thesis: dict) -> str:
        if desc := thesis.get("description"):
            return desc
        keywords = thesis.get("keywords", [])
        sectors = thesis.get("sectors", [])
        combined = keywords + [s for s in sectors if s not in keywords]
        return f"Focus on {', '.join(combined)} opportunities." if combined else "Diversified private market investments."

    def _call_claude(self, prompt: str) -> str:
        message = self._claude.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text
        match = _CODE_FENCE_RE.search(text)
        return match.group(1) if match else text.strip()

    def _write_memo(self, company_id: UUID, client_id: UUID, content: str) -> Memo:
        latest_version = (
            self.db.query(func.max(Memo.version))
            .filter(Memo.company_id == company_id, Memo.client_id == client_id)
            .scalar()
            or 0
        )
        memo = Memo(
            company_id=company_id,
            client_id=client_id,
            content=content,
            version=latest_version + 1,
            generated_at=datetime.now(timezone.utc),
        )
        self.db.add(memo)
        self.db.commit()
        return memo

    def _format_result(self, memo: Memo, *, cached: bool) -> dict:
        return {
            "memo_id": str(memo.id),
            "company_id": str(memo.company_id),
            "client_id": str(memo.client_id),
            "content": memo.content,
            "version": memo.version,
            "generated_at": memo.generated_at.isoformat(),
            "cached": cached,
        }
