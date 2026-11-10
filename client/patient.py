from dataclasses import dataclass


@dataclass(frozen=True)
class Patient:
    id: str
    name: str
    room: str
    weight: float
    age: int
    height: float
    heart_rate: int
    oxygen_saturation: int

    def __str__(self):
        return f"{self.id} | {self.name} | {self.room} | {self.weight} | {self.age} | {self.height} | {self.heart_rate} | {self.oxygen_saturation}"
