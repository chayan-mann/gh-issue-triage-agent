import re

from codeowners import CodeOwners
from pydantic import BaseModel

from triage_bot.github.client import GitHubClient

CODEOWNERS_PATHS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")

_PATH_RE = re.compile(r"(?<![\w/])((?:[\w.-]+/)+[\w.-]+\.\w+|(?:[\w.-]+/){2,})")


class CodeOwnerRule(BaseModel):
    pattern: str
    owners: list[str]


def parse_codeowners(text: str) -> list[CodeOwnerRule]:
    rules = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pattern, *owners = line.split()
        if owners:
            rules.append(CodeOwnerRule(pattern=pattern, owners=owners))
    return rules


async def load_codeowners(client: GitHubClient) -> tuple[str | None, list[CodeOwnerRule]]:
    for path in CODEOWNERS_PATHS:
        text = await client.get_file(path)
        if text is not None:
            return text, parse_codeowners(text)
    return None, []


def extract_paths(text: str) -> list[str]:
    return list(dict.fromkeys(match.group(1).lstrip("./") for match in _PATH_RE.finditer(text)))


def owners_for_paths(codeowners_text: str, paths: list[str]) -> list[str]:
    matcher = CodeOwners(codeowners_text)
    owners: list[str] = []
    for path in paths:
        for _, owner in matcher.of(path):
            if owner not in owners:
                owners.append(owner)
    return owners


def default_owners(rules: list[CodeOwnerRule]) -> list[str]:
    for rule in reversed(rules):
        if rule.pattern in ("*", "/*", "**"):
            return rule.owners
    return []
