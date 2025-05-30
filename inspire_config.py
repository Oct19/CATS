# inspire_config.py

# Serial port settings
SERIAL_PORT = 'COM4'  # Replace with your actual serial port
BAUD_RATE = 921600    # Replace with your actual baud rate

# Actuator IDs (list of integers)
# Example for two actuators with IDs 1 and 2
ACTUATOR_IDS = [3, 4,5]
# Example for six actuators
# ACTUATOR_IDS = [1, 2, 3, 4, 5, 6]

# Logging settings
LOG_DIRECTORY = 'experiments/inspire'
LOG_FILE_PREFIX = 'actuator_data'
LOG_INTERVAL_SECONDS = 0.1  # Interval for logging data (e.g., 10 times per second)

# Control parameters (optional, can be expanded)
DEFAULT_TARGET_SPEED = 100 # Example default speed
MAX_POSITION = 2000 # Example maximum position from inspire_hand.py
MIN_POSITION = 0   # Example minimum position from inspire_hand.py (or 0 if preferred)

# Register mapping (can be imported or defined here if different from inspire_LASF.py)
# This is based on inspire_LASF.py's regdict
REG_DICT = {
    'ID'              : 0x16,
    'baudrate'        : 0x17,
    'clearErrors'     : 0x18,
    'emergencyStop'   : 0x19,
    'suspend'         : 0x1A,
    'restorePar'      : 0x1B,
    'save'            : 0x1C,
    'authority'       : 0x1D,
    'forceAct'        : 0x1E,
    'warmUpSta'       : 0x1F,
    'overCurproSet'   : 0X20,
    'travelLimit'     : 0x23,
    'controlModel'    : 0x25,   # 0x00 for position, 0x02 for speed, 0x03 for force
    'outputVol'       : 0x26,
    'targetValue'     : 0x27,   # Force target in force mode
    'targetSpeed'     : 0x28,   # Speed target in speed mode
    'targetLocation'  : 0x29,   # Position target
    'actualLocation'  : 0x2A,
    'current'         : 0x2B,   # mA
    'actualForce'     : 0x2C,   # g
    'fOriginalValue'  : 0x2D,
    'actualTem'       : 0x2E,
    'faultCodes'      : 0x2F,
}