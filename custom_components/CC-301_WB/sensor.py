"""Platform for sensor integration."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    hub = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    device = hub.devices[0]
    new_devices.append(ElectricMeter(device, device.electric_meter.summary_power, "summary_power"))
    new_devices.append(ElectricMeter(device, device.electric_meter.first_phase_power, "first_phase_power"))
    new_devices.append(ElectricMeter(device, device.electric_meter.second_phase_power, "second_phase_power"))
    new_devices.append(ElectricMeter(device, device.electric_meter.third_phase_power, "third_phase_power"))
    new_devices.append(ElectricMeter(device, device.electric_meter.first_phase_voltage, "first_phase_voltage"))
    new_devices.append(ElectricMeter(device, device.electric_meter.second_phase_voltage, "second_phase_voltage"))
    new_devices.append(ElectricMeter(device, device.electric_meter.third_phase_voltage, "third_phase_voltage"))

    if new_devices:
        async_add_entities(new_devices)


class ElectricMeter(Entity):
    """Representation of a Sensor."""

    should_poll = False

    def __init__(self, device, result_function, name):
        """Initialize the sensor."""
        self._device = device
        self._attr_unique_id = f"{self._device.name}_{name}"
        self._attr_name = f"{self._device.name} {name}"
        self._result_function = result_function

    @property
    def device_info(self):
        """Information about this entity/device."""

        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._result_function()

    @property
    def available(self):
        """Return True if meter is available"""
        return self._device.electric_meter.available

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        self._device.remove_callback(self.async_write_ha_state)
