# src/gui.py
"""
Streamlit Graphical User Interface (GUI) for the Water Pump Automation System.
Displays system status, tank levels, logs, and allows manual control.
"""
import streamlit as st
import pandas as pd
import datetime
import time # For sleep

from controller import AutomationController
from database import get_recent_logs
from sensors import reset_simulation, get_current_water_levels
from config import APP_TITLE, STATE_UPDATE_INTERVAL, SIMULATION_INTERVAL_SECONDS, P1_MANUAL_BYPASS_MIN_MAIN_LINE
from pumps import PumpState

def initialize_session_state():
    """Initializes Streamlit session state variables if they don't exist."""
    if 'controller' not in st.session_state:
        st.session_state.controller = AutomationController()
        print("Initialized Controller in session state.")
    if 'last_run_time' not in st.session_state:
        # Use a slightly past time to ensure the first run executes
        st.session_state.last_run_time = datetime.datetime.now() - datetime.timedelta(seconds=STATE_UPDATE_INTERVAL + 1)
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = True # Start simulation automatically

def run_simulation_step():
    """Runs one step of the simulation if enough time has passed."""
    controller: AutomationController = st.session_state.controller
    now = datetime.datetime.now()

    # Check if simulation is running and interval has passed
    if st.session_state.simulation_running :
        # Run the control cycle - this updates pump states AND simulates water flow
        controller.run_control_cycle(now)
        st.session_state.last_run_time = now # Update last run time after execution
        print(f"Control cycle run at {now}") # DEBUG
    else:
        # If paused, still update time-based constraints like peak hours/meter
        controller._check_time_constraints(now) # Use internal method carefully
        print(f"Simulation paused. Time constraints updated at {now}") # DEBUG


def display_dashboard(controller: AutomationController):
    """Displays the main dashboard elements."""
    st.header("System Status")

    # Display general messages and warnings
    if controller.system_message:
        st.info(controller.system_message)
    if controller.warnings:
        for warning in controller.warnings:
            st.warning(warning)

    # Layout columns for tanks and pumps
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tank Levels")
        levels = get_current_water_levels() # Get the latest levels after simulation step
        st.progress(int(levels.get("main_line", 0)), text=f"Main Line: {levels.get('main_line', 0):.1f}%")
        st.progress(int(levels.get("underground", 0)), text=f"Underground: {levels.get('underground', 0):.1f}%")
        st.progress(int(levels.get("overhead", 0)), text=f"Overhead: {levels.get('overhead', 0):.1f}%")

    with col2:
        st.subheader("Pump Status")
        for pump_id, pump in controller.pumps.items():
            status_text, color = pump.get_status_display()
            st.markdown(f"**{pump_id}:** <span style='color:{color};'>{status_text}</span>", unsafe_allow_html=True)
             # Add reset button for pumps in error state
            if pump.state == PumpState.ERROR:
                 if st.button(f"Reset Error {pump_id}", key=f"reset_{pump_id}"):
                     controller.reset_pump_error(pump_id)
                     st.rerun() # Rerun immediately to reflect the change


def display_controls(controller: AutomationController):
    """Displays control buttons."""
    st.sidebar.header("Controls")

    # Simulation Control
    if st.session_state.simulation_running:
        if st.sidebar.button("Pause Simulation"):
            st.session_state.simulation_running = False
            st.rerun()
    else:
        if st.sidebar.button("Resume Simulation"):
            st.session_state.simulation_running = True
            st.rerun()

    if st.sidebar.button("Reset Simulation State"):
        reset_simulation() # Reset tank levels in sensors.py
        # Re-initialize controller to reset pump states etc.
        st.session_state.controller = AutomationController()
        st.rerun()

    st.sidebar.subheader("Manual Pump Overrides")
    # P1 Manual Control
    p1_manual_active = controller.manual_override.get("P1", False)
    label_p1 = "Deactivate P1 Manual" if p1_manual_active else "Activate P1 Manual"
    tooltip_p1 = f"Manually run P1. Requires Main Line > {P1_MANUAL_BYPASS_MIN_MAIN_LINE}%. Cannot run during peak hours."
    if st.sidebar.button(label_p1, key="manual_p1", help=tooltip_p1):
        controller.request_manual_override("P1", not p1_manual_active)
        st.rerun()

    # P2 Manual Control
    p2_manual_active = controller.manual_override.get("P2", False)
    label_p2 = "Deactivate P2 Manual" if p2_manual_active else "Activate P2 Manual"
    tooltip_p2 = "Manually run P2 (Boring Well). Cannot run during peak hours."
    if st.sidebar.button(label_p2, key="manual_p2", help=tooltip_p2):
        controller.request_manual_override("P2", not p2_manual_active)
        st.rerun()

    # Display current override status
    st.sidebar.caption(f"P1 Manual Override: {'Active' if p1_manual_active else 'Inactive'}")
    st.sidebar.caption(f"P2 Manual Override: {'Active' if p2_manual_active else 'Inactive'}")


def display_logs():
    """Displays recent logs from the database."""
    st.header("Operation Logs")
    logs = get_recent_logs(limit=100)
    if logs:
        # Convert list of Row objects to list of dicts for Pandas
        log_data = [dict(log) for log in logs]
        df = pd.DataFrame(log_data)
        # Format timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        # Format percentages
        for col in ['main_line_level_pct', 'underground_level_pct', 'overhead_level_pct']:
             if col in df.columns:
                 df[col] = df[col].map('{:.1f}%'.format, na_action='ignore')

        # Select and reorder columns for display
        display_columns = ['timestamp', 'pump_id', 'action', 'reason', 'main_line_level_pct', 'underground_level_pct', 'overhead_level_pct', 'active_meter', 'details']
        df_display = df[[col for col in display_columns if col in df.columns]] # Ensure columns exist

        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No log entries yet.")


def main_gui():
    """Sets up and runs the Streamlit application."""
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    initialize_session_state()
    controller = st.session_state.controller

    # Run simulation step logic
    run_simulation_step()

    # Display UI elements
    display_dashboard(controller)
    display_controls(controller)
    display_logs()

    # Trigger periodic rerun using time.sleep
    # Note: Streamlit reruns automatically on widget interaction.
    # This sleep ensures updates even without interaction.
    # Be cautious with sleep in Streamlit; it blocks execution.
    # A background thread might be better for complex/long-running tasks,
    # but for this simulation, periodic reruns are acceptable.
    time.sleep(STATE_UPDATE_INTERVAL)
    if st.session_state.simulation_running:
        st.rerun()

