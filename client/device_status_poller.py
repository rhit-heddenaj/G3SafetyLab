import threading


class DeviceStatusPoller:
    def __init__(
        self, client, on_status, interval_seconds=3,
        on_inventory=None, on_inventory_error=None
    ):
        self.client = client
        self.on_status = on_status
        self.interval_seconds = interval_seconds
        self.on_inventory = on_inventory
        self.on_inventory_error = on_inventory_error
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="device-status", daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self.on_status(self.client.get("/status").replace("\n", " | "))
            except Exception:
                pass
            if self.on_inventory:
                try:
                    self.on_inventory(self.client.drugs())
                except Exception as exc:
                    if self.on_inventory_error:
                        self.on_inventory_error(exc)
            self._stop_event.wait(self.interval_seconds)

    def stop(self):
        self._stop_event.set()
