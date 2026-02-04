from datetime import datetime, time

class ScheduleEngine:
    def __init__(self, config_store):
        self.config_store = config_store

    def is_time_in_range(self, start_str, end_str, check_time):
        """Checks if check_time is in [start, end) range. Supports overnight."""
        try:
            start = datetime.strptime(start_str, "%H:%M").time()
            end = datetime.strptime(end_str, "%H:%M").time()

            if start <= end:
                return start <= check_time < end
            else:
                # Spans midnight
                return check_time >= start or check_time < end
        except:
            return False

    def get_desired_status(self, now=None):
        if now is None:
            now = datetime.now()
        
        current_time = now.time()
        current_day = now.strftime("%a") # Mon, Tue, etc.
        
        # 1. ALWAYS PRIORITIZE MANUAL OVERRIDE
        # We reload here to ensure current state is fresh
        self.config_store.reload()
        override = self.config_store.config.get("manual_override")
        
        # Mapping legacy names to new names
        cmap = {"red": "focused", "green": "open", "blue": "away"}
        if override in cmap:
            override = cmap[override]
            
        if override and override.lower() != "none":
            return override.lower()

        # 2. EVALUATE RULES
        settings = self.config_store.config
        rules = settings.get("rules", [])
        default_state = settings.get("default_state", "away")
        
        final_state = default_state
        
        for rule in rules:
            if not rule.get("enabled", True):
                continue
                
            if current_day in rule.get("days", []):
                if self.is_time_in_range(rule["start"], rule["end"], current_time):
                    final_state = rule["state"]
                    
        return final_state
