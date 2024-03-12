"""Hub that connects several devices."""
from __future__ import annotations
import asyncio
import logging
import threading
from typing import List, Callable
from homeassistant.core import HomeAssistant
from .electric_meter import ElectricMeter
from .const import SCAN_INTERVAL, TIMEOUT
from .modbus_switcher import ModbusSwitcher

_LOGGER = logging.getLogger(__name__)

class Hub:

    def __init__(self, hass: HomeAssistant, device_name: str, device_id: str, host: str, port: str, slave_id: int, count_of_coils: int) -> None:
        self._mutex = threading.Lock()
        self._hass = hass
        self._name = f'{device_name}_{host}'
        self._id = host.lower()
        self.devices = [
            Meter(f"electric_meter_{self._id}",
                   f"{device_name}",
                  device_id,
                  host,
                  port,
                  self._mutex),

            ModbusDevice(f"modbus_switcher_{self._id}",
                         f"{device_name}",
                         slave_id,
                         host,
                         port,
                         count_of_coils,
                         self._mutex),
        ]
        self.online = True
        self._loop = asyncio.get_event_loop()
        self._loop.create_task(self.update())


    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"model": "CC-301 and modbus switcher"}

    @property
    def hub_id(self) -> str:
        """Return hub id."""
        return self._id

    async def update(self):
        while True:
            await asyncio.sleep(SCAN_INTERVAL)
            for device in self.devices:
                try:
                    self._mutex.acquire(timeout=TIMEOUT)
                    await device.update()
                    self._mutex.release()
                except Exception as exc:
                    _LOGGER.error(exc)


class Meter:
    """Device responsible for electric meter"""

    def __init__(self, hass_device_id: str, name: str, device_id: str, host: str, port: str, mutex: threading.Lock) -> None:
        self._mutex = mutex
        self._id = hass_device_id
        self._name = name
        self._electric_meter = ElectricMeter(device_id, host, port, mutex)
        self._model = "CC-301"
        self._manufacturer = "Gran Electro"
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._loop.create_task(self.update())

    @property
    def model(self) -> str:
        """Return the device model"""
        return self._model

    @property
    def manufacturer(self) -> str:
        """Return the device manufacturer"""
        return self._manufacturer

    @property
    def id(self) -> str:
        """Return id for electric meter"""
        return self._id

    @property
    def name(self) -> str:
        """Return name for electric meter"""
        return self._name

    @property
    def electric_meter(self) -> ElectricMeter:
        """Returns the object receiving and storing the state of electric meter"""
        return self._electric_meter

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when electric meter changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    async def update(self) -> None:
        """Update electric meter sensors states"""
        await self._loop.run_in_executor(None, self._electric_meter.update)
        self.publish_updates()


class ModbusDevice:

    def __init__(self, hass_device_id: str, name: str, slave_id: int, host: str, port: str, count_of_coils: int, mutex: threading.Lock) -> None:
        self._mutex = mutex
        self._id = hass_device_id
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._count_of_coils = count_of_coils
        self._name = name
        self._modbus_switcher = ModbusSwitcher(slave_id, host, port, count_of_coils, mutex)
        self._model = "WB-MR"
        self._manufacturer = "Wirenboard"
        self._switches = []
        self._callbacks = set()

    @property
    def model(self) -> str:
        """Return the device model"""
        return self._model

    @property
    def manufacturer(self) -> str:
        """Return the device manufacturer"""
        return self._manufacturer

    @property
    def modbus_switcher(self) -> ModbusSwitcher:
        """Return an object that controls the states of the switches and stores the states of the switches"""
        return self._modbus_switcher

    @property
    def name(self) -> str:
        """Returns the device name"""
        return self._name

    @property
    def id(self) -> str:
        """Returns the device id"""
        return self._id

    @property
    def switches(self) -> List:
        """Return list of modbus switches"""
        return self._switches

    @property
    def count_of_coils(self) -> int:
        """Returns the count of device coils """
        return self._count_of_coils

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when modbus switches changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    async def update(self) -> None:
        """Update modbus switches states"""
        self._modbus_switcher.update()
        for light in self._switches:
            light.async_schedule_update_ha_state(True)