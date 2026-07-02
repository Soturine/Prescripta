from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PatientBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    birth_date: date | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    allergies: list[str] = Field(default_factory=list)
    comorbidities: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_age_or_birth_date(self) -> "PatientBase":
        if self.age is None and self.birth_date is None:
            raise ValueError("Informe idade ou data de nascimento.")
        return self


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    birth_date: date | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    weight_kg: float | None = Field(default=None, gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    allergies: list[str] | None = None
    comorbidities: list[str] | None = None
    current_medications: list[str] | None = None


class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
