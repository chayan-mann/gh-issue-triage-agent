import logging

from langchain_core.language_models import BaseChatModel

from triage_bot.agent.prompts import ASSIGNEE_PROMPT, CLASSIFY_PROMPT, REPRO_PROMPT
from triage_bot.agent.state import TriageState
from triage_bot.github.client import GitHubClient
from triage_bot.github.codeowners import default_owners, extract_paths, load_codeowners, owners_for_paths
from triage_bot.schemas.triage import AssigneeSuggestion, Classification, ReproCheck

log = logging.getLogger(__name__)

MARKER = "<!-- triage-bot -->"


class TriageNodes:
    def __init__(self, llm: BaseChatModel, gh: GitHubClient, allowed_labels: list[str]) -> None:
        self.llm = llm
        self.gh = gh
        self.allowed_labels = allowed_labels

    async def fetch_context(self, state: TriageState) -> TriageState:
        issue = state["event"].issue
        comments = await self.gh.list_comments(issue.number)
        if any(MARKER in (c.get("body") or "") for c in comments):
            log.info("Issue #%s already triaged, skipping", issue.number)
            return {"skipped": True}
        text, rules = await load_codeowners(self.gh)
        return {"skipped": False, "codeowners_text": text, "codeowners_rules": rules, "actions_taken": []}

    async def classify(self, state: TriageState) -> TriageState:
        event = state["event"]
        chain = CLASSIFY_PROMPT | self.llm.with_structured_output(Classification)
        result: Classification = await chain.ainvoke(
            {"repo": event.repository.full_name, "title": event.issue.title, "body": event.issue.body or "(empty)"}
        )
        result.labels = [label for label in dict.fromkeys(result.labels) if label in self.allowed_labels]
        return {"classification": result}

    async def check_repro(self, state: TriageState) -> TriageState:
        issue = state["event"].issue
        chain = REPRO_PROMPT | self.llm.with_structured_output(ReproCheck)
        result: ReproCheck = await chain.ainvoke({"title": issue.title, "body": issue.body or "(empty)"})
        return {"repro": result}

    async def suggest_assignee(self, state: TriageState) -> TriageState:
        rules = state.get("codeowners_rules") or []
        if not rules:
            return {"assignee": None}

        issue = state["event"].issue
        paths = extract_paths(f"{issue.title}\n{issue.body or ''}")
        if paths and state.get("codeowners_text"):
            owners = owners_for_paths(state["codeowners_text"], paths)
            if owners:
                return {
                    "assignee": AssigneeSuggestion(
                        matched_pattern=None, owners=owners, reasoning=f"Owns paths mentioned in the issue: {', '.join(paths)}"
                    )
                }

        chain = ASSIGNEE_PROMPT | self.llm.with_structured_output(AssigneeSuggestion)
        classification = state.get("classification")
        result: AssigneeSuggestion = await chain.ainvoke(
            {
                "rules": "\n".join(f"{r.pattern} -> {' '.join(r.owners)}" for r in rules),
                "labels": ", ".join(classification.labels) if classification else "",
                "title": issue.title,
                "body": issue.body or "(empty)",
            }
        )

        by_pattern = {r.pattern: r.owners for r in rules}
        if result.matched_pattern in by_pattern:
            result.owners = by_pattern[result.matched_pattern]
            return {"assignee": result}

        fallback = default_owners(rules)
        if fallback:
            return {"assignee": AssigneeSuggestion(matched_pattern="*", owners=fallback, reasoning="Default code owners")}
        return {"assignee": None}

    async def act(self, state: TriageState) -> TriageState:
        issue = state["event"].issue
        actions = list(state.get("actions_taken") or [])
        classification = state.get("classification")

        existing = {label.name for label in issue.labels}
        new_labels = [label for label in (classification.labels if classification else []) if label not in existing]
        if new_labels:
            await self.gh.ensure_labels(new_labels)
            await self.gh.add_labels(issue.number, new_labels)
            actions.append(f"labels:{','.join(new_labels)}")

        await self.gh.create_comment(issue.number, build_comment(state))
        actions.append("comment")
        return {"actions_taken": actions}


def build_comment(state: TriageState) -> str:
    issue = state["event"].issue
    classification = state.get("classification")
    repro = state.get("repro")
    assignee = state.get("assignee")

    lines = [MARKER, f"Thanks for opening this issue, @{issue.user.login}!", ""]
    if classification and classification.labels:
        lines.append(f"**Labels:** {', '.join(f'`{label}`' for label in classification.labels)}")

    if repro and not repro.has_repro_steps:
        lines += ["", "To help us investigate, could you please add:"]
        lines += [f"- {item}" for item in (repro.missing or ["steps to reproduce the problem"])]

    if assignee and assignee.owners:
        where = f" (matched `{assignee.matched_pattern}`)" if assignee.matched_pattern else ""
        lines += ["", f"**Suggested assignee:** {' '.join(assignee.owners)}{where}"]

    lines += ["", "<sub>Automated triage. A maintainer will follow up.</sub>"]
    return "\n".join(lines)
