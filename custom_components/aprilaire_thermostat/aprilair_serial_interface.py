
import logging
import asyncio
from serial_asyncio import open_serial_connection

from homeassistant.components.climate.const import (
    HVACMode, HVACAction
)

_LOGGER = logging.getLogger(__name__)

class AprilaireThermostatSerialInterface:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.reader = None
        self.writer = None
        self._readwrite_lock = asyncio.Lock()  # prevent read write pairs overlapping

    async def connect(self):
        """Establish a non-blocking serial connection."""
        try:
            self.reader, self.writer = await open_serial_connection(
                url=self.port, baudrate=self.baudrate
            )
            #_LOGGER.info(f"Serial connection established on {self.port}")
        except Exception as e:
            _LOGGER.error(f"Failed to connect to serial device: {e}")
            raise
    
    
    async def check_connection(self):
        """Check if the serial connection is still active."""
        if not self.writer or not self.reader:
            _LOGGER.error("No active serial connection to check")
            return False
        # FIX-THIS!!!
        return True

    async def send_command(self, command):
        """Send a command over the serial connection."""
        if not self.writer:
            _LOGGER.error("Attempted to send command without an active connection")
            return
        try:
            self.writer.write(f"{command}\r".encode('utf-8'))
            await self.writer.drain()
            _LOGGER.debug(f"Command sent: {command}")
        except Exception as e:
            _LOGGER.error(f"Error sending command '{command}': {e}")

    async def read_response(self, timeout=0.25):
        """Read the response asynchronously with a timeout and lock."""
        if not self.reader:
            _LOGGER.error("Attempted to read response without an active connection")
            return ""
        
        response = ""
        try:
            while True:
                # Wait up to 'timeout' seconds for each read operation
                data = await asyncio.wait_for(self.reader.read(50), timeout)
                if not data:
                    break
                response += data.decode('utf-8')
        except asyncio.TimeoutError:
            None
            #_LOGGER.warning("Timeout reached while reading response")
        except Exception as e:
            _LOGGER.error(f"Error reading response: {e}")

        return response.strip()
    
    async def command_response(self, command, timeout=0.25):
        async with self._readwrite_lock:  # Lock to prevent multiple concurrent reads/writes
            await self.send_command(command)
            response = await self.read_response(timeout)
        return response

    async def query_thermostats(self):
        """Query all connected thermostats."""
        response = await self.command_response("SN?#", 0.5)
        thermostats = [line for line in response.split("\r") if line.startswith("SN")]

        await asyncio.sleep(0.5)
        names = []
        for sn in thermostats:
            nm = await self.get_name(sn)
            names.append(nm)
        #_LOGGER.info(f"ASI: Thermostats found: {thermostats} named {names}")
        return (thermostats, names)

    async def get_temperature(self, sn):
        """Get the current temperature for a specific thermostat."""
        response = await self.command_response(f"{sn}T?")
        # Parse temperature from the response (assuming format is TEMP=XX.X)
        if "T=" in response:
            temp = response.split("T=")[1].replace("F","")
            #_LOGGER.info(f"ASI: Temperature for {sn}: {temp}°F")
            try:
                return float(temp)
            except:
                _LOGGER.error(f"ASI: {temp} is not a valid temprature")
        else:
            _LOGGER.error(f"ASI: For temprature got from {response}")
        _LOGGER.error(f"ASI: No temperature data received for {sn}.")
        return None
    
    async def get_name(self, sn):
        response = await self.command_response(f"{sn}NAME?")
        
        if response:
            return response[3:]  #Skip SN#
        else:
            return None
    
    def state2action(self, state):
        # the State is G?Y1?W1?Y2?W2?B+O-   ? is either + or -
        # Assuming G is for the fan, W1 for 1st stage heat (W2 for 2nd stage?)
        # Y1 is for cool (Y2?)  Not sure what B and O are (B s always seems to be + and O -)
        try:
            if state[state.find("W1")+2] == "+":
                return HVACAction.HEATING
            elif state[state.find("Y1")+2] == "+":
                return HVACAction.COOLING
            elif state[state.find("G")+1] == "+":
                return HVACAction.FAN
            else:
                return HVACAction.OFF
        except:
            _LOGGER.error(f"Could not convert {state} to action ")
            return None
        
    async def get_state(self, sn):
        response = await self.command_response(f"{sn}H?")        
        if response:
            return self.state2action(response)
        else:
            return None

    mode_convert_to = {
        HVACMode.COOL : "C",
        HVACMode.HEAT : "H",
        HVACMode.OFF : "OFF",
        HVACMode.HEAT_COOL : "A",
        HVACMode.FAN_ONLY : "OFF"  # NO Heat or Cool when Fan only
    }
    mode_convert_ret = {
        HVACMode.FAN_ONLY: "OFF",  # No Heat or Cool when Fan only First, so will not be left in mode_convert_from
        HVACMode.COOL : "COOL",
        HVACMode.HEAT : "HEAT",
        HVACMode.OFF : "OFF",
        HVACMode.HEAT_COOL: "AUTO",
    }
    mode_convert_from = {v: k for k,v in mode_convert_ret.items()}
        
    async def get_mode(self, sn):
        response = await self.command_response(f"{sn}M?")
        # Parse M=<mode>
        if "M=" in response:
            line = response.split("M=")[1]
            mode = self.mode_convert_from.get(line, None)
            if mode:
                if mode == HVACMode.OFF:  # Check if fan is on
                    response2 = await self.command_response(f"{sn}F?")
                    line2 = response2.split("F=")[1]
                    if line2 == "AUTO":
                        return mode
                    elif line2 == "ON":
                        return HVACMode.FAN_ONLY
                    else:
                        _LOGGER.error(f"ASI: Fan check got {line2} from {response2} for mode for {sn}")
                return mode
            _LOGGER.error(f"ASI: Got {line} from {response} for mode for {sn}")
        else:
            _LOGGER.error(f"ASI: no M= in {response} for mode for {sn}")
        return None
    
    async def set_mode(self, sn, inmode):
        """Set the mode for a specific thermostat."""
        mode = self.mode_convert_to.get(inmode, None)  # FAN_ONLY will set this to OFF
        if not mode:
            _LOGGER.error(f"ASI: Wrong mode {inmode} given")

        response = await self.command_response(f"{sn}M={mode}")
        if self.mode_convert_ret[inmode] in response:
            #_LOGGER.info(f"ASI: Mode updated successfully for {sn} to {inmode}.")
            None
        else:
            _LOGGER.error(f"ASI: Failed to update mode for {sn}, Got {response}.")

        # Now do the fan setup FAN_ONLY--> ON, rest --> A (Auto)
        if inmode == HVACMode.FAN_ONLY:
            response2 = await self.command_response(f"{sn}F=ON")
        else:
            response2 = await self.command_response(f"{sn}F=A")
        if "F=" not in response2:
            _LOGGER.error(f"ASI: Fan mode set {sn} for {inmode}, got back {response2}.")

    async def set_fan(self, sn, onauto):
        if onauto:
            response = await self.command_response(f"{sn}F=ON")
        else:
            response = await self.command_response(f"{sn}F=A")
        if "F=" not in response:
            _LOGGER.error(f"ASI: Fan mode set {sn} for {onauto}, got back {response}.")


    async def get_setpoint(self, sn, setpoint_type):
        """Get the current temperature for a specific thermostat."""
        if setpoint_type == HVACMode.HEAT:
            response = await self.command_response(f"{sn}SH?")
        elif setpoint_type == HVACMode.COOL:
            response = await self.command_response(f"{sn}SC?")
        else:
            _LOGGER.error(f"ASI: Invalid Setpoint type {setpoint_type}")
            return None
    
        # Parse temperature from the response (assuming format is TEMP=XX.X)
        if "SC=" in response or "SH=" in response:
            temp = response.split("=")[1].replace("F","")
            #_LOGGER.info(f"ASI: Setpoint {setpoint_type} for {sn}: {temp}°F")
            try:
                return float(temp)
            except:
                _LOGGER.error(f"ASI: {temp} connot be made a temprature")
        else:
            _LOGGER.error(f"ASI: For setpoint temprature got  {response}")
        _LOGGER.error(f"ASI: No setpoint temperature data received for {sn} ({setpoint_type}).")
        return None

    async def set_setpoint(self, sn, setpoint_type, value):
        """Set the temperature setpoint (heat or cool) for a specific thermostat."""
        if setpoint_type not in [HVACMode.HEAT,  HVACMode.COOL]:
            _LOGGER.error(f"ASI: Invalid setpoint type {setpoint_type}")
            return

        if setpoint_type == HVACMode.HEAT:
            response = await self.command_response(f"{sn}SH={int(value)}")
        elif setpoint_type == HVACMode.COOL:
            response = await self.command_response(f"{sn}SC={int(value)}")
        else:
            _LOGGER.error(f"ASI: Invalid Setpoint type {setpoint_type}")

        if str(int(value)) in response:
            #_LOGGER.info(f"ASI: Setpoint updated successfully for {sn}.")
            None
        else:
            _LOGGER.error(f"ASI: Failed to update setpoint for {sn}, got {response} ({setpoint_type}={value})")

    def close(self):
        """Close the serial connection."""
        if self.writer:
            self.writer.close()
            _LOGGER.info("Serial connection closed.")




if __name__ == "__main__":
    interface = AprilaireThermostatSerialInterface()
    thermostats = interface.query_thermostats()
    for sn in thermostats:
        interface.get_temperature(sn)
        interface.set_setpoint(sn, "SETPOINTHEAT", 72)
    interface.close()

