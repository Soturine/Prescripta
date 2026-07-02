from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEDICO = "medico"
    ENFERMAGEM = "enfermagem"
    AUDITOR = "auditor"


ALL_ROLES = (
    UserRole.ADMIN,
    UserRole.MEDICO,
    UserRole.ENFERMAGEM,
    UserRole.AUDITOR,
)
