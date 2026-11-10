from dataclasses import dataclass


@dataclass(frozen=True)
class Drug:
    drug_id: str
    name: str
    max_single_dose_mg: float
    min_interval_seconds: int
    max_daily_dose_mg: float
    half_life_seconds: int
    duration_seconds: int
    requires_age_check: bool
    available_amount_mg: float

    def __str__(self):
        return f"{self.drug_id} | {self.name} | {self.max_single_dose_mg} | {self.min_interval_seconds} | {self.max_daily_dose_mg} | {self.half_life_seconds} | {self.duration_seconds} | {self.requires_age_check}"
