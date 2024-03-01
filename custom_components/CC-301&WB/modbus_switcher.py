import logging
import threading


from pymodbus.client import ModbusTcpClient
from pymodbus.framer import ModbusRtuFramer


_LOGGER = logging.getLogger(__name__)

class ModbusSwitcher:

    def __init__(self, slave_id: int, host: str, port: str, count_of_coils: int, mutex: threading.Lock):
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._states = []
        self._client = None
        self._count_of_coils = count_of_coils
        self._available = False
        self._mutex = mutex

        for i in range(self._count_of_coils):
            self._states.append(None)

    @property
    def available(self) -> bool:
        """Return True if switcher and hub is available"""
        return self._available

    def is_on(self, coil: int) -> bool | None:
        """Return true if light is on."""
        return self._states[coil]

    async def turn_on(self, coil: int) -> None:
        self._mutex.acquire()
        self.connect()
        self._client.write_coil(coil, True, slave=self._slave_id)
        self.disconnect()
        self._mutex.release()

        self._states[coil] = True

    async def turn_off(self, coil: int) -> None:
        self._mutex.acquire()
        self.connect()
        self._client.write_coil(coil, False, slave=self._slave_id)
        self.disconnect()
        self._mutex.release()

        self._states[coil] = False

    def connect(self) -> None:
        try:
            self._client = ModbusTcpClient(self._host, self._port, framer=ModbusRtuFramer)
            self._available = True
        except Exception as exc:
            _LOGGER.error(f"ERROR: {exc} ")
            self._available = False

    def disconnect(self) -> None:
        try:
            self._client.close()
        except Exception as exc:
            _LOGGER.error(f"ERROR: {exc} ")

    def update(self) -> None:
        """Update switcher state"""
        self._mutex.acquire()
        try:
            self.connect()
            result = self._client.read_coils(0, self._count_of_coils, slave=self._slave_id)
            self.disconnect()
            for i in range(self._count_of_coils):
                self._states[i] = result.bits[i]
        except Exception as exc:
            _LOGGER.error(f"ERROR: {exc} ")
        self._mutex.release()

