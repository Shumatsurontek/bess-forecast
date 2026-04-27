from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    severity: Severity
    message: str
    affected_count: int = 0
    sample: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationReport:
    issues: list[ValidationIssue]

    @property
    def blocking_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.BLOCKING)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def is_blocking(self) -> bool:
        return self.blocking_count > 0
