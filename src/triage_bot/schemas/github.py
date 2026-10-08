from pydantic import BaseModel, ConfigDict, Field


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


class User(_Model):
    login: str
    type: str = "User"

    @property
    def is_bot(self) -> bool:
        return self.type == "Bot" or self.login.endswith("[bot]")


class Label(_Model):
    name: str


class Issue(_Model):
    number: int
    title: str
    body: str | None = None
    html_url: str
    user: User
    labels: list[Label] = Field(default_factory=list)


class Owner(_Model):
    login: str


class Repository(_Model):
    name: str
    full_name: str
    owner: Owner


class Installation(_Model):
    id: int


class IssueEvent(_Model):
    action: str
    issue: Issue
    repository: Repository
    sender: User
    installation: Installation | None = None
