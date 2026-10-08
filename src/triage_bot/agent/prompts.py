from langchain_core.prompts import ChatPromptTemplate

CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You triage GitHub issues. Pick every label that applies:\n"
            "- bug: something is broken, crashes, errors or behaves incorrectly\n"
            "- feature: a request for new functionality or an enhancement\n"
            "- docs: missing, wrong or unclear documentation\n"
            "Use only these labels.",
        ),
        ("human", "Repository: {repo}\nTitle: {title}\n\nBody:\n{body}"),
    ]
)

REPRO_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You review bug reports. A report has reproduction steps only if a maintainer could follow it "
            "to trigger the bug: concrete steps or a code snippet, expected vs actual behaviour, and ideally "
            "version or environment. List what is missing.",
        ),
        ("human", "Title: {title}\n\nBody:\n{body}"),
    ]
)

ASSIGNEE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You route GitHub issues to code owners. Given CODEOWNERS rules (pattern -> owners) and an issue, "
            "choose the single most relevant pattern based on the area of the codebase the issue is about. "
            "Return the pattern exactly as written and its owners. Return null if nothing fits.",
        ),
        ("human", "CODEOWNERS rules:\n{rules}\n\nLabels: {labels}\nTitle: {title}\n\nBody:\n{body}"),
    ]
)
