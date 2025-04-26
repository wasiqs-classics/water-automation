# src/sensors.py
"""
Simulates sensor readings for water levels and pump pressure.
Manages the state of the water tanks based on simulated flows.
"""
import random
import datetime
from typing import Dict, Optional

from config import (
    MAIN_LINE_TANK_CAPACITY, UNDERGROUND_TANK_CAPACITY, OVERHEAD_TANK_CAPACITY,
    CITY_SUPPLY_START_HOUR, CITY_SUPPLY_END_HOUR, CITY_SUPPLY_FLOW_RATE,
    P1_FLOW_RATE, P2_FLOW_RATE, P3_FLOW_RATE, HOUSEHOLD_CONSUMPTION_RATE,
    SIMULATION_INTERVAL_SECONDS
)

class Tank:
    """Represents a water tank with simulated level."""
    def __init__(self, name: str, capacity: float, initial_level_pct: float = 50.0):
        self.name = name
        self.capacity = capacity
        self._current_volume = (initial_level_pct / 100.0) * capacity
        self.level_pct = initial_level_pct # Keep track of percentage too

    def get_level_percentage(self) -> float:
        """Returns the current water level as a percentage."""
        self.level_pct = (self._current_volume / self.capacity) * 100.0
        return max(0.0, min(100.0, self.level_pct)) # Clamp between 0 and 100

    def add_water(self, volume: float) -> float:
        """Adds water to the tank, returns overflow volume."""
        potential_volume = self._current_volume + volume
        overflow = max(0.0, potential_volume - self.capacity)
        self._current_volume = min(self.capacity, potential_volume)
        self.get_level_percentage() # Update percentage
        return overflow

    def remove_water(self, volume: float) -> float:
        """Removes water from the tank, returns actual volume removed."""
        volume_to_remove = min(volume, self._current_volume)
        self._current_volume -= volume_to_remove
        self.get_level_percentage() # Update percentage
        return volume_to_remove

# --- Global Tank States (Simulation) ---
# Initialize tanks - these will be managed by the simulation update function
tanks: Dict[str, Tank] = {
    "main_line": Tank("Main Line Tank", MAIN_LINE_TANK_CAPACITY, initial_level_pct=20.0),
    "underground": Tank("Underground Tank", UNDERGROUND_TANK_CAPACITY, initial_level_pct=30.0),
    "overhead": Tank("Overhead Tank", OVERHEAD_TANK_CAPACITY, initial_level_pct=50.0),
}

def update_tank_levels(pump_states: Dict[str, bool], current_time: datetime.datetime) -> None:
    """
    Updates the simulated water levels in the tanks based on pump activity,
    city supply, and consumption. Called periodically.
    """
    global tanks
    dt = SIMULATION_INTERVAL_SECONDS # Time step for simulation

    # 1. City Supply to Main Line Tank
    hour = current_time.hour
    if CITY_SUPPLY_START_HOUR <= hour < CITY_SUPPLY_END_HOUR:
        # Add some randomness to simulate variable flow
        flow_variation = random.uniform(0.8, 1.2)
        inflow = CITY_SUPPLY_FLOW_RATE * flow_variation * dt
        tanks["main_line"].add_water(inflow)
        # print(f"Debug: City supply adding {inflow:.2f}L") # DEBUG

    # 2. Pump P1: Main Line -> Underground
    if pump_states.get("P1", False):
        volume_drawn = tanks["main_line"].remove_water(P1_FLOW_RATE * dt)
        tanks["underground"].add_water(volume_drawn)
        # print(f"Debug: P1 moved {volume_drawn:.2f}L") # DEBUG

    # 3. Pump P2: Boring Well -> Underground (Assume infinite well supply for simplicity)
    if pump_states.get("P2", False):
        tanks["underground"].add_water(P2_FLOW_RATE * dt)
        # print(f"Debug: P2 added {P2_FLOW_RATE * dt:.2f}L") # DEBUG


    # 4. Pump P3: Underground -> Overhead
    if pump_states.get("P3", False):
        volume_drawn = tanks["underground"].remove_water(P3_FLOW_RATE * dt)
        tanks["overhead"].add_water(volume_drawn)
        # print(f"Debug: P3 moved {volume_drawn:.2f}L") # DEBUG

    # 5. Household Consumption from Overhead Tank
    consumption = HOUSEHOLD_CONSUMPTION_RATE * dt
    tanks["overhead"].remove_water(consumption)
    # print(f"Debug: Consumption removed {consumption:.2f}L") # DEBUG

    # 6. Optional: Simulate very slow natural decrease (e.g., evaporation) - negligible here

def get_current_water_levels() -> Dict[str, float]:
    """Returns the current simulated water levels for all tanks."""
    return {name: tank.get_level_percentage() for name, tank in tanks.items()}

def check_pump_pressure(pump_id: str) -> bool:
    """
    Simulates checking inlet/outlet pressure for a pump.
    Returns True if pressure is OK, False if pressure is zero (simulated fault).
    Introduces a small chance of a zero pressure fault for testing.
    """
    # Simulate a rare pressure fault (e.g., 1 in 1000 checks)
    if random.randint(1, 1000) == 1:
        print(f"Debug: Simulated zero pressure for {pump_id}") # DEBUG
        return False
    return True

def reset_simulation(initial_levels: Optional[Dict[str, float]] = None) -> None:
    """Resets tank levels to initial or specified percentages."""
    global tanks
    default_levels = {
        "main_line": 20.0,
        "underground": 30.0,
        "overhead": 50.0,
    }
    levels_to_set = initial_levels if initial_levels else default_levels
    tanks["main_line"] = Tank("Main Line Tank", MAIN_LINE_TANK_CAPACITY, levels_to_set["main_line"])
    tanks["underground"] = Tank("Underground Tank", UNDERGROUND_TANK_CAPACITY, levels_to_set["underground"])
    tanks["overhead"] = Tank("Overhead Tank", OVERHEAD_TANK_CAPACITY, levels_to_set["overhead"])
    print("Simulation tanks reset.")


# Example usage (for testing module directly)
if __name__ == "__main__":
    print("Initial Levels:", get_current_water_levels())
    pump_states_test = {"P1": True, "P2": False, "P3": False}
    now = datetime.datetime.now()
    update_tank_levels(pump_states_test, now)
    print("Levels after 1 step (P1 ON):", get_current_water_levels())
    print("Pressure Check P1:", check_pump_pressure("P1"))
    reset_simulation()
    print("Levels after reset:", get_current_water_levels())
