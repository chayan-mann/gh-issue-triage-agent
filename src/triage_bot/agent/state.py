from typing import TypedDict

from triage_bot.github.codeowners import CodeOwnerRule
from triage_bot.schemas.github import IssueEvent
from triage_bot.schemas.triage import AssigneeSuggestion, Classification, ReproCheck


class TriageState(TypedDict, total=False):
    event: IssueEvent
    skipped: bool
    codeowners_text: str | None
    codeowners_rules: list[CodeOwnerRule]
    classification: Classification
    repro: ReproCheck | None
    assignee: AssigneeSuggestion | None
    actions_taken: list[str]
