import json
import logging
from collections import OrderedDict

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, status
from pydantic import ValidationError

from triage_bot.config import get_settings
from triage_bot.github.auth import GitHubAppAuth
from triage_bot.schemas.github import IssueEvent
from triage_bot.security import verify_signature
from triage_bot.service import run_triage

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("triage_bot")

app = FastAPI(title="gh-issue-triage-bot")
auth = GitHubAppAuth(settings)


class _RecentDeliveries:
    def __init__(self, maxsize: int = 1000) -> None:
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._maxsize = maxsize

    def seen(self, delivery_id: str) -> bool:
        if delivery_id in self._seen:
            return True
        self._seen[delivery_id] = None
        if len(self._seen) > self._maxsize:
            self._seen.popitem(last=False)
        return False


deliveries = _RecentDeliveries()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook(
    request: Request,
    background: BackgroundTasks,
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    body = await request.body()
    if not verify_signature(settings.github_webhook_secret.get_secret_value(), body, x_hub_signature_256):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

    if x_github_event != "issues":
        return {"status": "ignored", "reason": f"event {x_github_event}"}

    payload = json.loads(body)
    if payload.get("action") != "opened":
        return {"status": "ignored", "reason": f"action {payload.get('action')}"}

    if x_github_delivery and deliveries.seen(x_github_delivery):
        return {"status": "ignored", "reason": "duplicate delivery"}

    try:
        event = IssueEvent.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid payload") from exc

    if event.sender.is_bot:
        return {"status": "ignored", "reason": "bot sender"}

    log.info("Queued triage for %s#%s", event.repository.full_name, event.issue.number)
    background.add_task(run_triage, event, settings, auth)
    return {"status": "queued"}
