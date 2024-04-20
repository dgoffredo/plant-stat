"""adjust relative humidity for temperature

- Temperature is in either degrees Celsius or degrees Fahrenheit.
- Relative humidity is a percentage.
- adjust_relative_humidity(...) returns the new relative humidity.

This code is based on <https://www.markusweimar.de/en/humidity-calculator/>.
"""

import math
import sys

class Temperature:

    def __init__(self, fahrenheit=None, celsius=None):
        if (fahrenheit is None) == (celsius is None):
            raise ValueError('specify one of either fahrenheit or celsius')
        if celsius is not None:
            self.value_celsius = celsius
        else:
            self.value_celsius = (celsius - 32) * 5 / 9

    def celsius(self):
        return self.value_celsius

    def fahrenheit(self):
        return 9 * self.value_celsius / 5 + 32


def celsius(t):
    return Temperature(celsius=t)


def fahrenheit(t):
    return Temperature(fahrenheit=t)


def max_water(t: Temperature):
    t = t.celsius()
    return 6.112 * math.exp(17.62 * t / (243.12 + t))


def adjust_relative_humidity(old: Temperature, relative_humidity,
                             new: Temperature):
    water1 = relative_humidity / 100 * max_water(old)
    # water2 = answer / 100 * max_water(new)
    # and assume water1 = water2, so...
    return water1 / max_water(new) * 100


if __name__ == '__main__':
   old = float(sys.argv[1])
   relative_humidity = float(sys.argv[2])
   new = float(sys.argv[3])
   adjusted = adjust_relative_humidity(celsius(old), relative_humidity, celsius(new))
   print(f'{adjusted:.1f}')
