from .models import Patient
from .models import Drug
import threading

#You can add more patients for testing
class PatientRepository:
    def __init__(self):
        self.patients = [
            Patient('SIM-101', 'Alex Morgan (SIM)', 'F123', 72.5, 34, 175.0, 72, 98),
            Patient('SIM-102', 'Jordan Taylor (SIM)', 'D222', 85.0, 46, 182.0, 84, 97),
            Patient('SIM-103', 'Casey Rivera (SIM)', 'M543', 58.5, 27, 163.0, 62, 99),
            Patient('SIM-104', 'Riley Chen (SIM)', 'F124', 64.0, 31, 168.0, 76, 98),
        ]
        
    def get_by_id(self, patient_id):
            for patient in self.patients:
                if patient.patient_id == patient_id:
                    return patient
            return None

    def all(self):
        return list(self.patients)
 
#You can add more drugs for testing   
class DrugRespository:
    def __init__(self):
            #**fake** drugs
        self.drugs = [
            Drug('DRUG-A', 'Corumane', 20.0, 30, 500.0, 7200, 14400, True),
            Drug('DRUG-B', 'Zenithium', 10.0, 15, 250.0, 5400, 10800, False),
            Drug('DRUG-C', 'Noxiside', 30.0, 60, 600.0, 10800, 21600, True),
            Drug('DRUG-D', 'Pyrithine', 5.0, 10, 125.0, 1800, 3600, True),
            Drug('DRUG-E', 'Vortexane', 40.0, 45, 800.0, 14400, 28800, False),
        ]
        self._inventory_mg = {drug.name: 1000.0 for drug in self.drugs}
        self._inventory_lock = threading.Lock()
    
    def all(self):
        return list(self.drugs)

    def get_by_name(self, name):
        return next((drug for drug in self.drugs if drug.name == name), None)

    def available_amount_mg(self, name):
        with self._inventory_lock:
            return self._inventory_mg.get(name)

    def dispense(self, name, amount_mg):
        with self._inventory_lock:
            available = self._inventory_mg.get(name)
            if available is None or amount_mg > available:
                return None

            remaining = max(0.0, available - amount_mg)
            self._inventory_mg[name] = remaining
            return available, remaining
