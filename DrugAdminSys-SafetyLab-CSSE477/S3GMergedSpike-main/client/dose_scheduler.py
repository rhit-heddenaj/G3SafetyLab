import threading
import time
from uuid import uuid4


class DoseScheduler:
    """Sends dose requests and polls the simulation server for notifications."""
    def __init__(self, client, default_log=print):
        self.client = client
        self.global_log = default_log
        self._stop_event = threading.Event()
        self._listener_thread = threading.Thread(
            target=self._notification_listener, name="dose-notifications", daemon=True)
        self._listener_thread.start()

    def start(self, plan, log):
        self.global_log = log
        data = {
            "patient": plan.patient.id,
            "drug": plan.drug,
            "dosage": plan.dosage_mg,
            "frequency": plan.frequency_seconds,
            "request_id": str(uuid4()),
        }
        try:
            answer = self.client.post("/dose", data)
            log(answer)
        except Exception as exc:
            log(f"Request error: {exc}")

    def _notification_listener(self):
        while not self._stop_event.is_set():
            try:
                update = self.client.get("/notifications")
                if update and update.strip():
                    for line in update.splitlines():
                        if self.global_log is not None:
                            self.global_log("[PUMP NOTIFICATION] " + line)
            except Exception:
                if self.global_log is not None:
                    self.global_log("[Poller Connection Status] Waiting for pump server...")
            self._stop_event.wait(2)

    def stop(self):
        self.close()

    def close(self):
        self._stop_event.set()
