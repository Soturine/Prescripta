from dataclasses import dataclass
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "baixo"
    MODERATE = "moderado"
    HIGH = "alto"
    CRITICAL = "critico"


class PrescriptionStatus(StrEnum):
    RELEASED = "liberado"
    ATTENTION = "atencao"
    BLOCKED = "bloqueado"


@dataclass(frozen=True)
class Alert:
    code: str
    title: str
    description: str
    severity: RiskLevel
    recommendation: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "recommendation": self.recommendation,
        }
