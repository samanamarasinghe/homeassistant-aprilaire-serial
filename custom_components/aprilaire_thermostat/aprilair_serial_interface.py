import serial
import time

# Initialize the serial connection
def initialize_serial_connection():
    try:
        ser = serial.Serial(
            port='/dev/ttyUSB0',          # Serial port path
            baudrate=9600,                # Baud rate as per Aprilaire 8811 specs
            bytesize=serial.EIGHTBITS,    # 8 data bits
            parity=serial.PARITY_NONE,    # No parity
            stopbits=serial.STOPBITS_ONE, # 1 stop bit
            timeout=1,                    # Read timeout of 1 second
            xonxoff=False,                # Disable software flow control
            rtscts=True                   # Enable hardware flow control (RTS/CTS)
        )
        print("Serial connection established.")
        return ser
    except serial.SerialException as e:
        print(f"Failed to initialize serial connection: {e}")
        return None

# Read and display data from the serial port
def read_serial_data(ser):
    while True:
        try:
            response = ser.read_all().decode('utf-8', errors='replace').strip()
            if response:
                print(f"Received: {response}")
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            break

# Main program execution
if __name__ == "__main__":
    serial_connection = initialize_serial_connection()
    if serial_connection:
        read_serial_data(serial_connection)

    