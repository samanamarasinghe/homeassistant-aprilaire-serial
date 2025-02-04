import serial
import time

class AprilaireSerialInterface:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        try:
            # Initialize serial connection with proper settings
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,      # Software flow control
                rtscts=False        # Disable hardware flow control
            )
            print("Serial connection established.")
        except serial.SerialException as e:
            print(f"Failed to initialize serial connection: {e}")
            self.ser = None

    def send_command(self, command):
        """Send a command to the Aprilaire device."""
        if not self.ser:
            print("Serial connection is not available.")
            return

        try:
            self.ser.reset_input_buffer()  # Clear any residual data
            self.ser.write(f"{command}\r".encode('utf-8'))
            print(f"Command sent: {command}")
        except serial.SerialException as e:
            print(f"Error sending command: {e}")

    def read_response(self, timeout=5):
        """Read and return the response from the Aprilaire device."""
        if not self.ser:
            print("Serial connection is not available.")
            return ""

        response_buffer = ""
        output_buffer = ""
        start_time = time.time()
        last_data_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Read up to 50 bytes at a time
                data = self.ser.read(50).decode('utf-8', errors='replace')
                if data:
                    response_buffer += data
                    last_data_time = time.time()  # Reset data timer on new data

                    # Process complete lines as they are received
                    while '\r' in response_buffer:
                        line, response_buffer = response_buffer.split('\r', 1)
                        line = line.strip()
                        if line:
                            print(f"Received Line: {line}")
                            output_buffer += line + "\n"
                else:
                    # If no data arrives for 500ms, assume the response is complete
                    if time.time() - last_data_time > 0.5:
                        break

            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break

            time.sleep(0.05)

        return output_buffer.strip()

    def close(self):
        """Close the serial connection."""
        if self.ser:
            self.ser.close()
            print("Serial connection closed.")


if __name__ == "__main__":
    interface = AprilaireSerialInterface()
    interface.send_command("SN?#")
    response = interface.read_response()
    print("\nFinal Response:")
    print(response)
    interface.close()
