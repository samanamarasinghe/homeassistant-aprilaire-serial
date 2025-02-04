import serial
import time
import logging
import asyncio

from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)

_LOGGER = logging.getLogger(__name__)

class AprilaireThermostatSerialInterface:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,
                rtscts=False
            )
            print("Serial connection established.")
        except serial.SerialException as e:
            _LOGGER.error(f"ASI: Failed to initialize serial connection: {e}")
            self.ser = None

    def send_command(self, command):
        if not self.ser:
            _LOGGER.error("ASI: Serial connection is not available.")
            return

        try:
            self.ser.reset_input_buffer()
            self.ser.write(f"{command}\r".encode('utf-8'))
            _LOGGER.info(f"ASI: Command sent: {command}")
        except serial.SerialException as e:
            _LOGGER.error(f"ASI: Error sending command: {e}")

    async def read_response(self, timeout=5):
        if not self.ser:
            _LOGGER.info("ASI: Serial connection is not available.")
            return ""

        response_buffer = ""
        output_buffer = ""
        start_time = time.time()
        last_data_time = time.time()

        while time.time() - start_time < timeout:
            try:
                data = self.ser.read(50).decode('utf-8', errors='replace')
                if data:
                    response_buffer += data
                    last_data_time = time.time()

                    while '\r' in response_buffer:
                        line, response_buffer = response_buffer.split('\r', 1)
                        line = line.strip()
                        if line:
                            _LOGGER.info(f"ASI: Received Line: {line}")
                            output_buffer += line + "\n"
                else:
                    if time.time() - last_data_time > 0.5:
                        break

            except serial.SerialException as e:
                _LOGGER.error(f"ASI: Serial error: {e}")
                break

            await asyncio.sleep(0.05)

        return output_buffer.strip()

    async def query_thermostats(self):
        """Query all connected thermostats."""
        self.send_command("SN?#")
        response = await self.read_response()
        thermostats = [line for line in response.split("\n") if line.startswith("SN")]
        _LOGGER.info(f"ASI: Thermostats found: {thermostats}")
        return thermostats

    async def get_temperature(self, sn):
        """Get the current temperature for a specific thermostat."""
        self.send_command(f"{sn}T?")
        response = await self.read_response()
        # Parse temperature from the response (assuming format is TEMP=XX.X)
        for line in response.split("\n"):
            if line.startswith("T="):
                temp = line.split("=")[1].replace("F","")
                _LOGGER.info(f"ASI: Temperature for {sn}: {temp}°F")
                return float(temp)
            else:
                _LOGGER.error(f"ASI: For temprature got {line}")
        _LOGGER.error(f"ASI: No temperature data received for {sn}.")
        return None
    
    mode_convert_to = {
        HVACMode.AUTO : "A",
        HVACMode.COOL : "C",
        HVACMode.HEAT : "H",
        HVACMode.OFF : "OFF"
    }
    mode_convert_ret = {
        HVACMode.AUTO : "AUTO",
        HVACMode.COOL : "COOL",
        HVACMode.HEAT : "HEAT",
        HVACMode.OFF : "OFF"
    }
    mode_convert_from = {v: k for k,v in mode_convert_to.items()}

    async def get_mode(self, sn):
        self.send_command(f"{sn}M?")
        response = await self.read_response()
        # Parse temperature from the response (assuming format is TEMP=XX.X)
        for line in response.split("\n"):
            mode = mode_convert_from.get(line, None)
            if mode:
                return mode
            _LOGGER.error(f"ASI: Got {line} for mode for {sn}")
        return None
    

    async def set_mode(self, sn, inmode):
        """Set the mode for a specific thermostat."""
        mode = mode_convert_to.get(inmode, None)
        if not mode:
            _LOGGER.error(f"ASI: Wrong mode {inmode} given")

        self.send_command(f"{sn}M={mode}")

        response = await self.read_response()
        if mode_convert_ret[inmode] in response:
            _LOGGER.info(f"ASI: Mode updated successfully for {sn} to {inmode}.")
        else:
            _LOGGER.error(f"ASI: Failed to update mode for {sn}, Got {response}.")


    async def get_setpoint(self, sn, setpoint_type):
        """Get the current temperature for a specific thermostat."""
        if setpoint_type == "SETPOINTHEAT":
            self.send_command(f"{sn}SH?")
        elif setpoint_type == "SETPOINTCOOL":
            self.send_command(f"{sn}SC?")
        else:
            _LOGGER.error(f"ASI: Invalid Setpoint type {setpoint_type}")
            return None
        
        response = await self.read_response()
        # Parse temperature from the response (assuming format is TEMP=XX.X)
        for line in response.split("\n"):
            if line.startswith("SC=") or line.startswith("SH="):
                temp = line.split("=")[1].replace("F","")
                _LOGGER.info(f"ASI: Setpoint {setpoint_type} for {sn}: {temp}°F")
                return float(temp)
            else:
                _LOGGER.error(f"ASI: For setpoint temprature got {line}")
        _LOGGER.error(f"ASI: No setpoint temperature data received for {sn}.")
        return None

    async def set_setpoint(self, sn, setpoint_type, value):
        """Set the temperature setpoint (heat or cool) for a specific thermostat."""
        if setpoint_type not in ["SETPOINTHEAT", "SETPOINTCOOL"]:
            _LOGGER.error("ASI: Invalid setpoint type. Use 'SETPOINTHEAT' or 'SETPOINTCOOL'.")
            return

        if setpoint_type == "SETPOINTHEAT":
            self.send_command(f"{sn}SH={value}")
        elif setpoint_type == "SETPOINTCOOL":
            self.send_command(f"{sn}SC={value}")
        else:
            _LOGGER.error(f"ASI: Invalid Setpoint type {setpoint_type}")
        response = await self.read_response()
        if "OK" in response:
            _LOGGER.info(f"ASI: Setpoint updated successfully for {sn}.")
        else:
            _LOGGER.error(f"ASI: Failed to update setpoint for {sn}.")

    def close(self):
        if self.ser:
            self.ser.close()
            _LOGGER.info("ASI: Serial connection closed.")




if __name__ == "__main__":
    interface = AprilaireThermostatSerialInterface()
    thermostats = interface.query_thermostats()
    for sn in thermostats:
        interface.get_temperature(sn)
        interface.set_setpoint(sn, "SETPOINTHEAT", 72)
    interface.close()

