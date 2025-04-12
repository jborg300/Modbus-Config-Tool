import logging
import minimalmodbus
import serial.tools.list_ports
import json
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Define constants for MODBUS RTU instrument parameters. 
PARITY = minimalmodbus.serial.PARITY_NONE
STOPBITS = 1
BYTESIZE = 8
BAUD_RATES = [2400, 4800, 9600, 19200, 38400, 115200] # Commonly used Modbus RTU BAUD RATES (This is the data transfer rate in BITS per second.)

# Menu Option Lists
MENU_OPTIONS = ["Read Register(s)", "Write Register", "Manage Presets", "Modbus Connection Settings", "Retry/Select  COM Device", "" "Exit"]
READ_REG_OPTIONS = ["Read Single Register", "Read Contiguous Registers", "Select from Read Presets", "Select from Read-Multiple Presets", "Main Menu"]
WRITE_REG_OPTIONS = ["Write Register", "Select from Write Presets", "Main Menu"]
PRESET_MENU_OPTIONS = ["Add new Read Preset", "Add new Read-Multiple Preset", "Add new Write Preset", "Modify Read Presets", "Modify Read-Multiple Presets", "Modify Write Presets", "Main Menu"]
PRESET_CHOICES = ["Read Register", "Read Multiple Contiguous Registers", "Write Register", "Main Menu"]
MB_CONNECTION_SETTINGS = ["Change Baud Rate", "Change Device ID", "Main Menu"]

current_dir = os.path.dirname(os.path.abspath(__file__))  # Get the parent directory of the current file.
PRESETS_FILEPATH = os.path.join(current_dir, "presets.json") # Define path to "presets.json" using the determined parent directory.

# ANSI Escape Codes for colors
RED = "\033[31m"
GREEN = "\033[32m"
WHITE = "\033[37m"
RESET = "\033[0m"

# Styles
BOLD = "\033[1m"
UNDERLINE = "\033[4m"

MENU_FMTCLR = f"{GREEN}{BOLD}{UNDERLINE}" # Standardized ANSI Menu Format/Coloring. Make sure to end the line with a {RESET}



def main():
    print(f"{MENU_FMTCLR}### Modbus RTU Config Tool ###{RESET}")
    com_devices, menu_items = list_serial_ports()
    selected_port = select_com_device(com_devices, menu_items)
    bypass_com = False
    baud_rate = 0
    device_ID = 0
    status_color = GREEN
    
    while True:
        #clear_console()
        if not selected_port and selected_port is None and not bypass_com:
            bypass = str(input("No COM Devices found. Bypass and run anyway? (y/n):  ").lower())
            
            if bypass == "y".lower():
                selected_port = None
                bypass_com = True
                logging.info(f"{RED}No COM device connected. Bypassed...{RESET}")   

            else:
                logging.info("Exiting...")
                return
        
        if bypass_com and selected_port:
            bypass_com = False # Reset bypass_com to False - This handles 
            
        if selected_port or bypass_com:
            if bypass_com:
                status_color = RED
                
            if not bypass_com and (baud_rate == 0 or device_ID == 0):
                baud_rate = baud_input()
                device_ID = device_id_input()
                #clear_console() # Clear Console Lines after selecting initial Baud Rate and Device ID
                status_color = GREEN # Set the Status Color as GREEN while CommsOk
                    
            print_menu_options(MENU_OPTIONS, base=1, label=f"\n{BOLD}{UNDERLINE}{status_color}Main Menu Options - {selected_port} - Baud: {baud_rate} - ID: {device_ID}{RESET}")
            mmlen: int = len(MENU_OPTIONS)
            try:
                selection = get_int_input("Option: ")
                print(f"Selection: {MENU_OPTIONS[selection - 1]}\n")

                match selection:
                    case 1:
                        read_registers(selected_port, baud_rate, device_ID)
                    case 2:
                        write_register(selected_port, baud_rate, device_ID)
                    case 3:
                        presetRegConfig_handler()
                        
                    case 4:
                        while True:
                            print_menu_options(
                                MB_CONNECTION_SETTINGS,
                                base=1,
                                label=f"{BOLD}{UNDERLINE}{GREEN}Modbus Connection Settings: - Baud: {baud_rate} - ID: {device_ID}{RESET}",
                            )
                            option = get_int_input("Option: ")
                            if option == 1:
                                baud_rate = baud_input()
                                
                            elif option == 2:
                                device_ID = device_id_input()
                                
                            elif option == len(MB_CONNECTION_SETTINGS):
                                break
                            
                            else:
                                print("Invalid Input\n")

                    case 5:
                        com_devices, menu_items = list_serial_ports()
                        
                        selected_port = select_com_device(com_devices, menu_items)

                    case mmlen:
                        print("Exit App...")
                        break
                    
            except IndexError as e:
                print(f"Invalid input. - {e}\n")
                
            except Exception as e:
                print(e)
        

def clear_console():
    """Clear the terminal screen for Windows, macOS, and Linux."""
    os.system("cls" if os.name == "nt" else "clear")         
       
     
def list_serial_ports():
    """Return a list of connected serial devices to determine COM port
    """
    ports = serial.tools.list_ports.comports()
    available_ports = [] # List of actual COM devices
    ports_menu_items = [] # List of COM devices that aligns with available_ports

    for port, desc, hwid in sorted(ports):
        available_ports.append(f"{port}")
        ports_menu_items.append(f"{port} - {desc} - {hwid}")

    return available_ports, ports_menu_items


def select_com_device(com_devices: list, display_items: list = []):
    """Handle COM port selection when the application is started.
    """
    selected_port = None
    
    # Use the display_items that include more detail about the selection.
    if len(display_items) > 0:
        menu_items = display_items
        
    if len(display_items) == 0:
        menu_items = com_devices
        
    # Handle single COM device (Auto select)1
    if com_devices and len(com_devices) == 1:
        selected_port = com_devices[0]
        logging.info(f"{GREEN}'{selected_port}'Auto selected as COM device.{RESET}")

    # Handle multiple COM devices (User selects which to use)
    elif len(com_devices) > 1:
        print("Multiple COM Ports detected...")
        print_menu_options(menu_items, base=1)
        while True:
                selection = get_int_input("Select COM Port: ") - 1
                if selection in range(0, len(com_devices)):
                    selected_port = com_devices[selection]
                    logging.info(f"'Selected {selected_port}' as COM device.\n")
                    break
                else:
                    print("Invalid Input")


    return selected_port

        
def create_virtual_device(com_port, baud_rate: int, device_id: int):
    """Create a virtual Modbus RTU instrument instance.\n
    Returns a minimalmodbus.Instrument object instance
    """
    instrument = minimalmodbus.Instrument(com_port, device_id)
    
    if instrument.serial is not None:
        # Set Serial Connection Parameters for Instrument Instance
        instrument.serial.baudrate = baud_rate
        instrument.serial.bytesize = BYTESIZE
        instrument.serial.parity = PARITY
        instrument.serial.stopbits = STOPBITS
        instrument.serial.timeout = 1  # seconds

        # Set mode to RTU - required for Modbus RTU
        instrument.mode = minimalmodbus.MODE_RTU

    return instrument


def baud_input():
    print_menu_options(BAUD_RATES, base=1, label=f"\n{MENU_FMTCLR}Select Baud Rate(Bits per second) for device connection: (The Modbus Device Datasheet will provide the default Baud Rate) {RESET}")
    
    while True:
        selection = get_int_input(("Option: ")) - 1
        if selection in range(0, len(BAUD_RATES)): # 0 Based range check for list index
            print(f"Selected: {BAUD_RATES[selection]}")
            return BAUD_RATES[selection]

    
def device_id_input():
    while True:
        selection = get_int_input("\nDevice ID(1-254): ")
        if selection in range(1, 255):
            return selection


def print_menu_options(display_list: list, base: int = 0, label: str =""):
    """Helper function for printing enumerated Console Menus"""
    if label:
        print(f"{label}")
    
    if display_list:
        for i, option in enumerate(display_list, start=base):
            print(f"{i}: {option}")
    
       
def read_registers(com_port, baud_rate: int, device_ID: int):
    baud = baud_rate
    device_id = device_ID
    
    if not com_port:
        print(f"{RED}Bypass mode active. No COM device to read from. Returning to Main Menu{RESET}")
        return
    
    read_instrument = create_virtual_device(com_port, baud, device_id)  # Create a minimal modbus Instrument instance

    try:
        while True:
            print_menu_options(READ_REG_OPTIONS, base = 1, label=f"\n{BOLD}{UNDERLINE}{GREEN}Read Register Options - Baud: {baud}, ID: {device_id}{RESET}") # Print Read Options 1 base
            read_type = get_int_input("Read Type: ")
            r_menuLen = len(READ_REG_OPTIONS)
            print(f"Selection: {READ_REG_OPTIONS[read_type - 1]}\n")
            if read_type in range(1, len(READ_REG_OPTIONS)):

                # Load Necessary JSON Read Presets for seleciton / use 
                if read_type in (3, 4):
                    json_preset_data = load_json(PRESETS_FILEPATH)
                    
                    if read_type == 3:  
                        print(f"{GREEN}{BOLD}{UNDERLINE}Read Presets:{RESET}")
                        preset_choice = get_read_presets(json_preset_data) #Collect a list of presets for 'Read or Read Multiple'
                    elif read_type == 4:
                        print(f"{GREEN}{BOLD}{UNDERLINE}Read-Multiple Presets:{RESET}")
                        preset_choice = get_read_mult_presets(json_preset_data)

                    for i, preset in enumerate(preset_choice, start=1):
                        if read_type == 3:
                            print(f"{i}. {preset['name']} (type: {preset['type']}) (register: {preset['register']})") # Read Presets
                        elif read_type == 4:
                            print(f"{i}. {preset['name']} (type: {preset['type']}) (start register: {preset['start_register']}) - Count {preset['read_count']}") # Read-Multiple Presets
                            
                            
                    option = get_int_input("Option: ") - 1
                    preset_selection = preset_choice[option]
                    

                if read_type in (1, 3): # Read a single target register using either user input(1), or preset data(3)
                    if read_type == 1:
                        target_register = get_int_input("Target Register: ")
                        preset_label = "Read Single Register"
                    elif read_type == 3:
                        target_register = int(preset_selection['register'])
                        preset_label = preset_selection['name']
                    
                    # Subtract 1 from the designated start_register to account for 0 base Registers
                    read_register = read_instrument.read_register(target_register - 1, 0, 3)
                    print(f"\n{GREEN}Read Success for '{preset_label}'\n   {UNDERLINE}Register: {target_register}{RESET}\n   {GREEN}{UNDERLINE}Value: {read_register}{RESET}")
                    
                if read_type in (2, 4):  # Read Multiple contiguous registers using either user input(2), or preset data(4)
                    if read_type == 2:

                        start_register = get_int_input("Start Register: ")
                        regReadCnt = get_int_input("Number of contiguous registers to read: ")
                        preset_label = "Read Multiple Registers"
                    
                    elif read_type == 4:
                        # Populate values from the selected "Read-Multiple" preset
                        start_register = int(preset_selection['start_register'])
                        regReadCnt = int(preset_selection["read_count"])
                        preset_label = preset_selection["name"]

                    # Subtract 1 from the designated start_register to account for 0 base Registers
                    read_values = read_instrument.read_registers(start_register-1, regReadCnt, 3)

                    if read_values:
                        print(f"\n{GREEN}Read Success: - {preset_label}{RESET}")
                        for idx, reg in enumerate(read_values, start=0):
                            print(f"   {GREEN}{UNDERLINE}Register: {start_register + idx } - Value: {reg}{RESET}")

                    
            elif read_type == r_menuLen:
                # Break out of read_register loop
                break
    
    except minimalmodbus.NoResponseError:
        logging.info(f"{RED}No Response error. Verify Modbus device configuration and register values.\n{RESET}")
        
    except minimalmodbus.ModbusException as e:
        logging.info(f"{RED}Modbus error: {str(e)}\n{RESET}")
                     
    except Exception as e:  
        logging.info(f"{RED}{e}\n{RESET}")


def write_register(com_port, baud_rate, device_ID):
    baud = baud_rate
    device_id = device_ID
    
    if not com_port:
        print(f"{RED}Bypass mode active. No COM device to Write with. Returning to Main Menu{RESET}")
        return
    
    write_instrument = create_virtual_device(com_port, baud, device_id)  # Create a minimal modbus Instrument instance

    try:
        while True:
            print_menu_options(
                WRITE_REG_OPTIONS,
                base=1,
                label=f"\n{MENU_FMTCLR}Write Register Options - Baud: {baud}, ID: {device_id}{RESET}",
            )            
            write_type = get_int_input("Write Type: ")
            wr_menuLen = len(WRITE_REG_OPTIONS)

            if write_type in range(1, wr_menuLen + 1): 
                if write_type == 1:
                    target_register = get_int_input("Target Register: ")
                    write_value = get_int_input("Write Value: ")
                    write_register = write_instrument.write_register(target_register-1, write_value, 0, 16)
                    print(f"\n{GREEN}Write Success{RESET}")
                    print(f"   {GREEN}{UNDERLINE}Wrote value: '{write_value}' to Register: {target_register}{RESET}")             


                elif write_type == 2:
                    preset_data = load_json(PRESETS_FILEPATH)
                    write_presets = get_write_presets(preset_data)
                    print(f"\n{MENU_FMTCLR}Write Presets:{RESET}")
                    for i, preset in enumerate(write_presets, start=1):
                        print(f"{i}. Name: {preset['name']} (type: {preset['type']}) - Reg: {preset['register']}, Val: {preset['value']}")

                    option = get_int_input("Option: ") - 1
                    preset_selection = write_presets[option]
                    
                    preset_reg = int(preset_selection['register'])
                    preset_write_value =  int(preset_selection['value'])
                                     
                    
                    write_register = write_instrument.write_register(preset_reg-1, preset_write_value)
                    print(f"\n{GREEN}Write Success - {preset_selection['name']}{RESET}")
                    print(f"   {GREEN}{UNDERLINE}Wrote value: '{preset_write_value}' to Register: {preset_reg}{RESET}")        

                    
                elif write_type == wr_menuLen:
                    # Break out of write_register loop
                    break
                    
    
    except minimalmodbus.NoResponseError:
        logging.info(f"{RED}No Response error. Verify Modbus device configuration and register values.\n{RESET}")
        
    except minimalmodbus.ModbusException as e:
        logging.info(f"{RED}Modbus error: {str(e)}\n{RESET}")
                    
    except Exception as e:  
        logging.info(f"{RED}{e}\n{RESET}")


def save_json(file_path: str, new_data):
    with open(file_path, "w") as f:
        json.dump(new_data, f, indent=4)


def load_json(file_path):
    with open(file_path, "r") as f:
        preset_data = json.load(f)
    
    return preset_data


def get_read_presets(json_data):
    """Returns a list  the saved Read presets"""
    read_presets = []

    for r_preset in json_data["read_presets"]:
        read_presets.append(r_preset)
        
    return read_presets


def get_read_mult_presets(json_data):
    readMult_presets = []

    for rm_preset in json_data["read_multiple_presets"]:
        readMult_presets.append(rm_preset)

    return readMult_presets


def get_write_presets(json_write_data):
    write_presets = []

    for w_preset in json_write_data["write_presets"]:
        write_presets.append(w_preset)

    return write_presets


def get_int_input(prompt: str):
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
    read_presets: list[dict] = get_read_presets(json_data)
    readMult_presets: list[dict] = get_read_mult_presets(json_data)
    write_presets: list[dict] = get_write_presets(json_data)
    
    while True:
        try:
            print_menu_options(PRESET_MENU_OPTIONS, base=1, label=f"{MENU_FMTCLR}Preset Options:{RESET}")  # Display initial Menu Options for Preset Management
            preset_option = get_int_input("Option: ")
            if preset_option in range(1, len(PRESET_MENU_OPTIONS)+1):
                print(f"Selection: {PRESET_MENU_OPTIONS[preset_option-1]}\n")
        
            if preset_option not in range(1, len(PRESET_MENU_OPTIONS)+1):
                print("Invalid Input.\n")
            
            # Create a Preset using the Read(1) / Read Multiple(2) / Write(3) templates
            if preset_option in range(1, 4):
                new_preset = {} # Create a new empty preset dict
                new_preset["name"] = input("Enter preset name: ") # Specify a name for the preset
                print_menu_options(PRESET_CHOICES, base=1, label=f"{MENU_FMTCLR}Choose Preset Type:{RESET}") # Display the preset types 
                new_preset_type = preset_option
                
                # Handle creation of 'read' PRESET data
                if new_preset_type == 1:
                    new_preset['type'] = 'read'
                    new_preset["register"] = get_int_input("Enter register address to read: ")
                    preset_key = "read_presets"

                # Handle creation of 'read_multiple' PRESET data
                elif new_preset_type == 2:
                    new_preset['type'] = 'read_multiple'
                    new_preset["start_register"] = get_int_input("Start Register: ")
                    new_preset["read_count"] = get_int_input("Registers to read: ")
                    preset_key = "read_multiple_presets"

                # Handle creation of 'write' PRESET data
                elif new_preset_type == 3:
                    new_preset['type'] = 'write'
                    new_preset["register"] = get_int_input("Enter register address to write to: ")
                    new_preset["value"] = get_int_input("Enter value to write: ")
                    preset_key = "write_presets"

                # Append and save
                json_data[preset_key].append(new_preset)
                save_json(PRESETS_FILEPATH, json_data)

                print(f"{GREEN}Preset added successfully.\n{RESET}")
                # Reload the presets.json data to reflect changes
                json_data = load_json(PRESETS_FILEPATH)
                read_presets = get_read_presets(json_data)
                readMult_presets = get_read_mult_presets(json_data)
                write_presets = get_write_presets(json_data)
                
            # Modify / Delete existing Read(4) / Read Multiple(5) / Write(6) Presets
            elif preset_option in range(4, 7):
                if preset_option == 4:
                    presets_list = read_presets
                    preset_key = "read_presets"
                    
                if preset_option == 5:
                    presets_list = readMult_presets
                    preset_key = "read_multiple_presets"
                    
                if preset_option == 6:
                    presets_list = write_presets
                    preset_key = "write_presets"
                
                while True:
                
                    print_menu_options(presets_list, base=1, label=f"{MENU_FMTCLR}Saved {preset_key} - Modify:{RESET}")  
                    print(f"{len(presets_list) + 1}: Main Menu")  # Print the option to go back to the main menu
                    mm_selection = len(presets_list) + 1           # Set the value for the dynamic Main Menu option.
                    preset_selection = get_int_input("Option: ")
                    
                    if preset_selection in range(1, len(presets_list)):
                        print(f"Selection: {presets_list[preset_selection-1]}\n")
                        while True:

                            preset = presets_list[preset_selection - 1]
                            keys = list(preset.keys())
                            print(f"{MENU_FMTCLR}Modify/Remove - '{preset['name']}'{RESET}")
                            
                            # Print the Menu Options for editing the Preset
                            for idx, (k, v) in enumerate(preset.items(), start = 1):
                                print(f"{idx}: {k}: {v}")
                                
                            print(f"{len(keys) + 1}: Delete this preset") # Print the option to delete the preset    
                            option = get_int_input("Option: ")

                            if option == len(keys) + 1:
                                confirm = str(input(f"{BOLD}Are you sure you want to delete this preset? (y/n): {RESET}").lower())
                                if confirm == "y":
                                    deleted = json_data[preset_key].pop(preset_selection - 1)
                                    save_json(PRESETS_FILEPATH, json_data)
                                    print(f"{GREEN}Preset '{deleted['name']}' deleted.\n{RESET}")

                                    # Reload the presets.json data to reflect changes
                                    json_data = load_json(PRESETS_FILEPATH)
                                    read_presets = get_read_presets(json_data)
                                    readMult_presets = get_read_mult_presets(json_data)
                                    write_presets = get_write_presets(json_data)
                                else:
                                    print(f"{RED}Delete Cancelled.\n{RESET}")
                            
                            elif option in range(1, len(keys) + 1):
                                print(f"Selection: {keys[option-1]}\n")
                                
                                key_to_edit = keys[option - 1]
                                if key_to_edit != 'type':
                                    old_value = preset[key_to_edit]
                                    new_value = input(f"Enter new value for '{key_to_edit}' (current: {old_value}): ")
                                    preset[key_to_edit] = new_value
                                    json_data[preset_key][preset_selection - 1] = preset
                                    save_json(PRESETS_FILEPATH, json_data)
                                    print(f"{GREEN}Preset '{preset['name']}' updated.\n{RESET}")
                                    break
                                
                                elif key_to_edit == 'type':
                                    print(f'{RED}"type" is currently not changeable. This will be a Future enhancement{RESET}\n')
                                    
                                
                        
                            elif option not in range(1, len(keys) + 1):
                                print(f"{RED}Invalid Input.\n{RESET}")
                            
                    if preset_selection == mm_selection:
                        # Break out of preset Register handler back to Main Menu
                        break
                    
                    elif preset_selection not in range(1, mm_selection + 1):
                        print(f"{RED}Invalid Input.\n{RESET}")
                        
            
            # Back to Main Menu
            elif preset_option == len(PRESET_MENU_OPTIONS):
                # Break out of Preset Option selection to main menu
                break

        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
        



main()
        
