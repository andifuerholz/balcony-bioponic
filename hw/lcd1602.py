# hw/lcd1602.py
# Clean integration of AiP31068L 1602 LCD + SN3193 backlight controller
# Uses shared I2C bus from main.py

import time

# LCD1602 I2C address (7-bit)
LCD_ADDRESS = 0x3E   # 0x7C >> 1

# Command prefixes
COMMAND_MODE = 0x80
DATA_MODE = 0x40

# LCD Commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME   = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT  = 0x10
LCD_FUNCTIONSET  = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# Flags
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTDECREMENT = 0x00

LCD_DISPLAYON = 0x04
LCD_CURSOROFF = 0x00
LCD_BLINKOFF = 0x00

LCD_4BITMODE = 0x00
LCD_1LINE    = 0x00
LCD_2LINE    = 0x08
LCD_5x8DOTS  = 0x00


class LCD1602:
    """
    1602 LCD with AiP31068L controller.
    Uses direct I2C commands (not PCF8574).
    """

    def __init__(self, i2c, cols=16, rows=2):
        self.i2c = i2c
        self.cols = cols
        self.rows = rows

        self._displayfunction = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS
        self._init_lcd()

    # --- Low-level writes ----------------------------------

    def _cmd(self, value):
        """Send command to LCD."""
        self.i2c.writeto_mem(LCD_ADDRESS, COMMAND_MODE, bytes([value]))

    def _data(self, value):
        """Send data byte."""
        self.i2c.writeto_mem(LCD_ADDRESS, DATA_MODE, bytes([value]))

    # --- LCD Initialization --------------------------------

    def _init_lcd(self):
        time.sleep(0.05)
        if self.rows > 1:
            self._displayfunction |= LCD_2LINE

        # Function set sequence
        self._cmd(LCD_FUNCTIONSET | self._displayfunction)
        time.sleep(0.005)
        self._cmd(LCD_FUNCTIONSET | self._displayfunction)
        time.sleep(0.005)
        self._cmd(LCD_FUNCTIONSET | self._displayfunction)

        # Display ON
        self._displaycontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.display(True)

        # Clear screen
        self.clear()

        # Entry Mode: left-to-right
        self._entrymode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        self._cmd(LCD_ENTRYMODESET | self._entrymode)

    # --- Public API ----------------------------------------

    def clear(self):
        self._cmd(LCD_CLEARDISPLAY)
        time.sleep(0.005)

    def home(self):
        self._cmd(LCD_RETURNHOME)
        time.sleep(0.005)

    def display(self, enable=True):
        if enable:
            self._cmd(LCD_DISPLAYCONTROL | self._displaycontrol)
        else:
            self._cmd(LCD_DISPLAYCONTROL | 0x00)

    def setCursor(self, col, row):
        if row >= self.rows:
            row = self.rows - 1

        addr = col + (0x80 if row == 0 else 0xC0)
        self._cmd(addr)

    def printout(self, text):
        if not isinstance(text, str):
            text = str(text)
        for ch in text:
            self._data(ord(ch))


# -----------------------------------------------------------------
# SN3193 LED Backlight Controller
# -----------------------------------------------------------------

SN3193_ADDR = 0x6B

# Registers
SHUTDOWN_REG = 0x00
LED_MODE_REG = 0x02
CURRENT_SETTING_REG = 0x03
PWM_1_REG = 0x04
PWM_UPDATE_REG = 0x07


class SN3193:
    """
    Simple wrapper for SN3193 LED backlight.
    """

    def __init__(self, i2c):
        self.i2c = i2c
        self._init_chip()

    def _write(self, reg, val):
        self.i2c.writeto_mem(SN3193_ADDR, reg, bytes([val]))

    def _init_chip(self):
        self._write(SHUTDOWN_REG, 0x20)
        self._write(LED_MODE_REG, 0x00)
        self._write(CURRENT_SETTING_REG, 0x00)
        time.sleep(0.01)
        self._write(PWM_1_REG, 0xFF)
        time.sleep(0.05)
        self._write(PWM_UPDATE_REG, 0x00)

    def set_brightness(self, percent):
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        pwm = int(percent * 2.55)  # 0..255
        self._write(PWM_1_REG, pwm)
        time.sleep(0.05)
        self._write(PWM_UPDATE_REG, 0x00)

