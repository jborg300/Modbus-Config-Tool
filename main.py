import logging
import minimalmodbus
import serial.tools.list_ports
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define constants for MODBUS RTU instrument instances. 
# ###* These options can be changed, but the majority of MB RTU device connection will use these common settings. 
# ###* Will consider making these an option the user can modify.

PARITY = minimalmodbus.serial.PARITY_NONE
STOPBITS = 1
BYTESIZE = 8
BAUD_RATES = [2400, 4800, 9600, 19200, 38400, 115200] # Commonly used Modbus RTU BAUD RATES (This is the data transfer rate in BITS per second.)
MENU_OPTIONS = ["Read Register(s)", "Write Register", "Manage Presets", "Exit"]


def list_serial_ports():
    """Return a list of connected serial devices to determine COM port
    """
    ports = serial.tools.list_ports.comports()
    available_ports = []

    for port, desc, hwid in sorted(ports):
        available_ports.append(f"{port}")

    return available_ports


def select_com_device(com_devices: list):
    """Handle COM port selection when the Application is started."""
    # Handle single COM device (Auto select)
    if com_devices and len(com_devices) == 1:
        selected_port = com_devices[0]
        logging.info(f"'{selected_port}'Auto selected as COM device.")

    # Handle multiple COM devices (User selects which to use)
    elif com_devices and len(com_devices) > 1:
        print("Multiple COM Ports detected...")
        for i, comPort in enumerate(com_devices):
            print(f"{i}: {comPort}")
            
        selection = int(input("Select COM Port: "))
        selected_port = com_devices[selection]
        
        #print(selected_port)

    # Handle cases where no connected COM devices are detected.
    elif len(com_devices) == 0:
        selected_port = None
        print("No COM Devices found.")
        
        input("(y/n): ")

    # Handle edge cases for COM Port selection not covered above
    else:
        pass
    
    return selected_port
    
    
def create_virtual_device(com_port):
    """Create a virtual Modbus RTU instrument instance.\n
    Prompts the user for BAUD RATE and DEVICE ID.\n
    Returns a minimalmodbus.Instrument object instance
    """
    
    print("Baud Rate: ")
    
    for i, br in enumerate(BAUD_RATES):
        print(f"{i}: {br}")
    
    while True:
        baudInput = int(input("Baud Rate: "))
        if baudInput >= 0 and baudInput < len(BAUD_RATES):
            break

    baud = BAUD_RATES[baudInput]
    print(f"Selected Baud Rate: {baud}")
    
    while True:
        device_idInput = int(input("Device ID(2 - 255): "))
        if device_idInput in range(2, 256):
            break

    device_id = device_idInput
    print(f"Selected Device ID: {device_idInput}")
    
    return minimalmodbus.Instrument(com_port, device_id)
    

def main():
    logging.info("### Modbus RTU Config Tool ###")
    com_devices: list = list_serial_ports()
    selected_port = select_com_device(com_devices)

    if selected_port:
        logging.info(f"Using {selected_port}\n")
    
        while True:
            print("Menu Options")
            for i, option in enumerate(MENU_OPTIONS, start=1):
                print(f"{i}: {option}")
            
            selection = int(input("Option: "))
            print(f"Selection: {MENU_OPTIONS[selection-1]}\n")
            
            match selection:
                case 1:
                    read_registers()
                case 2:
                    write_register()
                case 3:
                    presetRegConfig_handler()
                case 4:
                    print("Exit App...")
                    break
                
        
            
            

        
def read_registers():
    pass 

def write_register():
    pass

def presetRegConfig_handler():
    pass


main()
        
