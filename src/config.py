"""
Confirguration constants for the Water Pump Automation System
"""

import os
from datetime import time

# Defining Database path for later use
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATABASE_PATH = os.path.join(DATA_DIR,'automation_logs.db')

# Ensure that the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Defining constants

# TANK CAPACITIES in Liters
MAIN_LINE_TANK_CAPACITY = 1000
UNDERGROUND_TANK_CAPACITY = 5000
OVERHEAD_TANK_CAPACITY = 2000

# PUMPS OPERATIONAL THRESHOLDS (in percentages)

# for PUMP P1
P1_START_THRESHOLD_UNDERGROUND = 10.0 #Start the P1 pump if underground level is < 10%
P1_STOP_THRESHOLD_MAIN_LINE = 15.0 # Stop P1 if Main Line Levvel is < 15%
P1_REQ_MAIN_LINE_LEVEL = 15.0 # P1 requires main line level to be at least 15% or more. 
P1_MANUAL_BYPASS_MIN_UNDERGOUND = 5.0 # Allow bypass if Underground level is < 5%
P1_MANUAL_BYPASS_MIN_MAIN_LINE = 5.0 # Allow bypass if Main Line level is < 5%

# For PUMP P2
P2_START_THRESHOLD_MAIN_LINE = 5.0 # Condition to consider P2: Main line < 5%
P2_START_THRESHOLD_UNDERGROUND = 5.0 # Condition to consider P2: Underground tank < 5%
P2_START_THRESHOLD_OVERHEAD = 5.0 # Condition to consider P2: Overhead tank < 5%
P2_STOP_THRESHOLD_UNDERGROUND = 30.0 # Stop P2 if underground level is > 10%


# For PUMP P3
P3_START_THRESHOLD_OVERHEAD = 10.0 # Start P3 if Overhead < 10%
P3_REQ_UNDERGROUND_LEVEL = 10.0 #P3 requires underground level to be at least 10% or more.
P3_SIGNAL_PUMP_THRESHOLD_UNDERGROUND = 10.0 # If underground level is < 10% then signal either P1 or P2 to start pumping water to the underground tank.
P3_SIGNAL_TARGET_UNDERGROUND = 30.0 # Target level to stop P1/P2 when signaled by P3
P3_WARN_THRESHOLD_OVERHEAD = 5.0 # Warning if overhead is < 5%
P3_WARN_THRESHOLD_UNDERGROUND_LOW = 5.0 # lower limit for warning
P3_WARN_THRESHOLD_UNDERGROUND_HIGH = 10.0 # upper limit for warning
P3_STOP_THRESHOLD_UNDERGROUND= 5.0 # Stop P3 if underground level is < 5%

# Pump & Water Flow Rates (liters per second!)
P1_FLOW_RATE = 10.0
P2_FLOW_RATE = 8.0
P3_FLOW_RATE = 12.0
HOUSEHOLD_CONSUMPTION_RATE = 1.0 # Water consumption from overhead tank per second.

# CITY WATER SUPPLY SCHEDULE
CITY_SUPPLY_START_HOUR = 10 # 10 AM
CITY_SUPPLY_END_HOUR = 15 # 3 PM
CITY_SUPPLY_FLOW_RATE = 15.0 # This is the flow rate of city water supply in liters per second.

# PEAK ELECTRICITY HOURS CALCULATION
PEAK_HOUR_START = time(18, 30) # 6:30 PM
PEAH_HOUR_END = time(22, 30) # 10:30 PM

# ELECTRICITY METER SCHEDULE
GROUND_FLOOR_METER_DAYS = range(1,16) # 1st to 15th of the month

# SIMULATION SETTINGS
SIMULATION_INTERVAL_SECONDS = 1 # How often the simulation state updates in real time in seconds.
STATE_UPDATE_INTERVAL = 5 # How often Streamlit App refresh

# FOR LOGGING
LOG_LEVEL = 'INFO' # Set the logging level to INFO, DEBUG, WARNING, ERROR, CRITICAL

# GUI SETTINGS

APP_TITLE = "Water Pump Automation System"

print(f"DATABASE will be stored at {DATABASE_PATH}")