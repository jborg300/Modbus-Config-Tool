import serial.tools.list_ports
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def list_serial_ports():
    """Scan Serial ports for COM devices and return a list of detected ports
    """
    ports = serial.tools.list_ports.comports()
    available_ports = []

    for port, desc, hwid in sorted(ports):
        available_ports.append(f"{port}")

    return available_ports


def select_com_device(com_devices: list):
    # Handle single COM device (Auto select)
    if com_devices and len(com_devices) == 1:
        selected_port = com_devices[0]
        logging.info(f"'{selected_port}'Auto selected as COM device.")

    # Handle multiple COM devices (User selects which to use)
    elif com_devices and len(com_devices) > 1:
        # WIP function for user selection handling
        pass

    elif len(com_devices) == 0:
        print("No COM Devices found.")
        print("Use a virtual COM Device for testing?")
        input("(y/n): ")

def main():
    logging.info("### Modbus RTU Config Tool ###")
    
    com_devices: list = list_serial_ports()
    
    select_com_device(com_devices)
        
        

main()
        
    
    