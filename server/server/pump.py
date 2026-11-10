import threading
import time
import random
import math
from .models import DeviceState

class SimulatedPump:
    def __init__(self, patient_repository, drug_repository):
        self.state = DeviceState()
        self.lock = threading.Lock()
        
        self.doseTracker = {} 
        self.outbound_messages = [] 
        self.last_air_bubble = 0
        self.last_battery_drain = time.time()
        self.patient_repository = patient_repository
        self.drug_repository = drug_repository
    
        self.worker_running = True
        self.worker_thread = threading.Thread(target=self._checker_loop, daemon=True)
        self.worker_thread.start()

    def setDose(self, patient_id: str, drug: str, dosage: str, frequency: str, request_id: str) -> str:
        try:
            dosage_mg = float(dosage)
            frequency_seconds = int(frequency)
        except ValueError:
            return 'REJECTED: dosage or frequency is invalid'
        if not math.isfinite(dosage_mg) or dosage_mg <= 0 or frequency_seconds <= 0:
            return 'REJECTED: dosage and frequency must be positive'
        if self.drug_repository.get_by_name(drug) is None:
            return 'REJECTED: drug not found'

        with self.lock:
            self.doseTracker[request_id] = {
                "patient_id": patient_id,
                "drug": drug,
                "dosage": dosage_mg,
                "frequency": frequency_seconds,
                "last_administered": 0.0,
                "dose_amt": 0,
                "air_bubble": False
            }
        return f"Dose set. ID = {request_id}"
        
    def administer(self, request_id) -> str:
      
        with self.lock:
            current = self.doseTracker.get(request_id)
            if not current:
                return 'REJECTED: request_id not found'
            
            if not self.state.pump_enabled:
                return 'REJECTED: simulated device paused'

            inventory_reading = self.drug_repository.dispense(
                current["drug"], current["dosage"])
            if inventory_reading is None:
                self.doseTracker.pop(request_id, None)
                message = (
                    f'REJECTED: insufficient simulated inventory for '
                    f'{current["drug"]}; schedule stopped')
                self.notify(message)
                return message
            inventory_before_mg, inventory_after_mg = inventory_reading
            
            current["dose_amt"] += 1
            self.state.total_simulated_doses += 1
            
            current["last_administered"] = time.time()
            
            message = (f'SIMULATED DOSE #{current["dose_amt"]} '
                       f'patient={current["patient_id"]} drug={current["drug"]} '
                       f'requested={current["dosage"]:g} mg '
                       f'inventory_before={inventory_before_mg:g} mg '
                       f'inventory_after={inventory_after_mg:g} mg '
                       f'request={request_id}')
            self.notify(message)

            return 'ADMINISTERED (SIMULATION ONLY): ' + message


    def _checker_loop(self):
        """Runs constantly in the background to evaluate interval-based schedules."""
        while self.worker_running:
            with self.lock:
                items = list(self.doseTracker.items())
            
            now = time.time()

            for req_id, details in items:
                seconds_since_last_dose = now - details["last_administered"]
                
                if seconds_since_last_dose >= details["frequency"]:
                    if self.doseTracker[req_id]["air_bubble"]:
                        patient_id = self.doseTracker[req_id]["patient_id"]
                        patient = self.patient_repository.get_by_id(patient_id)
                        if patient:
                            patient.deteriorate()
                        
                    if self.state.pump_enabled:
                        self.drain_battery()
                        self.air_bubble_generator(req_id)
                        self.administer(req_id)
    
            time.sleep(0.5) 

    def stop_worker(self):
        self.worker_running = False
        self.worker_thread.join()

    def status(self):
        with self.lock:
            return (self.state.battery_percent, self.state.pump_enabled,
                    self.state.total_simulated_doses)

    def notify(self, message: str):
        self.outbound_messages.append(message)
    
    #You can change the rate of battery loss for testing
    def drain_battery(self):
        now = time.time()

        with self.lock:
            if self.state.battery_percent <= 0:
                self.state.pump_enabled = False
            if now - self.last_battery_drain >= 10:
                self.state.battery_percent = max(
                    0, self.state.battery_percent - 2
                )
                self.last_battery_drain = now
            
    def recharge_battery(self, value):
        with self.lock:
            self.state.battery_percent = max(0, min(100, value))
            self.state.pump_enabled = True
            self.notify(
                f"SIMULATION battery changed to {self.state.battery_percent}%"
            )
            
    def set_enabled(self, value):
        with self.lock:
            self.state.pump_enabled = value
            self.notify(f"SIMULATION pump enabled={value}")
    
    #You can change the rate of air bubbles for testing
    def air_bubble_generator(self, req_id):
        now = time.time()
        with self.lock:
            if now - self.last_air_bubble >= 60:
                if random.random() < 0.05:
                    self.doseTracker[req_id]["air_bubble"] = True
                    self.last_air_bubble = now
   
    def stopDose(self) -> str:
        with self.lock:
            self.doseTracker.clear()

        return "SIMULATION schedule stopped"
