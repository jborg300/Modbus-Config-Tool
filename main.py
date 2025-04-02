import logging
import minimalmodbus
import serial.tools.list_ports
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define constants for MODBUS RTU instrument parameters. 
# ###* These options can be changed, but the majority of MB RTU device connection will use these common settings. 
# ###* Will consider making these an option the user can modify.


PARITY = minimalmodbus.serial.PARITY_NONE
STOPBITS = 1
BYTESIZE = 8
BAUD_RATES = [2400, 4800, 9600, 19200, 38400, 115200] # Commonly used Modbus RTU BAUD RATES (This is the data transfer rate in BITS per second.)
MENU_OPTIONS = ["Read Register(s)", "Write Register", "Manage Presets", "Exit"]
READ_REG_OPTIONS = ["Read Single Register", "Read Contiguous Registers", "Main Menu"]
WRITE_REG_OPTIONS = ["Write Register", "Main Menu"]


def main():
    logging.info("### Modbus RTU Config Tool ###")
    com_devices: list = list_serial_ports()
    selected_port = select_com_device(com_devices)

    if selected_port:
        logging.info(f"Using {selected_port}\n")

        while True:
            print("Menu Options")
            print_menu_options(MENU_OPTIONS, base=1)

            selection = int(input("Option: ")) - 1
            print(f"Selection: {MENU_OPTIONS[selection]}\n")

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
        selection = int(input("Select COM Port: ")) - 1
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
    print_menu_options(BAUD_RATES, base=1)
    
    while True:
        selection = int(input("Baud Rate:")) - 1
        if selection in range(0, len(BAUD_RATES) - 1):
            return BAUD_RATES[selection]

    
def device_id_input():
    while True:
        selection = int(input("Device ID(1-254): "))
        if selection in range(0, 255):
            return selection


def print_menu_options(display_list: list, base: int = 0):
    if display_list:
        for i, option in enumerate(display_list, start=base):
            print(f"{i}: {option}")
    
       
def read_registers(com_port): 
    baud = baud_input()
    device_id = device_id_input()
    read_instrument = create_virtual_device(com_port, baud, device_id)  # Create a minimal modbus Instrument instance

    try:
        while True:
            print_menu_options(READ_REG_OPTIONS, base = 1) # Print Read Options 1 base
            read_type = int(input("Read Type: ")) - 1 # Subtract 1 for 0 base

            if read_type in range(0, len(READ_REG_OPTIONS) - 1):
                if read_type == 1: # Read a single target register
                    target_register = int(input("Target Register: "))
                    read_register = read_instrument.read_register(target_register, 0, 3)
                    print(f"{target_register}: {read_register}")
                    
                elif read_type == 2:  # Read Multiple contiguous registers
                    start_register = int(input("Start Register: "))
                    regReadCnt = int(input("Number of contiguous registers to read: "))
                    read_registers = read_instrument.read_registers(start_register, regReadCnt, 3)  #! TODO: Allow user to choose modbus function code 3 or 4.

                    if read_registers:
                        for reg in read_registers:
                            print(f"{start_register}: {reg}")
                            start_register += 1

                elif read_type == 3:
                    # Break out of read_register loop
                    break
                      
    except Exception as e:  
        print(e)


def write_register(com_port):
    baud = baud_input()
    device_id = device_id_input()
    write_instrument = create_virtual_device(com_port, baud, device_id)  # Create a minimal modbus Instrument instance

    try:
        while True:
            print_menu_options(WRITE_REG_OPTIONS, base = 1) # Print Write Options 1 base                
            write_type = int(input("Write Type: ")) - 1 # Subtract 1 for 0 base

            if write_type in range(0, len(WRITE_REG_OPTIONS) - 1):
                if write_type == 1:
                    target_register = int(input("Target Register: "))
                    write_value = int(input("Write Value: "))
                    write_register = write_instrument.write_register(target_register, write_value, 0, 3)  #! TODO: Allow user to choose modbus function code 3 or 4.
                    print(f"{target_register}: {write_register}")             

                elif write_type == 3:
                    # Break out of write_register loop
                    break
                    
                    
                
    except Exception as e:  
        print(e)



def presetRegConfig_handler():
    pass


main()
        
