from dataclasses import dataclass, field
from uuid import uuid4
from patient import Patient


@dataclass(frozen=True)
class DosePlan:
    patient: Patient
    drug: str
    dosage_mg: str
    frequency_seconds: str
    until_minutes: str
    plan_id: str = field(default_factory=lambda: str(uuid4()))
