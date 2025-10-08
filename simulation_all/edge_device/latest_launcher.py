'''import os
import sys
import threading

# --- This script must be run from the project root: ~/edge_device/ ---

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Define the path to the subdirectory containing all your application logic
APP_DIRECTORY = os.path.join(PROJECT_ROOT, "edge_device")

# --- CRITICAL FIX for ModuleNotFoundError ---
# Add the application's directory to the Python Path.
# This allows all imports within your modules (like 'from modbus_master...') to work.
if APP_DIRECTORY not in sys.path:
    sys.path.insert(0, APP_DIRECTORY)

# --- Now that the path is set, we can safely import all modules ---
try:
    from edge_device import main_thread
    from edge_device.reports_handling import report_handler as rpthndler
    from edge_device import path_config  # This now imports the file with the guaranteed 'path_cfg' object
except ModuleNotFoundError as e:
    print(f"❌ ERROR: A module could not be imported. Please check the file structure.")
    print(f"Details: {e}")
    sys.exit(1)


if __name__ == "__main__":
    print("🚀 Starting Firmware...")
    print(f"Project Root: {PROJECT_ROOT}")

    # --- CRITICAL FIX for AttributeError ---
    # Set the base_path on the now-guaranteed 'path_cfg' object.
    # We set it to the APP_DIRECTORY so all internal file loading works.
    path_config.path_cfg.base_path = APP_DIRECTORY

    # Call the device initialization function from main_thread.py.
    # It will use the global path_config object to find its files.
    main_thread.readDeviceList()

    # Start the main application threads if the config file was loaded successfully
    if main_thread.install_file:
        print("✅ Devices initialized. Starting main threads...")
        rpthndler.data_handler = rpthndler.dataBank()
        
        t1 = threading.Thread(target=main_thread.getData)
        t2 = threading.Thread(target=rpthndler.data_handler.runDataLoop)

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        print("Threads finished.")
    else:
        print("Device installation file not found or failed to read. Application did not start.")
'''

'''# latest_launcher.py (Definitive Version)
import os
import sys
import threading

# --- This script should be run from your project root: ~/edge_device/ ---

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Define the absolute path to the subdirectory containing all your application logic
APP_DIRECTORY = os.path.join(PROJECT_ROOT, "edge_device")

# --- CRITICAL FIX 1: Add the app directory to Python's Path ---
# This allows all imports within your modules (like 'from modbus_master...') to work correctly.
if APP_DIRECTORY not in sys.path:
    sys.path.insert(0, APP_DIRECTORY)

# --- Now that the path is set, we can safely import all modules ---
try:
    from edge_device import main_thread
    from edge_device.reports_handling import report_handler as rpthndler
    from edge_device import path_config
except ModuleNotFoundError as e:
    print(f"❌ ERROR: A module could not be imported. Please check the file structure.")
    print(f"Details: {e}")
    sys.exit(1)


if __name__ == "__main__":
    print("🚀 Starting Firmware...")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"App Directory: {APP_DIRECTORY}")

    # --- CRITICAL FIX 2: Set the global base_path correctly ---
    # Set the base_path on the global object BEFORE any other code uses it.
    # This resolves the TypeError.
    path_config.path_cfg.base_path = APP_DIRECTORY

    # Now, call the device initialization function. It will use the
    # global path_config object to find its files correctly.
    main_thread.readDeviceList()

    # Start the main application threads if the config file was loaded successfully
    if main_thread.install_file:
        print("✅ Devices initialized. Starting main threads...")
        rpthndler.data_handler = rpthndler.dataBank()
        
        t1 = threading.Thread(target=main_thread.getData)
        t2 = threading.Thread(target=rpthndler.data_handler.runDataLoop)

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        print("Threads finished.")
    else:
        print("Device installation file not found or failed to read. Application did not start.")
'''

import os
import sys
import threading

# --- This script must be run from your project root: ~/edge_device/ ---

# Define the absolute path to the subdirectory containing all your application logic
APP_DIRECTORY = os.path.expanduser("~/edge_device/edge_device/")

# --- CRITICAL FIX 1: Change the Current Working Directory ---
# This ensures that all relative file paths inside your original
# main_thread.py (like "../submodules/...") work correctly.
try:
    print(f"Changing working directory to: {APP_DIRECTORY}")
    os.chdir(APP_DIRECTORY)
    print(f"✅ Current working directory is now: {os.getcwd()}")
except FileNotFoundError:
    print(f"❌ ERROR: Application directory not found at: {APP_DIRECTORY}")
    sys.exit(1)

# --- CRITICAL FIX 2: Add the App Directory to Python's Path ---
# This allows Python to find and import your modules.
if APP_DIRECTORY not in sys.path:
    sys.path.insert(0, APP_DIRECTORY)

# --- Now that the environment is correct, we can safely import all modules ---
try:
    import main_thread
    import reports_handling.report_handler as rpthndler
    import path_config
except ModuleNotFoundError as e:
    print(f"❌ ERROR: A module could not be imported. Please check the file structure.")
    print(f"Details: {e}")
    sys.exit(1)


if __name__ == "__main__":
    print("🚀 Starting Firmware...")
    
    # We no longer need to set the base_path, as chdir() has fixed all relative paths.
    # main_thread.py will now work as it did when run directly.
    
    # Call the device initialization function from main_thread.py
    main_thread.readDeviceList()

    # Start the main application threads if the config file was loaded successfully
    if main_thread.install_file:
        print("✅ Devices initialized. Starting main threads...")
        rpthndler.data_handler = rpthndler.dataBank()
        
        t1 = threading.Thread(target=main_thread.getData)
        t2 = threading.Thread(target=rpthndler.data_handler.runDataLoop)

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        print("Threads finished.")
    else:
        print("Device installation file not found or failed to read. Application did not start.")
