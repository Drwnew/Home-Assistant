"""Platform for light integration."""
from __future__ import annotations
from typing import Any
from .const import DOMAIN
from homeassistant.components.light import (LightEntity)
    
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    hub = hass.data[DOMAIN][config_entry.entry_id]
    device = hub.devices[1]
    for i in range(device.count_of_coils):
        light = ModbusSwitch(device, i, f"_{str(i)}")
        device.switches.append(light)
    if device:
        async_add_entities(device.switches)


class ModbusSwitch(LightEntity):

    should_poll = True

    @property
    def device_info(self):
        """Information about this entity/device."""
        """Данная функция должна быть определена в каком-либо классе, унаследованном от
        LightEntity и им подобных"""

        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    def __init__(self, device, coil: int, name="") -> None:
        self._switcher = device.modbus_switcher
        self._state = None
        self._device = device
        self._attr_unique_id = f"{self._device.name}_{name}"
        self._attr_name = f"{self._device.name}_{name}"
        self._coil = coil

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        self._switcher.turn_on(self._coil)
        self._state = True

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._switcher.turn_off(self._coil)
        self._state = False

    def update(self) -> None:
        self._state = self._switcher.is_on(self._coil)

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available"""
        return self._switcher.available

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)

