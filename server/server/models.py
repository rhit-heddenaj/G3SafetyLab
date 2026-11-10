from dataclasses import dataclass, field
from datetime import datetime, timezone
import time

#If you feel more fields are needed for a safe system, you can add them
@dataclass
class Patient:
    patient_id: str
    name: str
    room: str
    weight: float
    age: int
    height: float
    heart_rate: int
    oxygen_saturation: int
    last_deterioration: float = 0.0
    
    def deteriorate(self):
        now = time.time()

        if now - self.last_deterioration >= 5:
            self.heart_rate = max(0, self.heart_rate - 5)
            self.oxygen_saturation = max(
                0, self.oxygen_saturation - 1
            )
            self.last_deterioration = now

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

@dataclass
class DeviceState:
    battery_percent: int = 100
    connected: bool = True
    pump_enabled: bool = True
    total_simulated_doses: int = 0
    events: list[str] = field(default_factory=list)

    def log(self, message: str):
        time = datetime.now(timezone.utc).strftime('%H:%M:%S')
        self.events.append(f'{time}Z | {message}')
        self.events = self.events[-120:]
