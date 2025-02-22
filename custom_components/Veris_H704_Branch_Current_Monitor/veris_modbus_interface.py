import logging
import asyncio
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .const import DEFAULT_BAUDRATE, DEFAULT_SLAVE_ID, REGISTER_COUNT

_LOGGER = logging.getLogger(__name__)

class VerisModbusInterface:
    """Handles asynchronous Modbus communication with the Veris Branch Power Monitor."""

    def __init__(self, port="/dev/ttyUSB1", baudrate=DEFAULT_BAUDRATE, slave_id=DEFAULT_SLAVE_ID):
        """Initialize the Modbus interface."""
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.client = None
        self._lock = asyncio.Lock()  # Prevent concurrent Modbus read/writes

    async def connect(self):
        """Establish a non-blocking Modbus RTU connection."""
        _LOGGER.info(f"Connecting to Veris Branch Monitor on {self.port} with baudrate {self.baudrate}")

        self.client = AsyncModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=2
        )

        if not await self.client.connect():
            _LOGGER.error("Failed to connect to Modbus device.")
            return False

        _LOGGER.info("Modbus connection established successfully.")
        return True

    async def check_connection(self):
        """Check if the Modbus client is still connected."""
        if not self.client or not self.client.connected:
            _LOGGER.error("Modbus connection lost.")
            return False
        return True

    async def read_power_data(self):
        """Asynchronously reads power data from the Veris Branch Current Monitor."""
        if not await self.check_connection():
            return None

        power_values = []

        async with self._lock:  # Prevent concurrent Modbus reads
            try:
                # Read registers from Modbus
                for i in range(1, REGISTER_COUNT + 1):
                    response = await self.client.read_holding_registers(address=i, count=1, slave=self.slave_id)
                    
                    if response.isError():
                        _LOGGER.warning(f"Modbus read error at register {i}")
                        power_values.append(0)
                    else:
                        power_values.append(response.registers[0])

                total_power = sum(power_values)
                return power_values, total_power

            except ModbusException as e:
                _LOGGER.error(f"Modbus error: {e}")
                return None

    async def close(self):
        """Close the Modbus connection asynchronously."""
        if self.client:
            await self.client.close()
            _LOGGER.info("Modbus connection closed.")
