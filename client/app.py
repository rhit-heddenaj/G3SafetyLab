"""Medication Safety Lab client — simulation only."""
import tkinter as tk
from tkinter import ttk, messagebox
from device_client import DeviceClient
from dose_scheduler import DoseScheduler
from device_status_poller import DeviceStatusPoller
from dose_plan import DosePlan


class MainWindow:
    def __init__(self, root):
        self.root = root
        root.title("MEDICATION SAFETY LAB - SIMULATION ONLY")
        root.geometry("1020x670")
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.client = DeviceClient()
        self.scheduler = DoseScheduler(self.client, self.log)
        self.status_poller = DeviceStatusPoller(
            self.client,
            self.set_device_status,
            on_inventory=self.set_drugs,
            on_inventory_error=self.set_inventory_error,
        )
        self.patients = []
        self.drugs = []
        self.current_patient = None

        banner = tk.Label(
            root,
            text="TRAINING SIMULATOR — NEVER CONNECT TO A REAL MEDICAL DEVICE",
            bg="#ffe7ba",
            pady=12,
            font=("TkDefaultFont", 10, "bold"),
        )
        banner.pack(fill="x", padx=10, pady=(10, 5))

        body = tk.Frame(root)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        left = tk.Frame(body, width=320)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        ttk.Button(left, text="Connect / refresh patient list",
                    command=lambda: (self.load_patients(), self.load_drugs())).pack(fill="x")
        self.connection_status = tk.StringVar(value="Not connected")
        ttk.Label(left, textvariable=self.connection_status).pack(fill="x", pady=(4, 8))

        inventory = ttk.LabelFrame(left, text="Drug inventory (simulated mg)", padding=5)
        inventory.pack(fill="x", pady=(0, 8))
        self.inventory_list = ttk.Treeview(
            inventory,
            columns=("drug", "available"),
            show="headings",
            height=5,
        )
        self.inventory_list.heading("drug", text="Training substance")
        self.inventory_list.heading("available", text="Available (mg)")
        self.inventory_list.column("drug", width=150, anchor="w")
        self.inventory_list.column("available", width=115, anchor="e")
        self.inventory_list.pack(fill="x")

        self.patient_list = tk.Listbox(left, exportselection=False)
        self.patient_list.pack(fill="both", expand=True)
        self.patient_list.bind("<<ListboxSelect>>", self.select_patient)

        right = tk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        form = ttk.LabelFrame(right, text="Remote medication commands (simulation)", padding=10)
        form.pack(fill="x", pady=(0, 8))
        form.columnconfigure(1, weight=1)

        self.selected_patient_text = tk.StringVar(value="No patient selected")
        self.drug = tk.StringVar(value="No drug selected")
        self.dose = tk.StringVar(value="2.0")
        self.frequency = tk.StringVar(value="10")
        self.until = tk.StringVar(value="10")
        self.device_status = tk.StringVar(value="Status not available")
        self.drug_dropdown = ttk.Combobox(
            form,
            textvariable=self.drug,
            values=(),
            state="readonly"
        )

        rows = [
            ("Selected patient", ttk.Label(form, textvariable=self.selected_patient_text)),
            ("Training substance", self.drug_dropdown),
            ("Dosage (simulated mg)", ttk.Entry(form, textvariable=self.dose)),
            ("Repeat every (seconds)", ttk.Entry(form, textvariable=self.frequency)),
            ("Repeat for (minutes)", ttk.Entry(form, textvariable=self.until)),
            ("Device telemetry", ttk.Label(form, textvariable=self.device_status)),
        ]
        for row, (label, widget) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
            widget.grid(row=row, column=1, sticky="ew", pady=4)

        buttons = tk.Frame(form)
        buttons.grid(row=len(rows), column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Start simulated schedule",
                   command=self.start_schedule).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Stop schedule",
                   command=self.stop_schedule).pack(side="left")

        self.event_log = tk.Text(right, height=18, wrap="word", state="disabled",
                                 font=("Courier New", 10))
        self.event_log.pack(fill="both", expand=True)

        self.status_poller.start()
        root.after(100, self.load_patients)
        root.after(100, self.load_drugs)

    def ui(self, callback, *args):
        self.root.after(0, lambda: callback(*args))

    def log(self, message):
        self.ui(self._append_log, message)

    def _append_log(self, message):
        self.event_log.configure(state="normal")
        self.event_log.insert("end", str(message) + "\n")
        self.event_log.see("end")
        self.event_log.configure(state="disabled")

    def set_device_status(self, text):
        self.ui(self.device_status.set, text)

    def load_patients(self):
        self.connection_status.set("Connecting...")
        def worker():
            try:
                patients = self.client.patients()
                def update():
                    self.patients = patients
                    self.patient_list.delete(0, "end")
                    self.current_patient = None
                    self.selected_patient_text.set("No patient selected")
                    for patient in patients:
                        self.patient_list.insert("end", str(patient))
                    self.connection_status.set(
                        f"Connected: {len(patients)} simulation patients")
                self.ui(update)
            except Exception as exc:
                self.ui(self.connection_status.set, f"Could not connect: {exc}")
        import threading
        threading.Thread(target=worker, daemon=True).start()

    def load_drugs(self):
        def worker():
            try:
                drugs = self.client.drugs()
                self.ui(self.display_drugs, drugs)
            except Exception as exc:
                self.ui(self.connection_status.set, f"Could not load drugs: {exc}")
        import threading
        threading.Thread(target=worker, daemon=True).start()

    def display_drugs(self, drugs):
        self.drugs = drugs
        self.drug_dropdown["values"] = tuple(drug.name for drug in drugs)
        if drugs and self.drug.get() not in self.drug_dropdown["values"]:
            self.drug.set(drugs[0].name)

        self.inventory_list.delete(*self.inventory_list.get_children())
        for drug in drugs:
            self.inventory_list.insert(
                "",
                "end",
                values=(drug.name, f"{drug.available_amount_mg:g}"),
            )

    def set_drugs(self, drugs):
        self.ui(self.display_drugs, drugs)

    def set_inventory_error(self, error):
        self.ui(
            self.connection_status.set,
            f"Could not refresh drug inventory: {error}",
        )
    
    def select_patient(self, _event=None):
        selection = self.patient_list.curselection()
        self.current_patient = self.patients[selection[0]] if selection else None
        self.selected_patient_text.set(
            str(self.current_patient) if self.current_patient else "No patient selected")

    def start_schedule(self):
        if self.current_patient is None:
            messagebox.showinfo("Select patient", "Select a simulation patient first.")
            return
        plan = DosePlan(
            patient=self.current_patient,
            drug=self.drug.get(),
            dosage_mg=self.dose.get().strip(),
            frequency_seconds=self.frequency.get().strip(),
            until_minutes=self.until.get().strip(),
        )
        try:
            self.scheduler.start(plan, self.log)
            self.log(
                f"Started plan {plan.plan_id} for {plan.patient.id} "
                f"every {plan.frequency_seconds}s; {plan.dosage_mg} simulated mg")
        except Exception as exc:
            self.log(f"Scheduler could not start: {exc}")

    def stop_schedule(self):
        response = self.client.stop_schedule()
        self.log(response)

    def close(self):
        self.scheduler.close()
        self.status_poller.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
