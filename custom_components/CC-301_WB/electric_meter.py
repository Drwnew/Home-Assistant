import logging
import struct
import threading
from typing import List
import serial
from subprocess import run
from .const import TIMEOUT

_LOGGER = logging.getLogger(__name__)


class ElectricMeter:
    """Electric Meter Gran Electro CC-301"""

    def __init__(self, device_id: str, host: str, port: str, mutex: threading.Lock) -> None:
        self._host = host
        self._port = port
        self._available = False
        self._summary_power = None
        self._first_phase_power = None
        self._second_phase_power = None
        self._third_phase_power = None
        self._first_phase_voltage = None
        self._second_phase_voltage = None
        self._third_phase_voltage = None
        self._response_length = 78
        self._device_id = device_id
        self._command = f"{device_id} 3 46 0 0 0"
        self._rounding_accuracy = 2
        self._mutex = mutex

    def summary_power(self) -> float:
        return self._summary_power

    def first_phase_power(self) -> float:
        return self._first_phase_power

    def second_phase_power(self) -> float:
        return self._second_phase_power

    def third_phase_power(self) -> float:
        return self._third_phase_power

    def first_phase_voltage(self) -> float:
        return self._first_phase_voltage

    def second_phase_voltage(self) -> float:
        return self._second_phase_voltage

    def third_phase_voltage(self) -> float:
        return self._third_phase_voltage

    @property
    def available(self) -> bool:
        """Return True if electric meter and hub is available"""
        return self._available

    def prepare_command(self) -> bytearray:
        """Calculating and adding crc"""
        numbers = []
        for el in self._command.split(" "):
            numbers.append(int(el))

        command_line = ""
        packet = bytearray()

        for num in numbers:
            packet.append(num)
            command_line += str(num) + " "

        result = run(f"'./custom_components/CC-301_WB/CRC' {command_line}", shell=True, capture_output=True)
        result = result.stdout.decode()
        packet.append(int("0x" + result[5:7], 16))
        packet.append(int("0x" + result[3:5], 16))

        return packet

    def get_data(self, packet) -> bytes:
        """Sends a request and receive a response"""
        ser = serial.serial_for_url(f"socket://{self._host}:{self._port}", timeout=TIMEOUT)

        try:
            ser.write(packet)
            response = ser.read(self._response_length)
        finally:
            ser.close()

        return response

    @staticmethod
    def unpack_data(line) -> List:
        """Сonverting response from hex to float"""
        unpacked_data = []
        index = 0
        while index + 4 < 78:
            unpacked_data.append(struct.unpack('f', line[index:index + 4])[0])
            index += 4
        return unpacked_data

    @staticmethod
    def check_crc(response) -> bool:
        """Check crc from response"""
        command_line = ""

        for num in response[:76]:
            command_line += str(num) + " "

        result = run(f"'./custom_components/CC-301_WB/CRC' {command_line}", shell=True, capture_output=True)
        result = result.stdout.decode()

        first_crc_response_byte = "0x" + result[5:7]
        second_crc_response_byte = "0x" + result[3:5]
        first_crc_check_byte = hex(response[76])
        second_crc_check_byte = hex(response[77])

        return first_crc_response_byte == first_crc_check_byte and second_crc_response_byte == second_crc_check_byte

    @staticmethod
    def check_response(response) -> bool:
        """Check success byte"""
        return response[3] == 0

    def update(self) -> None:
        """Update electric meter state"""
        try:
            prepared_command = self.prepare_command()
            response = self.get_data(prepared_command)

            if self.check_response(response) and self.check_crc(response):
                unpacked_data = self.unpack_data(response)

                self._summary_power = round(50 * unpacked_data[1], self._rounding_accuracy)
                self._first_phase_power = round(50 * unpacked_data[2], self._rounding_accuracy)
                self._second_phase_power = round(50 * unpacked_data[3], self._rounding_accuracy)
                self._third_phase_power = round(50 * unpacked_data[4], self._rounding_accuracy)
                self._first_phase_voltage = round(unpacked_data[9], self._rounding_accuracy)
                self._second_phase_voltage = round(unpacked_data[10], self._rounding_accuracy)
                self._third_phase_voltage = round(unpacked_data[11], self._rounding_accuracy)
                self._available = True
        except Exception as exc:
            _LOGGER.error(exc)
            # self._available = False

