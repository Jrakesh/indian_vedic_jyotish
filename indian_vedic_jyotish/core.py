import swisseph as swe
import pytz
from datetime import datetime

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
        Calculate sunrise and sunset for a given date and location.
        Returns (sunrise_dt, sunset_dt) as datetime objects or None.
        """
        # Start search from midnight of the given date
        midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        jd_start = Ephemeris.get_julian_day(midnight)
        
        # swe.rise_trans expects (lon, lat, height)
        geopos = (lon, lat, 0)
        
        # Calculate Sunrise
        # disc_center=True (Hindu sunrise is usually upper limb, but standard calc often uses center or refraction)
        # We use standard SWIEPH flags which include refraction.
        # 0 = transit, 1 = rise, 2 = set
        
        rise_res = swe.rise_trans(jd_start, swe.SUN, swe.FLG_SWIEPH, geopos)
        set_res = swe.rise_trans(jd_start, swe.SUN, swe.FLG_SWIEPH, geopos)
        
        sunrise_dt = None
        sunset_dt = None
        
        if rise_res and rise_res[1]: # rise_res[1] is rise time in JD
             # Convert JD back to datetime
             # Note: This returns UTC JD. We need to convert to local time.
             # Actually swe.rise_trans returns JD in UT.
             
             # We need to be careful. rise_res might return a tuple.
             # Documentation: returns ((transit, rise, set), ret_flag)
             # Wait, pyswisseph returns a tuple of times?
             # Let's double check standard usage.
             pass

        # Let's use a more robust approach for Rise/Set
        # We need to find the *next* rise after midnight
        
        res = swe.rise_trans(jd_start, swe.SUN, swe.FLG_SWIEPH, geopos)
        # res is ((transit, rise, set), flags)
        
        if res:
            times = res[0]
            rise_jd = times[1]
            set_jd = times[2]
            
            if rise_jd > 0:
                y, m, d, h = swe.revjul(rise_jd)
                # h is decimal hour
                hour = int(h)
                minute = int((h - hour) * 60)
                second = int(((h - hour) * 60 - minute) * 60)
                sunrise_dt = datetime(y, m, d, hour, minute, second, tzinfo=pytz.utc)
                
            if set_jd > 0:
                y, m, d, h = swe.revjul(set_jd)
                hour = int(h)
                minute = int((h - hour) * 60)
                second = int(((h - hour) * 60 - minute) * 60)
                sunset_dt = datetime(y, m, d, hour, minute, second, tzinfo=pytz.utc)
                
        return sunrise_dt, sunset_dt
