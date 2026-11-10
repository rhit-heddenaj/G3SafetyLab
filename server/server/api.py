from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from .repository import PatientRepository, DrugRespository
from .pump import SimulatedPump

class DeviceApiHandler(BaseHTTPRequestHandler):
    patient_repository = PatientRepository()
    drug_repository = DrugRespository()
    pump = SimulatedPump(patient_repository, drug_repository)

    def reply(self, code, body):
        data = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split('?')[0]
        with self.pump.lock:
            if self.pump.state.battery_percent <= 0:
                return self.reply(503, "")
            
        if path == '/patients':
            lines = [f'{p.patient_id}|{p.name}|{p.room}|{p.weight}|{p.age}|{p.height}| {p.heart_rate} | {p.oxygen_saturation}' for p in self.patient_repository.all()]
            return self.reply(200, '\n'.join(lines))
        if path == '/drugs':
            lines = [
                f'{drug.drug_id}|{drug.name}|{drug.max_single_dose_mg}|'
                f'{drug.min_interval_seconds}|{drug.max_daily_dose_mg}|'
                f'{drug.half_life_seconds}|{drug.duration_seconds}|'
                f'{drug.requires_age_check}|'
                f'{self.drug_repository.available_amount_mg(drug.name):g}'
                for drug in self.drug_repository.all()
            ]
            return self.reply(200, '\n'.join(lines))
        if path == '/status':
            battery, enabled, count = self.pump.status()
            return self.reply(200, f'battery={battery}\nenabled={str(enabled).lower()}\ncount={count}')
        if path == '/notifications':
            with self.pump.lock:
                payload = "\n".join(self.pump.outbound_messages)
                self.pump.outbound_messages.clear() 
            return self.reply(200, payload)
        return self.reply(404, 'Unknown endpoint')

    def do_POST(self):
        size = int(self.headers.get('Content-Length', '0'))
        if size > 8192:
            return self.reply(413, 'Request too large')
        fields = parse_qs(self.rfile.read(size).decode('utf-8', errors='replace'))
        value = lambda key: fields.get(key, [''])[0]
        
        with self.pump.lock:
            battery_dead = self.pump.state.battery_percent <= 0

        if battery_dead and self.path != '/rechargeBattery':
            return self.reply(503, "")
                    
        if self.path == '/dose':
            result = self.pump.setDose(value('patient'), value('drug'),
                                          value('dosage'), value('frequency'), value('request_id'))
            return self.reply(200, result)
        if self.path == '/rechargeBattery':
            try:
                self.pump.recharge_battery(int(value('percent')))
            except ValueError:
                return self.reply(400, 'Invalid integer')
            return self.reply(200, 'SIMULATION battery updated')
        if self.path == '/changePump':
            self.pump.set_enabled(value('enabled').lower() == 'true')
            return self.reply(200, 'SIMULATION device state updated')
        if self.path == '/stop':
            return self.reply(200, self.pump.stopDose())

        return self.reply(404, 'Unknown endpoint')

    def log_message(self, format, *args):
        print('[DEVICE SIM]', format % args)

def serve():
    address = ('127.0.0.1', 8765)
    server = ThreadingHTTPServer(address, DeviceApiHandler)
    print(f'Device SIMULATOR running at http://{address[0]}:{address[1]}')
    print('TRAINING ONLY: No drugs, patients, actuators, or hardware involved.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        DeviceApiHandler.pump.stop_worker()
        server.server_close()
