import tkinter as tk
from tkinter import ttk, messagebox
import platform
import os
from datetime import datetime

class SettingsUI:
    STATES = ["Open", "Focused", "Away", "Off"]
    STATE_COLORS = {
        "Open": "#10B981",    # Green
        "Focused": "#EF4444", # Red
        "Away": "#3B82F6",    # Blue
        "Off": "#94A3B8"      # Gray
    }
    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, root, config_store, device_manager):
        self.root = root
        self.config_store = config_store
        self.device_manager = device_manager
        
        self.root.title("Blynclight Scheduler")
        self.root.geometry("700x800")
        self.root.configure(bg="#F8FAFC")
        
        # Internal state for rules
        self.rules = []
        for r in self.config_store.config.get("rules", []):
            # Ensure all keys exist
            rule = {
                "days": r.get("days", []),
                "start": r.get("start", "09:00"),
                "end": r.get("end", "17:00"),
                "state": r.get("state", "focused").capitalize(),
                "enabled": r.get("enabled", True)
            }
            self.rules.append(rule)
            
        self.setup_ui()
        self.refresh_preview()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#FFFFFF", height=80, highlightthickness=1, highlightbackground="#E2E8F0")
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        tk.Label(header, text="Blynclight Scheduler", font=("Arial", 18, "bold"), bg="#FFFFFF", fg="#1E293B").pack(side="left", padx=25)
        
        self.status_dot = tk.Canvas(header, width=12, height=12, bg="#FFFFFF", highlightthickness=0)
        self.status_dot.pack(side="right", padx=(0, 25))
        self.status_dot.create_oval(2, 2, 11, 11, fill="#94A3B8", outline="")
        
        self.status_lbl = tk.Label(header, text="Status: Away", font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#64748B")
        self.status_lbl.pack(side="right", padx=10)

        # Scrollable Rule Area
        main_container = tk.Frame(self.root, bg="#F8FAFC")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Default State Section
        def_frame = tk.Frame(main_container, bg="#FFFFFF", padx=20, pady=15, highlightthickness=1, highlightbackground="#E2E8F0")
        def_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(def_frame, text="All other time:", font=("Arial", 12, "bold"), bg="#FFFFFF", fg="#1E293B").pack(side="left")
        
        self.def_state_var = tk.StringVar(value=self.config_store.config.get("default_state", "away").capitalize())
        def_combo = ttk.Combobox(def_frame, textvariable=self.def_state_var, values=self.STATES, state="readonly", width=12)
        def_combo.pack(side="left", padx=15)
        def_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_preview())

        # Rules Section
        rules_header = tk.Frame(main_container, bg="#F8FAFC")
        rules_header.pack(fill="x", pady=(0, 10))
        tk.Label(rules_header, text="Scheduled Rules", font=("Arial", 13, "bold"), bg="#F8FAFC", fg="#1E293B").pack(side="left")
        
        tk.Button(rules_header, text="+ Add Rule", command=self.add_rule, bg="#6366F1", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=10).pack(side="right")

        # Rules List (Scrollable)
        list_canvas = tk.Canvas(main_container, bg="#F8FAFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=list_canvas.yview)
        self.rules_frame = tk.Frame(list_canvas, bg="#F8FAFC")
        
        self.rules_frame.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
        list_canvas.create_window((0, 0), window=self.rules_frame, anchor="nw", width=640)
        list_canvas.configure(yscrollcommand=scrollbar.set)
        
        list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.render_rules()

        # Footer
        footer = tk.Frame(self.root, bg="#FFFFFF", height=70, highlightthickness=1, highlightbackground="#E2E8F0")
        footer.pack(fill="x", side="bottom")
        
        tk.Button(footer, text="Save & Apply", command=self.save_settings, bg="#6366F1", fg="white", font=("Arial", 11, "bold"), relief="flat", padx=30, pady=8).pack(pady=15)

    def render_rules(self):
        for widget in self.rules_frame.winfo_children():
            widget.destroy()
            
        for idx, rule in enumerate(self.rules):
            row = tk.Frame(self.rules_frame, bg="#FFFFFF", padx=15, pady=15, highlightthickness=1, highlightbackground="#E2E8F0")
            row.pack(fill="x", pady=5)
            
            # Days
            day_frame = tk.Frame(row, bg="#FFFFFF")
            day_frame.pack(fill="x")
            
            rule["day_vars"] = []
            for d in self.DAYS:
                v = tk.BooleanVar(value=d in rule["days"])
                rule["day_vars"].append(v)
                cb = tk.Checkbutton(day_frame, text=d, variable=v, bg="#FFFFFF", font=("Arial", 9), command=self.refresh_preview)
                cb.pack(side="left", padx=2)
            
            # Bottom row: times, state, enabled, delete
            ctrl_row = tk.Frame(row, bg="#FFFFFF")
            ctrl_row.pack(fill="x", pady=(10, 0))
            
            tk.Label(ctrl_row, text="From:", bg="#FFFFFF", font=("Arial", 10)).pack(side="left")
            start_ent = tk.Entry(ctrl_row, width=6, font=("Arial", 10))
            start_ent.insert(0, rule["start"])
            start_ent.pack(side="left", padx=5)
            rule["start_ent"] = start_ent
            
            tk.Label(ctrl_row, text="To:", bg="#FFFFFF", font=("Arial", 10)).pack(side="left")
            end_ent = tk.Entry(ctrl_row, width=6, font=("Arial", 10))
            end_ent.insert(0, rule["end"])
            end_ent.pack(side="left", padx=5)
            rule["end_ent"] = end_ent
            
            state_var = tk.StringVar(value=rule["state"])
            state_cmbo = ttk.Combobox(ctrl_row, textvariable=state_var, values=self.STATES, state="readonly", width=10)
            state_cmbo.pack(side="left", padx=15)
            rule["state_var"] = state_var
            state_cmbo.bind("<<ComboboxSelected>>", lambda e: self.refresh_preview())
            
            en_var = tk.BooleanVar(value=rule["enabled"])
            tk.Checkbutton(ctrl_row, text="Enabled", variable=en_var, bg="#FFFFFF", font=("Arial", 10), command=self.refresh_preview).pack(side="left")
            rule["en_var"] = en_var
            
            tk.Button(ctrl_row, text="Delete", fg="#EF4444", bg="#FFFFFF", relief="flat", command=lambda i=idx: self.delete_rule(i)).pack(side="right")

    def add_rule(self):
        self.sync_rules()
        self.rules.append({
            "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "start": "09:00",
            "end": "17:00",
            "state": "Focused",
            "enabled": True
        })
        self.render_rules()
        self.refresh_preview()

    def delete_rule(self, idx):
        self.sync_rules()
        self.rules.pop(idx)
        self.render_rules()
        self.refresh_preview()

    def sync_rules(self):
        """Pulls UI data into the self.rules list."""
        for rule in self.rules:
            if "day_vars" in rule:
                rule["days"] = [self.DAYS[i] for i, v in enumerate(rule["day_vars"]) if v.get()]
                rule["start"] = rule["start_ent"].get()
                rule["end"] = rule["end_ent"].get()
                rule["state"] = rule["state_var"].get()
                rule["enabled"] = rule["en_var"].get()

    def refresh_preview(self):
        """Shows what the state would be RIGHT NOW based on current unsaved UI."""
        self.sync_rules()
        
        # Temporary config object for evaluation
        tmp_config = {
            "default_state": self.def_state_var.get().lower(),
            "rules": [{
                "days": r["days"],
                "start": r["start"],
                "end": r["end"],
                "state": r["state"].lower(),
                "enabled": r["enabled"]
            } for r in self.rules]
        }
        
        # We'd need the engine but let's just do a quick manual check for the UI label
        # To avoid circularity or complex imports here, let's just update based on the list
        self.update_status_bar(tmp_config)

    def update_status_bar(self, config):
        # We need to import the engine here to avoid circularity if called during initialization
        from schedule_engine import ScheduleEngine
        class MockStore:
            def __init__(self, c): self.config = c
            def get(self, k, d=None): return self.config.get(k, d)
        
        engine = ScheduleEngine(MockStore(config))
        state = engine.get_desired_status().capitalize()
        
        self.status_lbl.config(text=f"Current State: {state}")
        color = self.STATE_COLORS.get(state, "#94A3B8")
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 11, 11, fill=color, outline="")

    def save_settings(self):
        self.sync_rules()
        
        # Validate HH:MM
        for r in self.rules:
            try:
                datetime.strptime(r["start"], "%H:%M")
                datetime.strptime(r["end"], "%H:%M")
            except:
                messagebox.showerror("Error", f"Invalid time format in rules. Use HH:MM.")
                return

        # Prepare final config
        self.config_store.config["default_state"] = self.def_state_var.get().lower()
        self.config_store.config["rules"] = [{
            "days": r["days"],
            "start": r["start"],
            "end": r["end"],
            "state": r["state"].lower(),
            "enabled": r["enabled"]
        } for r in self.rules]
        
        self.config_store.save_config()
        messagebox.showinfo("Success", "Settings saved and applied!")
        self.root.destroy()
