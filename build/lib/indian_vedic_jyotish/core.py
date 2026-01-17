import swisseph as swe
import pytz
from datetime import datetime
from .utils import normalize_degrees

# Set Ayanamsa to Lahiri (Chitra Paksha) - Standard for Indian Astrology
swe.set_sid_mode(swe.SIDM_LAHIRI)

class Ephemeris:
    """
    Wrapper around pyswisseph for easy planetary position calculations.
    """
    
    @staticmethod
    def get_julian_day(dt: datetime) -> float:
        """Convert datetime to Julian Day."""
        if dt.tzinfo:
            dt = dt.astimezone(pytz.utc)
        return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

    @staticmethod
    def get_planetary_positions(jd: float):
        """
        Get geocentric longitude of Sun and Moon.
        Returns (sun_long, moon_long) in degrees.
        """
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        # Sun
        sun_res = swe.calc_ut(jd, swe.SUN, flags)
        sun_long = sun_res[0][0]
        
        # Moon
        moon_res = swe.calc_ut(jd, swe.MOON, flags)
        moon_long = moon_res[0][0]
        
        return sun_long, moon_long

    @staticmethod
    def get_sunrise_sunset(dt: datetime, lat: float, lon: float):
        """
        Calculate sunrise and sunset for a given date and location using iterative search.
        Returns (sunrise_dt, sunset_dt) as datetime objects or None.
        """
        # Target altitude for sunrise/sunset (center of disc) with refraction
        # Standard refraction is 34 arcmin = 0.5667 deg.
        # Sun semi-diameter is ~16 arcmin = 0.2667 deg.
        # Upper limb rise: -0.8333 deg (-50 arcmin).
        TARGET_ALT = -0.8333
        
        def get_sun_alt(t_jd):
            # Calculate Topocentric position
            swe.set_topo(lon, lat, 0)
            flags = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL | swe.FLG_TOPOCTR
            res = swe.calc_ut(t_jd, swe.SUN, flags)
            # res[0] is (RA, Dec, Dist, SpeedRA, SpeedDec, SpeedDist)
            ra = res[0][0]
            dec = res[0][1]
            
            import math
            lat_rad = math.radians(lat)
            dec_rad = math.radians(dec)
            
            # Calculate GST
            gst = swe.sidtime(t_jd)
            # Local Sidereal Time (hours)
            lst = gst + lon / 15.0
            # Hour Angle (degrees)
            ha_deg = normalize_degrees(lst * 15.0 - ra)
            ha_rad = math.radians(ha_deg)
            
            sin_alt = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad)
            # Clamp value for asin
            if sin_alt > 1.0: sin_alt = 1.0
            if sin_alt < -1.0: sin_alt = -1.0
            
            alt_rad = math.asin(sin_alt)
            return math.degrees(alt_rad)

        def find_event(start_jd, rising=True):
            # Iterative search
            t = start_jd
            for _ in range(10):
                alt = get_sun_alt(t)
                diff = alt - TARGET_ALT
                if abs(diff) < 0.001: # Precision ~1 sec
                    return t
                
                # Correction: 1 deg ~ 4 min = 1/360 days
                correction = -diff / 360.0 
                if not rising: correction = -correction 
                t += correction
            return t

        # Search for Sunrise around 6 AM
        midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        jd_mid = Ephemeris.get_julian_day(midnight)
        
        # Approx Sunrise: 6 AM = 0.25 days from midnight
        rise_guess = jd_mid + 0.25
        # Approx Sunset: 6 PM = 0.75 days from midnight
        set_guess = jd_mid + 0.75
        
        rise_jd = find_event(rise_guess, rising=True)
        set_jd = find_event(set_guess, rising=False)
        
        sunrise_dt = None
        sunset_dt = None
        
        if rise_jd:
            y, m, d, h_dec = swe.revjul(rise_jd)
            h = int(h_dec); mn = int((h_dec - h) * 60); s = int(((h_dec - h) * 60 - mn) * 60)
            sunrise_dt = datetime(y, m, d, h, mn, s, tzinfo=pytz.utc)
            
        if set_jd:
            y, m, d, h_dec = swe.revjul(set_jd)
            h = int(h_dec); mn = int((h_dec - h) * 60); s = int(((h_dec - h) * 60 - mn) * 60)
            sunset_dt = datetime(y, m, d, h, mn, s, tzinfo=pytz.utc)
            
        return sunrise_dt, sunset_dt
