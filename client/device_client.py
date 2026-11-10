from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class DeviceClient:
    """HTTP client for the local simulation server."""
    def __init__(self, base_url="http://127.0.0.1:8765", timeout=5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, endpoint):
        request = Request(self.base_url + endpoint, method="GET")
        return self._read(request)

    def post(self, endpoint, values):
        body = urlencode(values).encode("utf-8")
        request = Request(
            self.base_url + endpoint,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            method="POST",
        )
        return self._read(request)

    def _read(self, request):
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8").strip()
        except HTTPError as exc:
            return exc.read().decode("utf-8").strip()

    def stop_schedule(self):
        return self.post("/stop", {})

    def patients(self):
        result = []
        response = self.get("/patients")
        for line in response.splitlines():
            tokens = line.split("|")
            if len(tokens) == 8:
                result.append(
                    __import__("patient").Patient(
                        id=tokens[0],
                        name=tokens[1],
                        room=tokens[2],
                        weight=float(tokens[3]),
                        age=int(tokens[4]),
                        height=float(tokens[5]),
                        heart_rate=int(tokens[6]),
                        oxygen_saturation=int(tokens[7])
                    )
                )
        return result
    
    def drugs(self):
        result = []
        response = self.get("/drugs")
        for line in response.splitlines():
            tokens = [token.strip() for token in line.split("|")]
            if len(tokens) == 9:
                result.append(
                    __import__("drug").Drug(
                        drug_id=tokens[0],
                        name=tokens[1],
                        max_single_dose_mg=float(tokens[2]),
                        min_interval_seconds=int(tokens[3]),
                        max_daily_dose_mg=float(tokens[4]),
                        half_life_seconds=int(tokens[5]),
                        duration_seconds=int(tokens[6]),
                        requires_age_check=tokens[7].lower() == "true",
                        available_amount_mg=float(tokens[8]),
                    )
                )
        return result
