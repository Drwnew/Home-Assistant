"""The Detailed Hello World Push integration."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .hub import Hub
from .const import DOMAIN

PLATFORMS: list[str] = ["sensor", "light"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hub from config entry"""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = Hub(hass,
                                                           entry.data["device_name"],
                                                           entry.data["device_id"],
                                                           entry.data["host"],
                                                           entry.data["port"],
                                                           entry.data["slave_id"],
                                                           entry.data["count_of_coils"])
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
