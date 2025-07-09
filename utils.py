import math
from fractions import Fraction


def float_to_rational(f):
    frac = Fraction(f).limit_denominator(10000)
    return (frac.numerator, frac.denominator)


def shutter_speed_to_apex_rational(shutter_speed_str):
    """
    Convert shutter speed string (e.g., "1/125" or "0.008") to APEX rational tuple for EXIF.
    """
    shutter_speed_str = shutter_speed_str.strip()
    if '"' in shutter_speed_str:
        # Format like 1" or 2.5"
        shutter_speed_sec = float(shutter_speed_str.replace('"', "").strip())
    elif "/" in shutter_speed_str:
        num, denom = shutter_speed_str.split("/")
        shutter_speed_sec = float(num) / float(denom)
    else:
        shutter_speed_sec = float(shutter_speed_str)
    shutter_speed_apex = -math.log2(shutter_speed_sec)
    return float_to_rational(shutter_speed_apex)


def aperture_to_apex_rational(aperture_str):
    """
    Convert aperture string (e.g., "2.8") to APEX rational tuple for EXIF.
    """
    aperture_val = float(aperture_str)
    aperture_apex = 2 * math.log2(aperture_val)
    return float_to_rational(aperture_apex)
