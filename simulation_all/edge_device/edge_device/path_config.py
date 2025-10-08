import os

class pathConfig():
    base_path = ""

    def __init__(self) -> None:
        a=os.path.abspath(__file__)
        name = os.path.basename(__file__)
        self.base_path = a[0:len(a)-len(name)]

path_cfg : pathConfig

'''import os

class pathConfig_launcher:
    """A class to hold global path configurations."""
    def __init__(self):
        # The launcher will set this attribute at runtime.
        self.base_path = None

# Create a single, global instance that all other modules can import and use.
# This guarantees that 'path_cfg' always exists after import.
path_cfg_l = pathConfig_launcher()


import os

class pathConfig:
    """A simple class to hold the global base_path configuration."""
    def __init__(self):
        # This will be set by the launcher at runtime.
        self.base_path = None

# Create a single, global instance that all other modules can import and use.
# This line guarantees that 'path_cfg' always exists after this file is imported.
path_cfg = pathConfig()
'''
'''import os

class pathConfig:
    """A simple class to hold the global base_path configuration."""
    def __init__(self):
        # This will be set by main_thread.py at runtime.
        self.base_path = None

# Create a single, global instance that all other modules can import and use.
# This line is essential and fixes the AttributeError.
path_cfg = pathConfig()
'''
