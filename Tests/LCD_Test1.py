# LCD_Test1.py
from machine import Pin, I2C
from LCD1602 import LCD1602, SN3193

lcd = LCD1602(16, 2)
led = SN3193()

led.set_brightness(5)

lcd.clear()
lcd.printout("Hallo!")
