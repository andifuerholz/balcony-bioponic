# sensors_sht20.py
# Purpose:
# Read temperature and humidity from an SHT20 sensor over I2C
# and publish values to Arduino IoT Cloud.
#
# Published variables:
# - air_temp (°C)
# - air_humidity (% rF)

from machine import I2C
import time

SHT20_ADDR = 0x40

# Commands (no hold master)
CMD_TEMP = 0xF3
CMD_HUM  = 0xF5


class SHT20Manager:
    """
    Simple manager for a single SHT20 sensor on an I2C bus.
    Interface is compatible with the existing DS18B20Manager usage.
    """

    def __init__(self, client, i2c: I2C):
        self.client = client
        self.i2c = i2c

    # --- Low-level raw reads ----------------------------------------------

    def _read_temperature(self):
        self.i2c.writeto(SHT20_ADDR, bytes([CMD_TEMP]))
        time.sleep_ms(100)
        raw = self.i2c.readfrom(SHT20_ADDR, 2)
        val = (raw[0] << 8) | raw[1]
        val &= 0xFFFC  # mask status bits
        return -46.85 + 175.72 * val / 65536.0

    def _read_humidity(self):
        self.i2c.writeto(SHT20_ADDR, bytes([CMD_HUM]))
        time.sleep_ms(100)
        raw = self.i2c.readfrom(SHT20_ADDR, 2)
        val = (raw[0] << 8) | raw[1]
        val &= 0xFFFC  # mask status bits
        return -6.0 + 125.0 * val / 65536.0

    # --- Public API -------------------------------------------------------

    def read_and_publish_once(self):
        """
        Read temperature + humidity once and publish to the cloud.
        Also updates runtime temperature state.
        """
        try:
            temp = round(self._read_temperature(), 2)
            hum  = round(self._read_humidity(), 2)
        except Exception as e:
            print("SHT20 read error:", e)
            return

        # Publish to Arduino Cloud
        try:
            self.client["air_temp"] = temp
            self.client["air_humidity"] = hum
        except Exception as e:
            print("SHT20 publish error:", e)

        # Update runtime state for watering logic
        try:
            from state.runtime import set_air_temp
            set_air_temp(temp)
        except Exception:
            pass
