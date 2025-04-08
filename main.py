import logging
import minimalmodbus
import serial.tools.list_ports
import json
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define constants for MODBUS RTU instrument parameters. 
PARITY = minimalmodbus.serial.PARITY_NONE
STOPBITS = 1
BYTESIZE = 8
BAUD_RATES = [2400, 4800, 9600, 19200, 38400, 115200] # Commonly used Modbus RTU BAUD RATES (This is the data transfer rate in BITS per second.)

# Menu Option Lists
MENU_OPTIONS = ["Read Register(s)", "Write Register", "Manage Presets", "Exit"]
READ_REG_OPTIONS = ["Read Single Register", "Read Contiguous Registers", "Select from Read Presets", "Main Menu"]
WRITE_REG_OPTIONS = ["Write Register", "Select from Write Presets", "Main Menu"]
PRESET_MENU_OPTIONS = ["Add new Preset", "Modify Existing Preset", "Main Menu"]
PRESET_CHOICES = ["Read Register", "Read Multiple Contiguous Registers", "Write Register", "Main Menu"]

current_dir = os.path.dirname(os.path.abspath(__file__))  # Get the parent directory of the current file.
PRESETS_FILEPATH = os.path.join(current_dir, "presets.json") # Define path to "presets.json" using the determined parent directory.
#! TODO: Test this functionality after the script is built into an executable. Will likely need alternate handling




def main():
    logging.info("### Modbus RTU Config Tool ###")
    com_devices: list = list_serial_ports()
    selected_port = select_com_device(com_devices)
    
    # Add check for presets.json

    if selected_port:
        logging.info(f"Using {selected_port}\n")

        while True:
            print_menu_options(MENU_OPTIONS, base=1, label="Main Menu Options")

            selection = get_int_input("Option: ")
            print(f"Selection: {MENU_OPTIONS[selection - 1]}\n")

            match selection:
                case 1:
                    read_registers(selected_port)
                case 2:
                    write_register(selected_port)
                case 3:
                    presetRegConfig_handler()
                case 4:
                    print("Exit App...")
                    break



def list_serial_ports():
    """Return a list of connected serial devices to determine COM port
    """
    ports = serial.tools.list_ports.comports()
    available_ports = []

    for port, desc, hwid in sorted(ports):
        available_ports.append(f"{port}")

    return available_ports


def select_com_device(com_devices: list):
    """Handle COM port selection when the application is started."""
    # Handle single COM device (Auto select)
    if com_devices and len(com_devices) == 1:
        selected_port = com_devices[0]
        logging.info(f"'{selected_port}'Auto selected as COM device.")

    # Handle multiple COM devices (User selects which to use)
    elif com_devices and len(com_devices) > 1:
        print("Multiple COM Ports detected...")
        print_menu_options(com_devices, base = 1)
        selection = get_int_input("Select COM Port: ") - 1
        selected_port = com_devices[selection]
        logging.info(f"'Selected {selected_port}' as COM device.")

    # Handle cases where no connected COM devices are detected.
    elif not com_devices:
        selected_port = None
        print("No COM Devices found.")
        
        input("(y/n): ")

    # Handle edge cases for COM Port selection not covered above
    else:
        pass
    
    return selected_port

        
def create_virtual_device(com_port, baud_rate: int, device_id: int):
    """Create a virtual Modbus RTU instrument instance.\n
    Prompts the user for BAUD RATE and DEVICE ID.\n
    Returns a minimalmodbus.Instrument object instance
    """
    instrument = minimalmodbus.Instrument(com_port, device_id)
    
    if instrument.serial is not None:
        # Set Serial Connection Parameters for Instrument Instance
        instrument.serial.baudrate = baud_rate
        instrument.serial.bytesize = 8
        instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = 1  # seconds

        # Set mode to RTU - required for Modbus RTU
        instrument.mode = minimalmodbus.MODE_RTU

    return instrument

          
def baud_input():
    print_menu_options(BAUD_RATES, base=1, label="Select Baud Rate for device connection:")
    
    while True:
        selection = get_int_input(("Baud Rate: ")) - 1
        if selection in range(0, len(BAUD_RATES) - 1): # 0 Based range check for list index
            return BAUD_RATES[selection]

    
def device_id_input():
    while True:
        selection = get_int_input("Device ID(1-254): ")
        if selection in range(1, 255):
            return selection


def print_menu_options(display_list: list, base: int = 0, label=""):
    if label:
        print(f"{label}")
    
    if display_list:

        for i, option in enumerate(display_list, start=base):
            print(f"{i}: {option}")
    
       
def read_registers(com_port): 
    baud = baud_input()
    device_id = device_id_input()
    read_instrument = create_virtual_device(com_port, baud, device_id)  # Create a minimal modbus Instrument instance

    try:
        while True:
            print_menu_options(READ_REG_OPTIONS, base = 1, label=f"\nRead Register Options - Baud: {baud}, ID: {device_id}") # Print Read Options 1 base
            read_type = get_int_input("Read Type: ")

            if read_type in range(1, len(READ_REG_OPTIONS)):
                if read_type == 1: # Read a single target register
                    target_register = get_int_input("Target Register: ")
                    read_register = read_instrument.read_register(target_register, 0, 3)
                    print(f"{target_register}: {read_register}")
                    
                elif read_type == 2:  # Read Multiple contiguous registers
                    start_register = get_int_input("Start Register: ")
                    regReadCnt = get_int_input("Number of contiguous registers to read: ")
                    read_registers = read_instrument.read_registers(start_register, regReadCnt, 3)

                    if read_registers:
                        for reg in read_registers:
                            print(f"{start_register}: {reg}")
                            start_register += 1
                            
                            
                elif read_type == 3:
                    
                    # WIP
                    pass 
                    preset_data = load_json(PRESETS_FILEPATH)
                    read_presets = [preset for preset in preset_data["presets"] if preset["type"] in ("read", "read_multiple")] # Collect a list of presets for 'Read or Read Multiple'
                    
                    
                    print("Read Presets:")
                    for i, preset in enumerate(read_presets, start=1):
                        print(f"{i}. {preset['name']} (type: {preset['type']})")
                    
                    option = get_int_input("Option: ")

                elif read_type == 4:
                    # Break out of read_register loop
                    break
    
    except minimalmodbus.NoResponseError:
        print("No Response error. Verify Modbus device configuration and register values.")
        
    except minimalmodbus.ModbusException as e:
        print(f"Modbus error: {str(e)}")
                     
    except Exception as e:  
        print(e)


def write_register(com_port):
    baud = baud_input()
    device_id = device_id_input()
    write_instrument = create_virtual_device(com_port, baud, device_id)  # Create a minimal modbus Instrument instance

    try:
        while True:
            print_menu_options(WRITE_REG_OPTIONS, base=1, label=f"\nWrite Register Options - Baud: {baud}, ID: {device_id}")            
            write_type = get_int_input("Write Type: ")

            if write_type in range(1, len(WRITE_REG_OPTIONS) + 1):
                if write_type == 1:
                    target_register = get_int_input("Target Register: ")
                    write_value = get_int_input("Write Value: ")
                    write_register = write_instrument.write_register(target_register, write_value, 0, )
                    print(f"{target_register}: {write_register}")             


                elif write_type == 3:
                    # WIP
                    pass
                
                    preset_data = load_json(PRESETS_FILEPATH)
                    write_presets = [p for p in preset_data["presets"] if p["type"] == "write"]
                    print("Write Presets:\n")
                    for i, preset in enumerate(write_presets, start=1):
                        print(f"{i}. {preset['name']} (type: {preset['type']})")

                    option = get_int_input("Option: ")
                    

                    
                elif write_type == 4:
                    # Break out of write_register loop
                    break
                    
    
    except minimalmodbus.NoResponseError:
        print("No Response error. Verify Modbus device configuration and register values.")
        
    except minimalmodbus.ModbusException as e:
        print(f"Modbus error: {str(e)}")
                    
    except Exception as e:  
        print(e)


def save_json(file_path, new_data):
    with open(file_path, "w") as f:
        json.dump(new_data, f, indent=4)


def load_json(file_path):
    with open(file_path, "r") as f:
        preset_data = json.load(f)
    
    return preset_data


def get_int_input(prompt):
    while True:
        user_input = input(prompt)
        try:
            if user_input is not None:
                value = int(user_input)

                return value
        except ValueError:
            print("Invalid input. Please enter an integer.")


def presetRegConfig_handler():
    json_data = load_json(PRESETS_FILEPATH)
    presets_list: list[dict] = [p for p in json_data["presets"]]
    
    while True:
        print_menu_options(PRESET_MENU_OPTIONS, base=1, label="Preset Options:")  # Display initial Menu Options for Preset Management
        preset_option = get_int_input("Option: ")
        print(f"Selection: {preset_option}\n")
        
        # Create a Preset using the Read / Read Multiple / Write templates
        if preset_option == 1:
            new_preset = {} # Create a new empty preset dict
            new_preset["name"] = input("Enter preset name: ") # Specify a name for the preset
            print_menu_options(PRESET_CHOICES, base=1, label="Choose Preset Type: ") # Display the preset types 
            new_preset_type = get_int_input("Enter type (read / read_multiple / write): ") # Get selection for which preset type to create
            
            # Handle creation of 'read' PRESET data
            if new_preset_type == 1:
                new_preset['type'] = 'read'
                new_preset["register"] = get_int_input("Enter register address to read: ")

            # Handle creation of 'read_multiple' PRESET data
            elif new_preset_type == 2:
                new_preset['type'] = 'read_multiple'
                new_preset["start_register"] = get_int_input("Starting read address: ")
                new_preset["read_count"] = get_int_input("Number of registers to read: ")

            # Handle creation of 'write' PRESET data
            elif new_preset_type == 3:
                new_preset['type'] = 'write'
                new_preset["register"] = get_int_input("Enter register address to write to: ")
                new_preset["value"] = get_int_input("Enter value to write: ")
                
            else:
                print("Invalid type. Aborting.")
                return

            # Append and save
            json_data["presets"].append(new_preset)
            save_json(PRESETS_FILEPATH, json_data)

            print("Preset added successfully.\n")
            # Reload the presets.json data to reflect changes
            json_data = load_json(PRESETS_FILEPATH)
            presets_list = json_data["presets"]
            
        # Modify / Delete existing Preset
        elif preset_option == 2:
            print_menu_options(presets_list, base=1, label="Saved Presets - Modify: ")  
            print(f"{len(presets_list) + 1}: Main Menu")  # Print the option to go back to the main menu
            mm_selection = len(presets_list) + 1            # Set the value for the dynamic Main Menu option.
            preset_selection = get_int_input("Option: ")
            print(f"Selection: {preset_selection}\n")
            
            if preset_selection in range(1, len(presets_list) + 1):
                preset = presets_list[preset_selection - 1]
                keys = list(preset.keys())
                print(f"Modify/Remove - '{preset['name']} ")
                
                # Print the Menu Options for choosing which key to edit for the selected Preset
                for idx, (k, v) in enumerate(preset.items(), start = 1):
                    print(f"{idx}: {k}: {v}")
                    
                print(f"{len(keys) + 1}: Delete this preset") # Print the option to delete the preset    
                option = get_int_input("Option: ")
                print(f"Selection: {option}\n")
                
                if option in range(1, len(keys)):
                    key_to_edit = keys[option - 1]
                    old_value = preset[key_to_edit]
                    
                    new_value = input(f"Enter new value for '{key_to_edit}' (current: {old_value}): ")

                    preset[key_to_edit] = new_value
                    json_data["presets"][preset_selection - 1] = preset
                    save_json(PRESETS_FILEPATH, json_data)
                    print(f"Preset '{preset['name']}' updated.\n")
                
                
                elif option == len(keys) + 1:
                    confirm = input("Are you sure you want to delete this preset? (y/n): ").lower()
                    if confirm == 'y':
                        deleted = json_data["presets"].pop(preset_selection - 1)
                        save_json(PRESETS_FILEPATH, json_data)
                        print(f"Preset '{deleted['name']}' deleted.\n")
                        
                        # Reload the presets.json data to reflect changes
                        json_data = load_json(PRESETS_FILEPATH)
                        presets_list = json_data["presets"]
                    else:
                        print("Delete Cancelled.\n")
                    
            if preset_selection == mm_selection:
                print()
                # Break out of preset Register handler back to Main Menu
                break
            
        
        # Back to Main Menu
        elif preset_option == 3:
            print()
            # Break out of Preset Option selection to main menu
            break
    




main()
        
