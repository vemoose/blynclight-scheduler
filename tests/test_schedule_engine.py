import pytest
from datetime import datetime
from schedule_engine import ScheduleEngine

class MockConfig:
    def __init__(self, config):
        self.config = config
    def get(self, key, default=None):
        return self.config.get(key, default)

def test_default_state():
    config = MockConfig({"default_state": "away", "rules": []})
    engine = ScheduleEngine(config)
    
    # Monday at 10:00 AM
    now = datetime(2026, 2, 2, 10, 0) 
    assert engine.get_desired_status(now) == "away"

def test_single_rule_match():
    rules = [{"days": ["Mon"], "start": "09:00", "end": "11:00", "state": "open", "enabled": True}]
    config = MockConfig({"default_state": "away", "rules": rules})
    engine = ScheduleEngine(config)
    
    # Monday at 10:00 AM (Match)
    now = datetime(2026, 2, 2, 10, 0)
    assert engine.get_desired_status(now) == "open"
    
    # Monday at 11:01 AM (No Match - Exclusive)
    now = datetime(2026, 2, 2, 11, 1)
    assert engine.get_desired_status(now) == "away"

def test_last_match_wins():
    rules = [
        {"days": ["Mon"], "start": "09:00", "end": "12:00", "state": "open", "enabled": True},
        {"days": ["Mon"], "start": "10:00", "end": "11:00", "state": "focused", "enabled": True}
    ]
    config = MockConfig({"default_state": "away", "rules": rules})
    engine = ScheduleEngine(config)
    
    # Monday at 10:30 AM (Matches both, last wins)
    now = datetime(2026, 2, 2, 10, 30)
    assert engine.get_desired_status(now) == "focused"

def test_overnight_rule():
    # Rule spans midnight: 22:00 -> 02:00
    # If checked at 23:00 Monday, it should match.
    # If checked at 01:00 Monday, it should match (because 01:00 < 02:00).
    rules = [{"days": ["Mon"], "start": "22:00", "end": "02:00", "state": "off", "enabled": True}]
    config = MockConfig({"default_state": "away", "rules": rules})
    engine = ScheduleEngine(config)
    
    # Monday at 11:00 PM (Match)
    now = datetime(2026, 2, 2, 23, 0)
    assert engine.get_desired_status(now) == "off"
    
    # Monday at 01:00 AM (Match - spanning midnight logic)
    now = datetime(2026, 2, 2, 1, 0)
    assert engine.get_desired_status(now) == "off"
    
    # Tuesday at 01:00 AM (No match if 'Tue' not in days, since each rule is evaluated per-day)
    # The requirement says "If current_day in rule.days AND time in range".
    now = datetime(2026, 2, 3, 1, 0)
    assert engine.get_desired_status(now) == "away"

def test_boundary_times():
    rules = [{"days": ["Mon"], "start": "09:00", "end": "10:00", "state": "open", "enabled": True}]
    config = MockConfig({"default_state": "away", "rules": rules})
    engine = ScheduleEngine(config)
    
    # Exactly 09:00 (Inclusive)
    now = datetime(2026, 2, 2, 9, 0)
    assert engine.get_desired_status(now) == "open"
    
    # Exactly 10:00 (Exclusive)
    now = datetime(2026, 2, 2, 10, 0)
    assert engine.get_desired_status(now) == "away"

def test_disabled_rule():
    rules = [{"days": ["Mon"], "start": "09:00", "end": "17:00", "state": "open", "enabled": False}]
    config = MockConfig({"default_state": "away", "rules": rules})
    engine = ScheduleEngine(config)
    
    now = datetime(2026, 2, 2, 10, 0)
    assert engine.get_desired_status(now) == "away"
