# src/controller.py
"""
Core logic engine for the Water Pump Automation System.
Evaluates rules, controls pumps, and logs actions.
"""
import datetime
from typing import Dict, Optional

from config import (
    PEAK_HOUR_START, PEAK_HOUR_END, GROUND_FLOOR_METER_DAYS,
    P1_START_THRESHOLD_UNDERGROUND, P1_STOP_THRESHOLD_MAIN_LINE, P1_REQ_MAIN_LINE_LEVEL,
    P1_MANUAL_BYPASS_MIN_UNDERGROUND, P1_MANUAL_BYPASS_MIN_MAIN_LINE,
    P2_START_THRESHOLD_MAIN_LINE, P2_START_THRESHOLD_UNDERGROUND, P2_START_THRESHOLD_OVERHEAD,
    P2_STOP_THRESHOLD_UNDERGROUND,
    P3_START_THRESHOLD_OVERHEAD, P3_REQ_UNDERGROUND_LEVEL, P3_SIGNAL_PUMP_THRESHOLD_UNDERGROUND,
    P3_SIGNAL_TARGET_UNDERGROUND, P3_WARN_THRESHOLD_OVERHEAD, P3_WARN_THRESHOLD_UNDERGROUND_LOW,
    P3_WARN_THRESHOLD_UNDERGROUND_HIGH, P3_STOP_THRESHOLD_UNDERGROUND
)
from pumps import Pump, PumpState
from sensors import get_current_water_levels, check_pump_pressure, update_tank_levels
from database import log_pump_action
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AutomationController:
    """Manages the overall state and control logic of the pump system."""

    def __init__(self):
        self.pumps: Dict[str, Pump] = {
            "P1": Pump("P1"),
            "P2": Pump("P2"),
            "P3": Pump("P3"),
        }
        self.last_levels: Dict[str, float] = {}
        self.active_meter: str = "Ground" # Default, will be updated
        self.is_peak_hours: bool = False
        self.warnings: list[str] = [] # Store warnings for UI display
        self.system_message: Optional[str] = None # General status messages
        self.manual_override: Dict[str, bool] = {"P1": False, "P2": False} # Track manual requests
        logging.info("Automation Controller initialized.")

    def get_pump_states(self) -> Dict[str, bool]:
        """Returns a simple dictionary of which pumps are currently ON."""
        return {pid: p.is_on() for pid, p in self.pumps.items()}

    def _check_time_constraints(self, current_time: datetime.datetime) -> None:
        """Updates active meter and peak hour status."""
        # Check peak hours
        now_time = current_time.time()
        self.is_peak_hours = PEAK_HOUR_START <= now_time <= PEAK_HOUR_END

        # Check active meter
        day = current_time.day
        self.active_meter = "Ground" if day in GROUND_FLOOR_METER_DAYS else "First Floor"

        if self.is_peak_hours:
            self.system_message = f"Peak hours active ({PEAK_HOUR_START.strftime('%H:%M')} - {PEAK_HOUR_END.strftime('%H:%M')}). Automatic pumping paused."
        else:
             self.system_message = f"Active Meter: {self.active_meter}"

    def _log_action(self, pump_id: str, action: str, reason: str, details: Optional[str] = None) -> None:
        """Helper to log actions with current state."""
        log_pump_action(
            pump_id=pump_id,
            action=action,
            reason=reason,
            levels=self.last_levels,
            active_meter=self.active_meter,
            details=details
        )

    def _handle_pump_stop(self, pump_id: str, reason: str, action_type: str = 'STOP') -> None:
        """Stops a pump and logs the action."""
        pump = self.pumps[pump_id]
        if pump.is_on():
            pump.set_state(PumpState.OFF, reason=reason)
            self._log_action(pump_id, action_type, reason)

    def _handle_pump_start(self, pump_id: str, reason: str, manual: bool = False) -> bool:
        """Attempts to start a pump, checking pressure and logging."""
        pump = self.pumps[pump_id]
        if not pump.is_on(): # Only attempt to start if it's off
            if check_pump_pressure(pump_id):
                new_state = PumpState.MANUAL_ON if manual else PumpState.ON
                pump.set_state(new_state, reason=reason)
                action_type = 'MANUAL_START' if manual else 'START'
                self._log_action(pump_id, action_type, reason)
                return True
            else:
                error_reason = "Zero Pressure Detected"
                pump.set_state(PumpState.ERROR, reason=error_reason)
                self._log_action(pump_id, 'ERROR', error_reason)
                return False
        return True # Already running or successfully started

    def run_control_cycle(self, current_time: datetime.datetime) -> None:
        """Executes one cycle of the automation logic."""
        self.warnings = [] # Clear previous warnings
        self.system_message = None # Clear previous message

        # 1. Update time constraints and sensor readings
        self._check_time_constraints(current_time)
        self.last_levels = get_current_water_levels()
        ml_level = self.last_levels.get("main_line", 0.0)
        ug_level = self.last_levels.get("underground", 0.0)
        oh_level = self.last_levels.get("overhead", 0.0)

        # 2. Update tank levels based on current pump states (from previous cycle)
        # This simulates water movement between checks
        update_tank_levels(self.get_pump_states(), current_time)
        # Get updated levels after simulation step
        self.last_levels = get_current_water_levels()
        ml_level = self.last_levels.get("main_line", 0.0)
        ug_level = self.last_levels.get("underground", 0.0)
        oh_level = self.last_levels.get("overhead", 0.0)


        # --- Safety Checks and Peak Hour Stops ---
        # Stop all pumps if pressure fails during operation or if peak hours start
        for pump_id, pump in self.pumps.items():
            if pump.is_on():
                if self.is_peak_hours and pump.state != PumpState.MANUAL_ON: # Stop auto pumps during peak
                     self._handle_pump_stop(pump_id, "Peak hours started")
                elif not check_pump_pressure(pump_id):
                    error_reason = "Zero Pressure Detected during operation"
                    pump.set_state(PumpState.ERROR, reason=error_reason)
                    self._log_action(pump_id, 'ERROR', error_reason)


        # --- Manual Overrides ---
        # P1 Manual
        if self.manual_override["P1"]:
            if self.is_peak_hours:
                 self.warnings.append("P1 Manual Start ignored during peak hours.")
            elif ml_level < P1_MANUAL_BYPASS_MIN_MAIN_LINE:
                 self.warnings.append(f"P1 Manual Start failed: Main Line Tank < {P1_MANUAL_BYPASS_MIN_MAIN_LINE}%")
                 self._handle_pump_stop(pump_id, f"Manual start condition not met (Main Line < {P1_MANUAL_BYPASS_MIN_MAIN_LINE}%)")
            elif not self.pumps["P1"].is_on():
                 self._handle_pump_start("P1", "Manual Override Activated", manual=True)
            # Keep it running manually unless stopped or error
        elif self.pumps["P1"].state == PumpState.MANUAL_ON:
             # Allow manual run to continue unless explicitly stopped or error
             # Check stop conditions that might apply even to manual? e.g., pressure
             if not check_pump_pressure("P1"):
                  error_reason = "Zero Pressure Detected during manual operation"
                  self.pumps["P1"].set_state(PumpState.ERROR, reason=error_reason)
                  self._log_action("P1", 'ERROR', error_reason)


        # P2 Manual
        if self.manual_override["P2"]:
             if self.is_peak_hours:
                 self.warnings.append("P2 Manual Start ignored during peak hours.")
             elif not self.pumps["P2"].is_on():
                  self._handle_pump_start("P2", "Manual Override Activated", manual=True)
             # Keep it running manually unless stopped or error
        elif self.pumps["P2"].state == PumpState.MANUAL_ON:
             if not check_pump_pressure("P2"):
                  error_reason = "Zero Pressure Detected during manual operation"
                  self.pumps["P2"].set_state(PumpState.ERROR, reason=error_reason)
                  self._log_action("P2", 'ERROR', error_reason)


        # --- Automatic Pump Logic (only if not peak hours and no errors) ---
        if not self.is_peak_hours:
            # Pump P3 Logic (Highest Priority Consumer)
            pump3 = self.pumps["P3"]
            if pump3.state != PumpState.ERROR:
                # Conditions to STOP P3
                if pump3.is_on() and (oh_level >= P3_START_THRESHOLD_OVERHEAD + 5.0): # Stop with a buffer
                     self._handle_pump_stop("P3", f"Overhead Tank reached {oh_level:.1f}%")
                elif pump3.is_on() and ug_level < P3_STOP_THRESHOLD_UNDERGROUND:
                     self._handle_pump_stop("P3", f"Underground Tank fell below {P3_STOP_THRESHOLD_UNDERGROUND}%")
                     self.system_message = f"P3 stopped. Underground low ({ug_level:.1f}%). Requesting fill."
                     # Signal P1/P2 logic will handle the request below

                # Conditions to START P3 (if off)
                elif not pump3.is_on() and oh_level < P3_START_THRESHOLD_OVERHEAD:
                    if ug_level >= P3_REQ_UNDERGROUND_LEVEL:
                         self._handle_pump_start("P3", f"Overhead Tank < {P3_START_THRESHOLD_OVERHEAD}%")
                    else:
                         # Not enough water in UG tank, signal P1/P2 needed
                         self.system_message = f"P3 needs to start (Overhead < {P3_START_THRESHOLD_OVERHEAD}%) but Underground level ({ug_level:.1f}%) is below required {P3_REQ_UNDERGROUND_LEVEL}%."
                         # P1/P2 logic will check if they need to run based on this implicit signal

                # Warnings for P3 operation
                if pump3.is_on():
                    if oh_level < P3_WARN_THRESHOLD_OVERHEAD:
                        self.warnings.append(f"Warning: P3 running with Overhead Tank level low ({oh_level:.1f}% < {P3_WARN_THRESHOLD_OVERHEAD}%)")
                    if P3_WARN_THRESHOLD_UNDERGROUND_LOW <= ug_level < P3_WARN_THRESHOLD_UNDERGROUND_HIGH:
                         self.warnings.append(f"Warning: P3 running with Underground Tank level low ({ug_level:.1f}%)")


            # Pump P1 Logic (Primary Supply) - only if not manually controlled
            pump1 = self.pumps["P1"]
            if pump1.state not in [PumpState.ERROR, PumpState.MANUAL_ON]:
                 # Conditions to STOP P1
                 if pump1.is_on():
                     if ml_level < P1_STOP_THRESHOLD_MAIN_LINE:
                         self._handle_pump_stop("P1", f"Main Line Tank < {P1_STOP_THRESHOLD_MAIN_LINE}%")
                     elif ug_level >= P3_SIGNAL_TARGET_UNDERGROUND + 5.0: # Stop if UG tank is sufficiently full (e.g. filled after P3 request)
                         self._handle_pump_stop("P1", f"Underground Tank reached target level ({ug_level:.1f}%)")

                 # Conditions to START P1 (if off)
                 elif not pump1.is_on():
                     # Start if UG is low OR if P3 signaled for more water (UG < P3_REQ_UNDERGROUND_LEVEL)
                     needs_fill = ug_level < P1_START_THRESHOLD_UNDERGROUND or ug_level < P3_REQ_UNDERGROUND_LEVEL
                     if needs_fill and ml_level >= P1_REQ_MAIN_LINE_LEVEL:
                         self._handle_pump_start("P1", f"Underground Tank < {max(P1_START_THRESHOLD_UNDERGROUND, P3_REQ_UNDERGROUND_LEVEL)}%")
                     elif needs_fill and ml_level < P1_REQ_MAIN_LINE_LEVEL:
                          self.system_message = f"P1 cannot start: Underground needs fill ({ug_level:.1f}%) but Main Line level ({ml_level:.1f}%) is below required {P1_REQ_MAIN_LINE_LEVEL}%."


            # Pump P2 Logic (Backup Supply) - only if not manually controlled
            pump2 = self.pumps["P2"]
            if pump2.state not in [PumpState.ERROR, PumpState.MANUAL_ON]:
                 # Conditions to STOP P2
                 if pump2.is_on() and ug_level >= P2_STOP_THRESHOLD_UNDERGROUND:
                      self._handle_pump_stop("P2", f"Underground Tank reached {P2_STOP_THRESHOLD_UNDERGROUND}%")

                 # Conditions to START P2 (if off)
                 # Start if Main Line is very low AND Underground is very low AND Overhead is very low
                 # OR if P3 signaled and P1 cannot run
                 elif not pump2.is_on():
                     critical_levels = (ml_level < P2_START_THRESHOLD_MAIN_LINE and
                                       ug_level < P2_START_THRESHOLD_UNDERGROUND and
                                       oh_level < P2_START_THRESHOLD_OVERHEAD)
                     p3_needs_water_p1_cant = (ug_level < P3_REQ_UNDERGROUND_LEVEL and
                                              ml_level < P1_REQ_MAIN_LINE_LEVEL) # P1 can't fulfill P3's need

                     if critical_levels:
                           self._handle_pump_start("P2", "Critical low levels detected in all tanks")
                     elif p3_needs_water_p1_cant:
                           self._handle_pump_start("P2", f"Backup needed: P3 requires water and P1 cannot run (Main Line {ml_level:.1f}%)")


    def request_manual_override(self, pump_id: str, enable: bool) -> None:
        """Handles requests from the UI to enable/disable manual override."""
        if pump_id in self.manual_override:
            if enable and self.pumps[pump_id].state == PumpState.ERROR:
                 logging.warning(f"Cannot enable manual override for {pump_id}, pump is in ERROR state.")
                 self.warnings.append(f"Cannot manually start {pump_id} while in ERROR state.")
                 return # Don't enable override if pump is in error

            self.manual_override[pump_id] = enable
            logging.info(f"Manual override for {pump_id} set to {enable}")

            if not enable: # If disabling manual override
                pump = self.pumps[pump_id]
                if pump.state == PumpState.MANUAL_ON:
                    # Stop the pump if it was running manually
                    pump.set_state(PumpState.OFF, reason="Manual Override Disabled")
                    self._log_action(pump_id, 'MANUAL_STOP', "Manual Override Disabled")
            # If enabling, the main control loop will handle starting it if conditions allow

    def reset_pump_error(self, pump_id: str) -> None:
        """Resets the error state of a pump."""
        if pump_id in self.pumps:
            pump = self.pumps[pump_id]
            if pump.state == PumpState.ERROR:
                pump.set_state(PumpState.OFF, reason="Error Reset by User")
                self._log_action(pump_id, 'INFO', "Error Reset by User")
                logging.info(f"Error state for pump {pump_id} reset.")
            else:
                logging.warning(f"Attempted to reset error on pump {pump_id}, but it was not in error state.")
