import asyncio
import time
from datetime import datetime

import httpx
import jwt

from triage_bot.config import Settings

_REFRESH_MARGIN = 300


class GitHubAppAuth:
    def __init__(self, settings: Settings) -> None:
        self._app_id = settings.github_app_id
        self._private_key = settings.github_private_key
        self._api_url = settings.github_api_url
        self._tokens: dict[int, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    def app_jwt(self) -> str:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 540, "iss": self._app_id}
        return jwt.encode(payload, self._private_key, algorithm="RS256")

    async def installation_token(self, installation_id: int) -> str:
        async with self._lock:
            cached = self._tokens.get(installation_id)
            if cached and cached[1] - _REFRESH_MARGIN > time.time():
                return cached[0]

            async with httpx.AsyncClient(base_url=self._api_url, timeout=15) as client:
                resp = await client.post(
                    f"/app/installations/{installation_id}/access_tokens",
                    headers={
                        "Authorization": f"Bearer {self.app_jwt()}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")).timestamp()
            self._tokens[installation_id] = (data["token"], expires_at)
            return data["token"]
