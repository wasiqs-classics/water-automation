# main.py
"""
Main entry point for the Water Pump Automation Streamlit application.
"""
import sys
import os

# Add the src directory to the Python path
# This allows importing modules from src/ like 'from src.gui import main_gui'
# Adjust if your project structure or execution method differs.
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now import from src
try:
    from gui import main_gui
    from database import create_tables
except ImportError as e:
     print(f"Error importing modules. Ensure '{src_path}' is accessible.")
     print(f"Original Error: {e}")
     sys.exit(1)


if __name__ == "__main__":
    print("Starting Water Pump Automation System...")
    # Ensure database tables are ready before starting the GUI
    print("Initializing database...")
    create_tables()
    print("Launching Streamlit GUI...")
    # The Streamlit app is defined and run within gui.main_gui()
    # Streamlit handles the server and execution flow.
    main_gui()

