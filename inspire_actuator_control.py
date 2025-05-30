import serial
import time
import datetime
import os
import csv
import threading

# Import configurations and register definitions
import inspire_config as config

# Attempt to import functions from inspire_LASF.py
# Assuming inspire_LASF.py is in reference/inspire relative to this script's location
# Adjust the path if necessary, or ensure it's in PYTHONPATH
try:
    from reference.inspire import inspire_LASF
except ImportError:
    print("Error: Could not import from reference.inspire.inspire_LASF.py")
    print("Please ensure the file exists and the path is correct or add it to PYTHONPATH.")
    # Define fallback functions or raise an error if essential
    # For now, we'll assume it imports and define wrappers later or use its functions directly
    pass

ser = None
logging_active = False
log_thread = None
log_file_writer = None
log_file = None

def open_serial_port():
    """Opens the serial port using settings from inspire_config.py."""
    global ser
    try:
        # Use openSerial from inspire_LASF if available and it matches requirements
        if hasattr(inspire_LASF, 'openSerial'):
            ser = inspire_LASF.openSerial(config.SERIAL_PORT, config.BAUD_RATE)
        else:
            # Fallback or direct implementation if inspire_LASF.openSerial is not suitable/available
            ser = serial.Serial(config.SERIAL_PORT, config.BAUD_RATE, timeout=0.1)
        if ser.is_open:
            print(f"Successfully opened serial port {config.SERIAL_PORT} at {config.BAUD_RATE} baud.")
            return True
        else:
            print(f"Failed to open serial port {config.SERIAL_PORT}.")
            return False
    except serial.SerialException as e:
        print(f"Error opening serial port {config.SERIAL_PORT}: {e}")
        ser = None
        return False

def close_serial_port():
    """Closes the serial port if it is open."""
    global ser
    if ser and ser.is_open:
        ser.close()
        print(f"Closed serial port {config.SERIAL_PORT}.")

def send_command_and_parse_response(actuator_id, command_type, register_address, data_bytes=None):
    """Sends a command to the actuator and parses the response.
       This is a generic function that needs to be adapted based on the specific command structure
       and response format of the Inspire actuators, using inspire_LASF.py as a reference.

       command_type: 0x30 for read (like readState), 0x32 for write (like writeRegister)
       register_address: The starting register address.
       data_bytes: A list of data bytes for write commands.
    """
    if not ser or not ser.is_open:
        print("Serial port not open.")
        return None

    # Frame construction based on inspire_LASF.py (simplified)
    frame = [0x55, 0xAA]  # Header

    if command_type == 0x30: # Read command (similar to readState but more targeted)
        # For a targeted read, we might need a different command structure or adapt readState.
        # inspire_LASF.readState reads a general status. For specific registers, the command might differ.
        # This part needs careful implementation based on actuator's protocol for reading specific registers.
        # For now, let's assume a hypothetical read command structure or use readState if applicable.
        # This is a placeholder for a more robust read mechanism.
        print(f"Reading register {hex(register_address)} for actuator {actuator_id} - NOT FULLY IMPLEMENTED YET") 
        # Example: inspire_LASF.readRegister(ser, actuator_id, register_address, num_bytes_to_read)
        # The inspire_LASF.py doesn't have a direct readRegister for arbitrary addresses easily.
        # readState is for general status. We'll need to construct a specific read command.
        # For now, this function will focus on the write part and a conceptual read.
        
        # Simplified read based on readState structure for concept:
        cmd_data = [0x03, actuator_id, command_type, register_address & 0xFF, (register_address >> 8) & 0xFF]
        # Length byte needs to be accurate for the specific read command.
        # This is highly dependent on the protocol for reading specific registers.
        # Let's assume for now we are trying to read 2 bytes
        frame.append(len(cmd_data) -1) # Placeholder for length
        frame.extend(cmd_data[1:]) # id, command_type, register_address_low, register_address_high

    elif command_type == 0x32: # Write command (similar to writeRegister)
        if data_bytes is None:
            data_bytes = []
        # inspire_LASF.writeRegister(ser, id, add, num, val)
        # add = register_address, num = len(data_bytes)//2 (if val is pairs), val = data_bytes
        # The structure in inspire_LASF.writeRegister is:
        # bytes.append(num*2 + 3) # Frame length
        # bytes.append(id) # ID
        # bytes.append(0x32) # CMD_WR
        # bytes.append(add & 0xff) # Register address low
        # bytes.append((add >> 8) & 0xff) # Register address high
        # bytes.append(add & 0xff) # Control table index (seems to be repeated address low?)
        # for i in range(num): bytes.append(val[i])
        
        # Adapting for our generic function:
        # Assuming data_bytes are the raw bytes to write to consecutive registers starting at register_address
        payload = [actuator_id, command_type, register_address & 0xFF, (register_address >> 8) & 0xFF]
        payload.extend(data_bytes)
        frame.append(len(payload)) # Length of ID + CMD + ADDR_L + ADDR_H + DATA
        frame.extend(payload)
    else:
        print(f"Unknown command type: {hex(command_type)}")
        return None

    checksum = sum(frame[2:]) & 0xFF
    frame.append(checksum)

    try:
        ser.write(bytearray(frame))
        time.sleep(0.05)  # Wait for response, adjust as needed
        response = ser.read_all() # Read all available data

        if not response:
            # print(f"No response from actuator {actuator_id} for command {hex(command_type)} to reg {hex(register_address)}")
            return None

        # Basic response validation (header, checksum) - NEEDS TO BE IMPLEMENTED based on protocol
        # Example: if response[0] == 0x55 and response[1] == 0xAA:
        # For now, just return raw response bytes for further parsing
        # print(f"Raw response: {response.hex()}")
        return response

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
        return None
    except Exception as e:
        print(f"Error during command execution: {e}")
        return None

def set_target_position(actuator_id, position_value):
    """Sets the target position for a specific actuator."""
    # Ensure position is within bounds
    position_value = max(config.MIN_POSITION, min(config.MAX_POSITION, position_value))
    
    # Data for target position (0x29) is usually 2 bytes, LSB first
    pos_low = position_value & 0xFF
    pos_high = (position_value >> 8) & 0xFF
    data_to_write = [pos_low, pos_high]
    
    # First, set control mode to position mode (0x00) at register 0x25 if not already set
    # This might be done once at initialization or checked/set before each position command
    # For simplicity, we can call inspire_LASF.position directly if it handles mode setting.
    if hasattr(inspire_LASF, 'position'):
        print(f"Setting position for actuator {actuator_id} to {position_value} using inspire_LASF.position")
        inspire_LASF.position(ser, actuator_id, position_value)
        # inspire_LASF.position sends a complex frame that sets mode and position.
        # It doesn't return a value, and handles its own serial write/read_all.
        return True # Assuming success if no exception
    else:
        # Manual mode set + position set if inspire_LASF.position is not available
        print("Setting control mode to POSITION (0x00) for actuator {actuator_id}")
        send_command_and_parse_response(actuator_id, 0x32, config.REG_DICT['controlModel'], [0x00, 0x00]) # Assuming 2 bytes for control mode
        time.sleep(0.01)
        print(f"Setting target position for actuator {actuator_id} to {position_value}")
        response = send_command_and_parse_response(actuator_id, 0x32, config.REG_DICT['targetLocation'], data_to_write)
        return response is not None # Crude success check

def _parse_2_byte_response(response_bytes, offset=7):
    """Helper to parse a 2-byte little-endian value from response."""
    if response_bytes and len(response_bytes) >= offset + 2:
        # Assuming standard response format where data starts at an offset
        # Example from inspire_LASF.readState: value is at recv[7], recv[8], ...
        # This needs to be confirmed for specific register reads.
        value = response_bytes[offset] + (response_bytes[offset+1] << 8)
        # Handle potential signed values if necessary based on register definition
        return value
    return None

def get_actual_position(actuator_id):
    """Gets the actual position of a specific actuator."""
    # This requires a targeted read of the 'actualLocation' register (0x2A)
    # The command structure for reading specific registers needs to be precise.
    # inspire_LASF.readState reads multiple status registers, not ideal for single value.
    
    # Hypothetical targeted read command (needs verification with actuator protocol)
    # Frame: 55 AA <LEN> <ID> 31 <REG_L> <REG_H> <NUM_BYTES_TO_READ> <CHECKSUM>
    # Response: 55 AA <LEN> <ID> <CMD_ECHO> <REG_L> <REG_H> <DATA...> <CHECKSUM>
    
    # For now, this is a placeholder. The send_command_and_parse_response needs to be robust.
    print(f"Attempting to read actual position for actuator {actuator_id} (REG: {hex(config.REG_DICT['actualLocation'])})")
    
    # Constructing a read command: CMD 0x31 (hypothetical read register command)
    # Number of bytes to read for actual position (typically 2 bytes)
    bytes_to_read = 2
    read_cmd_payload = [
        actuator_id, 
        0x31,  # Hypothetical read register command, inspire_LASF uses 0x30 for general status
        config.REG_DICT['actualLocation'] & 0xFF, 
        (config.REG_DICT['actualLocation'] >> 8) & 0xFF,
        bytes_to_read # Number of registers/bytes to read
    ]
    frame = [0x55, 0xAA]
    frame.append(len(read_cmd_payload)) # Length of payload
    frame.extend(read_cmd_payload)
    checksum = sum(frame[2:]) & 0xFF
    frame.append(checksum)

    try:
        ser.write(bytearray(frame))
        time.sleep(0.05)
        response = ser.read_all()
        if response:
            # print(f"Raw position response for {actuator_id}: {response.hex()}")
            # Response parsing needs to be accurate. Assuming data starts at offset 7 for a 2-byte value.
            # Example: 55 AA LL ID CMD REG_L REG_H D0 D1 CS
            if len(response) > 8 and response[0]==0x55 and response[1]==0xAA: # Basic check
                 # Check if response ID and CMD match request
                if response[3] == actuator_id and response[4] == 0x31: # Echoed ID and CMD
                    actual_pos = response[7] + (response[8] << 8)
                    # print(f"Actuator {actuator_id} actual position: {actual_pos}")
                    return actual_pos
            return _parse_2_byte_response(response) # Fallback to generic parser
        return None
    except Exception as e:
        print(f"Error reading actual position for actuator {actuator_id}: {e}")
        return None

def get_actual_force(actuator_id):
    """Gets the actual force reading of a specific actuator."""
    # Similar to get_actual_position, requires targeted read of 'actualForce' (0x2C)
    print(f"Attempting to read actual force for actuator {actuator_id} (REG: {hex(config.REG_DICT['actualForce'])})")
    bytes_to_read = 2
    read_cmd_payload = [
        actuator_id, 
        0x31,  # Hypothetical read register command
        config.REG_DICT['actualForce'] & 0xFF, 
        (config.REG_DICT['actualForce'] >> 8) & 0xFF,
        bytes_to_read
    ]
    frame = [0x55, 0xAA]
    frame.append(len(read_cmd_payload))
    frame.extend(read_cmd_payload)
    checksum = sum(frame[2:]) & 0xFF
    frame.append(checksum)

    try:
        ser.write(bytearray(frame))
        time.sleep(0.05)
        response = ser.read_all()
        if response:
            # print(f"Raw force response for {actuator_id}: {response.hex()}")
            if len(response) > 8 and response[0]==0x55 and response[1]==0xAA: # Basic check
                if response[3] == actuator_id and response[4] == 0x31: # Echoed ID and CMD
                    actual_force = response[7] + (response[8] << 8)
                    # print(f"Actuator {actuator_id} actual force: {actual_force}")
                    return actual_force
            return _parse_2_byte_response(response)
        return None
    except Exception as e:
        print(f"Error reading actual force for actuator {actuator_id}: {e}")
        return None

# --- Logging Functions ---
def start_logging():
    """Starts the data logging process in a separate thread."""
    global logging_active, log_thread, log_file_writer, log_file
    if not os.path.exists(config.LOG_DIRECTORY):
        os.makedirs(config.LOG_DIRECTORY)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_filename = os.path.join(config.LOG_DIRECTORY, f"{config.LOG_FILE_PREFIX}_{timestamp}.csv")
    
    try:
        log_file = open(log_filename, 'w', newline='')
        header = ['timestamp']
        for act_id in config.ACTUATOR_IDS:
            header.extend([f'actuator_{act_id}_pos', f'actuator_{act_id}_force'])
        log_file_writer = csv.writer(log_file)
        log_file_writer.writerow(header)
        
        logging_active = True
        log_thread = threading.Thread(target=log_data_loop, daemon=True)
        log_thread.start()
        print(f"Logging started to {log_filename}")
    except IOError as e:
        print(f"Error opening log file {log_filename}: {e}")

def log_data_loop():
    """Periodically logs data for all configured actuators."""
    global log_file_writer
    while logging_active:
        current_time = datetime.datetime.now().isoformat()
        log_row = [current_time]
        for act_id in config.ACTUATOR_IDS:
            pos = get_actual_position(act_id)
            force = get_actual_force(act_id)
            log_row.extend([pos if pos is not None else 'N/A', 
                            force if force is not None else 'N/A'])
        if log_file_writer:
             log_file_writer.writerow(log_row)
        time.sleep(config.LOG_INTERVAL_SECONDS)

def stop_logging():
    """Stops the data logging process."""
    global logging_active, log_thread, log_file
    if logging_active:
        logging_active = False
        if log_thread and log_thread.is_alive():
            log_thread.join(timeout=2) # Wait for the thread to finish
        print("Logging stopped.")
    if log_file:
        log_file.close()
        log_file = None
        print("Log file closed.")

# --- Main Execution Example ---
def main():
    if not open_serial_port():
        return

    start_logging()

    try:
        # Example: Move actuator 1 to position 500, then actuator 2 to 1000
        if len(config.ACTUATOR_IDS) >= 1:
            act_id_1 = config.ACTUATOR_IDS[0]
            print(f"\nMoving actuator {act_id_1} to position 500...")
            set_target_position(act_id_1, 500)
            time.sleep(2) # Allow time for movement
            pos1 = get_actual_position(act_id_1)
            force1 = get_actual_force(act_id_1)
            print(f"Actuator {act_id_1} - Actual Pos: {pos1}, Actual Force: {force1}")

        if len(config.ACTUATOR_IDS) >= 2:
            act_id_2 = config.ACTUATOR_IDS[1]
            print(f"\nMoving actuator {act_id_2} to position 1000...")
            set_target_position(act_id_2, 1000)
            time.sleep(2)
            pos2 = get_actual_position(act_id_2)
            force2 = get_actual_force(act_id_2)
            print(f"Actuator {act_id_2} - Actual Pos: {pos2}, Actual Force: {force2}")
            
            print(f"\nMoving actuator {act_id_1} to position 100...")
            set_target_position(act_id_1, 100)
            time.sleep(2)
            pos1 = get_actual_position(act_id_1)
            print(f"Actuator {act_id_1} - Actual Pos: {pos1}")

        # Add more complex sequences or interactive control here
        print("\nRunning example sequence for 10 seconds...")
        time.sleep(10) # Keep logging for a bit

    except KeyboardInterrupt:
        print("\nUser interrupted. Stopping...")
    finally:
        stop_logging()
        # Optional: return actuators to a safe/home position
        # for act_id in config.ACTUATOR_IDS:
        #    set_target_position(act_id, 0) # Example: move to 0
        # time.sleep(2)
        close_serial_port()

if __name__ == "__main__":
    main()
