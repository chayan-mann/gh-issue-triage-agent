import logging

from triage_bot.agent.graph import build_graph
from triage_bot.config import Settings
from triage_bot.github.auth import GitHubAppAuth
from triage_bot.github.client import GitHubClient
from triage_bot.llm import get_llm
from triage_bot.schemas.github import IssueEvent

log = logging.getLogger(__name__)


async def run_triage(event: IssueEvent, settings: Settings, auth: GitHubAppAuth) -> None:
    repo = event.repository
    if event.installation is None:
        log.error("Event for %s has no installation id", repo.full_name)
        return

    try:
        token = await auth.installation_token(event.installation.id)
        async with GitHubClient(token, repo.owner.login, repo.name, settings.github_api_url, settings.dry_run) as gh:
            graph = build_graph(get_llm(settings), gh, settings.allowed_labels)
            result = await graph.ainvoke({"event": event})
        log.info("Triaged %s#%s: %s", repo.full_name, event.issue.number, result.get("actions_taken"))
    except Exception:
        log.exception("Triage failed for %s#%s", repo.full_name, event.issue.number)
