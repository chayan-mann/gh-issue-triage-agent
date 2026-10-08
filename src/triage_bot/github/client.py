import base64
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

LABEL_COLORS = {"bug": "d73a4a", "feature": "a2eeef", "docs": "0075ca"}


class GitHubClient:
    def __init__(self, token: str, owner: str, repo: str, api_url: str, dry_run: bool = False) -> None:
        self.owner = owner
        self.repo = repo
        self.dry_run = dry_run
        self._http = httpx.AsyncClient(
            base_url=f"{api_url}/repos/{owner}/{repo}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=15,
        )

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._http.aclose()

    async def get_file(self, path: str) -> str | None:
        resp = await self._http.get(f"/contents/{path}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return base64.b64decode(resp.json()["content"]).decode("utf-8")

    async def list_comments(self, number: int) -> list[dict[str, Any]]:
        resp = await self._http.get(f"/issues/{number}/comments", params={"per_page": 100})
        resp.raise_for_status()
        return resp.json()

    async def ensure_labels(self, labels: list[str]) -> None:
        for name in labels:
            if self.dry_run:
                log.info("[dry-run] ensure label %s on %s/%s", name, self.owner, self.repo)
                continue
            resp = await self._http.post("/labels", json={"name": name, "color": LABEL_COLORS.get(name, "ededed")})
            if resp.status_code not in (201, 422):
                resp.raise_for_status()

    async def add_labels(self, number: int, labels: list[str]) -> None:
        if self.dry_run:
            log.info("[dry-run] add labels %s to #%s", labels, number)
            return
        resp = await self._http.post(f"/issues/{number}/labels", json={"labels": labels})
        resp.raise_for_status()

    async def create_comment(self, number: int, body: str) -> None:
        if self.dry_run:
            log.info("[dry-run] comment on #%s:\n%s", number, body)
            return
        resp = await self._http.post(f"/issues/{number}/comments", json={"body": body})
        resp.raise_for_status()
