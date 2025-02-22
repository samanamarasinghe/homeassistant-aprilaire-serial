import logging
import asyncio
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import POWER_WATT, ENERGY_KILO_WATT_HOUR
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_registry import async_get_registry

from .const import DOMAIN, REGISTER_COUNT, SCAN_INTERVAL
from .veris_modbus_interface import VerisModbusInterface

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Veris Branch Power Monitor sensors from a config entry."""
    modbus_interface = hass.data[DOMAIN].get("modbus_interface")

    if not modbus_interface:
        port = entry.data.get("port")
        baudrate = entry.data.get("baudrate")
        slave_id = entry.data.get("slave_id")

        modbus_interface = VerisModbusInterface(port, baudrate, slave_id)
        await modbus_interface.connect()

        hass.data[DOMAIN]["modbus_interface"] = modbus_interface

    # Set up data coordinator
    coordinator = VerisPowerCoordinator(hass, modbus_interface)
    await coordinator.async_config_entry_first_refresh()

    # Create sensors: One for each circuit + total power sensor
    entities = [
        VerisPowerSensor(coordinator, circuit_id)
        for circuit_id in range(1, REGISTER_COUNT + 1)
    ]
    entities.append(VerisTotalPowerSensor(coordinator))
    entities.append(VerisEnergySensor(coordinator))  # Add energy consumption sensor

    async_add_entities(entities, update_before_add=True)

class VerisPowerCoordinator(DataUpdateCoordinator):
    """Handles fetching data asynchronously for the Veris Branch Power Monitor."""
    
    def __init__(self, hass, modbus_interface):
        """Initialize the data coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Veris Power Monitor",
            update_interval=asyncio.timedelta(seconds=SCAN_INTERVAL),
        )
        self.modbus_interface = modbus_interface

    async def _async_update_data(self):
        """Fetch new power data from Modbus."""
        data = await self.modbus_interface.read_power_data()
        if data is None:
            _LOGGER.warning("Failed to fetch power data.")
            return {}
        
        power_values, total_power = data
        return {
            "circuits": power_values,
            "total_power": total_power,
        }

class VerisPowerSensor(CoordinatorEntity, SensorEntity):
    """Represents a sensor for an individual circuit in the Veris Branch Power Monitor."""

    def __init__(self, coordinator, circuit_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.circuit_id = circuit_id
        self._attr_name = f"Veris Circuit {circuit_id}"
        self._attr_unique_id = f"veris_circuit_{circuit_id}"
        self._attr_native_unit_of_measurement = POWER_WATT
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"  # Real-time measurement
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Optional

    @property
    def native_value(self):
        """Return the latest power reading for this circuit."""
        return self.coordinator.data.get("circuits", [0] * REGISTER_COUNT)[self.circuit_id - 1]

class VerisTotalPowerSensor(CoordinatorEntity, SensorEntity):
    """Represents a sensor for total power usage."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Veris Total Power"
        self._attr_unique_id = "veris_total_power"
        self._attr_native_unit_of_measurement = POWER_WATT
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"

    @property
    def native_value(self):
        """Return the latest total power reading."""
        return self.coordinator.data.get("total_power", 0)

class VerisEnergySensor(CoordinatorEntity, SensorEntity):
    """Represents an energy consumption sensor for integration with Home Assistant Energy Management."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Veris Energy Consumption"
        self._attr_unique_id = "veris_energy_consumption"
        self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
        self._attr_device_class = "energy"
        self._attr_state_class = "total_increasing"

    @property
    def native_value(self):
        """Return the total energy consumption based on power over time."""
        total_power = self.coordinator.data.get("total_power", 0)
        return (total_power / 1000) * (SCAN_INTERVAL / 3600)  # Convert W to kWh
