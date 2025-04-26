# src/pumps.py
"""
Defines the Pump class representing the state and basic operations of a pump.
"""
from enum import Enum, auto
import logging
from typing import Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PumpState(Enum):
    """Possible states for a pump."""
    OFF = auto()
    ON = auto()
    ERROR = auto()
    MANUAL_ON = auto() # State for when manually activated

class Pump:
    """Represents a single water pump."""
    def __init__(self, pump_id: str):
        self.pump_id = pump_id
        self.state: PumpState = PumpState.OFF
        self.error_message: str | None = None
        logging.info(f"Pump {self.pump_id} initialized in state {self.state.name}")

    def get_state(self) -> PumpState:
        """Returns the current state of the pump."""
        return self.state

    def set_state(self, new_state: PumpState, reason: str = "") -> None:
        """Sets the pump state, logging if it changes."""
        if self.state != new_state:
            old_state = self.state.name
            self.state = new_state
            self.error_message = reason if new_state == PumpState.ERROR else None
            logging.info(f"Pump {self.pump_id} state changed from {old_state} to {self.state.name}. Reason: {reason if reason else 'N/A'}")
        # If setting to ERROR, ensure reason is stored
        elif new_state == PumpState.ERROR and self.error_message != reason:
             self.error_message = reason
             logging.warning(f"Pump {self.pump_id} updated error reason: {reason}")


    def is_on(self) -> bool:
        """Checks if the pump is currently running (automatically or manually)."""
        return self.state in [PumpState.ON, PumpState.MANUAL_ON]

    def get_status_display(self) -> Tuple[str, str]:
        """Returns a display string and color for the UI."""
        if self.state == PumpState.ON:
            return "ON (Auto)", "green"
        elif self.state == PumpState.MANUAL_ON:
            return "ON (Manual)", "orange"
        elif self.state == PumpState.OFF:
            return "OFF", "grey"
        elif self.state == PumpState.ERROR:
            return f"ERROR ({self.error_message})", "red"
        return "Unknown", "black" # Should not happen

# Example usage (for testing module directly)
if __name__ == "__main__":
    p1 = Pump("P1")
    print(f"P1 initial state: {p1.get_state().name}")
    p1.set_state(PumpState.ON, reason="Low underground tank")
    print(f"P1 state after set ON: {p1.get_state().name}")
    print(f"P1 is on: {p1.is_on()}")
    p1.set_state(PumpState.ERROR, reason="Zero Pressure")
    print(f"P1 state after error: {p1.get_state().name}")
    print(f"P1 error message: {p1.error_message}")
    print(f"P1 is on: {p1.is_on()}")
    display_text, color = p1.get_status_display()
    print(f"P1 display: {display_text}, Color: {color}")
