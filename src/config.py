# src/config.py
"""
Configuration constants for the Water Pump Automation System.
"""
import os
from datetime import time

# --- Database ---
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATABASE_PATH = os.path.join(DATA_DIR, 'automation_logs.db')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# --- Tank Capacities (in Liters, example values) ---
MAIN_LINE_TANK_CAPACITY = 1000
UNDERGROUND_TANK_CAPACITY = 5000
OVERHEAD_TANK_CAPACITY = 2000

# --- Water Level Thresholds (as percentages) ---
# P1 Operation
P1_START_THRESHOLD_UNDERGROUND = 10.0  # Start P1 if Underground < 10%
P1_STOP_THRESHOLD_MAIN_LINE = 15.0     # Stop P1 if Main Line < 15%
P1_REQ_MAIN_LINE_LEVEL = 15.0          # P1 requires Main Line >= 15% to start
P1_MANUAL_BYPASS_MIN_UNDERGROUND = 5.0 # Allow bypass if Underground < 5%
P1_MANUAL_BYPASS_MIN_MAIN_LINE = 5.0   # Disallow bypass if Main Line < 5%

# P2 Operation
P2_START_THRESHOLD_MAIN_LINE = 5.0     # Condition to consider P2: Main Line < 5%
P2_START_THRESHOLD_UNDERGROUND = 5.0   # Condition to start P2: Underground < 5%
P2_START_THRESHOLD_OVERHEAD = 5.0      # Condition to start P2: Overhead < 5%
P2_STOP_THRESHOLD_UNDERGROUND = 30.0   # Stop P2 when Underground reaches >= 30%

# P3 Operation
P3_START_THRESHOLD_OVERHEAD = 10.0     # Start P3 if Overhead < 10%
P3_REQ_UNDERGROUND_LEVEL = 10.0        # P3 requires Underground >= 10% to start
P3_SIGNAL_PUMP_THRESHOLD_UNDERGROUND = 10.0 # If Underground < 10%, signal P1/P2
P3_SIGNAL_TARGET_UNDERGROUND = 30.0    # Target level for P1/P2 when signaled by P3
P3_WARN_THRESHOLD_OVERHEAD = 5.0       # Warning if Overhead < 5%
P3_WARN_THRESHOLD_UNDERGROUND_LOW = 5.0  # Warning if Underground < 5%
P3_WARN_THRESHOLD_UNDERGROUND_HIGH = 10.0 # Warning if Underground between 5% and 10%
P3_STOP_THRESHOLD_UNDERGROUND = 5.0    # Stop P3 if Underground < 5%

# --- Pump Flow Rates (Liters per second, for simulation) ---
P1_FLOW_RATE = 10.0
P2_FLOW_RATE = 8.0
P3_FLOW_RATE = 12.0
HOUSEHOLD_CONSUMPTION_RATE = 1.0 # Water consumed from Overhead Tank per second

# --- City Water Supply Timing ---
CITY_SUPPLY_START_HOUR = 10
CITY_SUPPLY_END_HOUR = 15
CITY_SUPPLY_FLOW_RATE = 15.0 # Liters per second when supply is on

# --- Peak Electricity Hours ---
PEAK_HOUR_START = time(18, 30) # 6:30 PM
PEAK_HOUR_END = time(22, 30)   # 10:30 PM

# --- Electricity Meter Schedule ---
GROUND_FLOOR_METER_DAYS = range(1, 16) # 1st to 15th

# --- Simulation Settings ---
SIMULATION_INTERVAL_SECONDS = 1 # How often the simulation state updates in real-time seconds
STATE_UPDATE_INTERVAL = 1 # How often the Streamlit app refreshes in seconds

# --- Logging ---
LOG_LEVEL = "INFO"

# --- GUI ---
APP_TITLE = "Water Pump Automation System"

print(f"Database will be stored at: {DATABASE_PATH}")

