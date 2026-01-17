from datetime import datetime, timedelta
import pytz
from .core import Ephemeris
from .utils import TITHIS, NAKSHATRAS, YOGAS, KARANAS_MOVABLE, KARANAS_FIXED, normalize_degrees, format_time
from .solar import SolarCalendar

class Panchang:
    """
    Calculates Panchang data for a specific date and location.
    """
    def __init__(self, dt: datetime, lat: float = 22.5726, lon: float = 88.3639):
        """
        Initialize Panchang calculation.
        dt: datetime object (timezone aware preferred, else assumed UTC)
        lat: Latitude (default Kolkata)
        lon: Longitude (default Kolkata)
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.utc)
        self.dt = dt
        self.lat = lat
        self.lon = lon
        self.jd = Ephemeris.get_julian_day(dt)
        
        # Calculate Planetary Positions
        self.sun_long, self.moon_long = Ephemeris.get_planetary_positions(self.jd)
        
        # Calculate Panchang Elements
        self._calculate_elements()
        
        # Calculate Timings
        self._calculate_timings()
        
        # Calculate Bengali Date
        self._calculate_bengali_date()

    def _calculate_elements(self):
        # Tithi
        diff = normalize_degrees(self.moon_long - self.sun_long)
        self.tithi_index = int(diff / 12)
        self.tithi_name = TITHIS[self.tithi_index % 30]
        self.tithi_end = self._calculate_end_time(self._get_tithi_index, self.tithi_index)
        
        # Nakshatra
        self.nakshatra_index = int(self.moon_long / (360 / 27))
        self.nakshatra_name = NAKSHATRAS[self.nakshatra_index % 27]
        self.nakshatra_end = self._calculate_end_time(self._get_nakshatra_index, self.nakshatra_index)
        
        # Yoga
        total = normalize_degrees(self.sun_long + self.moon_long)
        self.yoga_index = int(total / (360 / 27))
        self.yoga_name = YOGAS[self.yoga_index % 27]
        self.yoga_end = self._calculate_end_time(self._get_yoga_index, self.yoga_index)
        
        # Karana
        karana_idx = int(diff / 6)
        if karana_idx == 0:
            self.karana_name = "Kimstughna"
        elif karana_idx >= 57:
            if karana_idx == 57: self.karana_name = "Shakuni"
            elif karana_idx == 58: self.karana_name = "Chatushpada"
            else: self.karana_name = "Naga"
        else:
            self.karana_name = KARANAS_MOVABLE[(karana_idx - 1) % 7]

    def _get_tithi_index(self, sun, moon):
        return int(normalize_degrees(moon - sun) / 12)

    def _get_nakshatra_index(self, sun, moon):
        return int(moon / (360 / 27))

    def _get_yoga_index(self, sun, moon):
        return int(normalize_degrees(sun + moon) / (360 / 27))

    def _calculate_end_time(self, check_func, current_index):
        """Find the end time of the current element."""
        # Iterative search forward
        step = 15 # minutes
        dt = self.dt
        for _ in range(int(30 * 60 / step)): # Search up to 30 hours
            dt += timedelta(minutes=step)
            jd = Ephemeris.get_julian_day(dt)
            s, m = Ephemeris.get_planetary_positions(jd)
            if check_func(s, m) != current_index:
                # Refine search (binary search could be better but linear step back is fine)
                # Let's just return this approximate time for now
                return dt
        return None

    def _calculate_timings(self):
        self.sunrise, self.sunset = Ephemeris.get_sunrise_sunset(self.dt, self.lat, self.lon)
        
        self.timings = {}
        if self.sunrise and self.sunset:
            day_duration = (self.sunset - self.sunrise).total_seconds() / 60 # minutes
            part_duration = day_duration / 8
            weekday = self.dt.weekday() # 0=Mon
            
            # Rahu Kalam
            rahu_indices = {0: 1, 1: 6, 2: 4, 3: 5, 4: 3, 5: 2, 6: 7}
            rahu_start = self.sunrise + timedelta(minutes=rahu_indices[weekday] * part_duration)
            rahu_end = rahu_start + timedelta(minutes=part_duration)
            
            # Yama Gandam
            yama_indices = {0: 3, 1: 2, 2: 1, 3: 0, 4: 6, 5: 5, 6: 4}
            yama_start = self.sunrise + timedelta(minutes=yama_indices[weekday] * part_duration)
            yama_end = yama_start + timedelta(minutes=part_duration)
            
            # Abhijit (8th Muhurta of 15)
            muhurta = day_duration / 15
            abhijit_start = self.sunrise + timedelta(minutes=7 * muhurta)
            abhijit_end = abhijit_start + timedelta(minutes=muhurta)
            
            self.timings = {
                "rahu_start": rahu_start,
                "rahu_end": rahu_end,
                "yama_start": yama_start,
                "yama_end": yama_end,
                "abhijit_start": abhijit_start,
                "abhijit_end": abhijit_end
            }

    def _calculate_bengali_date(self):
        day, month, year = SolarCalendar.get_bengali_date(self.dt)
        self.bengali_date = day
        self.bengali_month = month
        self.bengali_year = year

    def to_dict(self):
        return {
            "tithi": {"name": self.tithi_name, "end": format_time(self.tithi_end)},
            "nakshatra": {"name": self.nakshatra_name, "end": format_time(self.nakshatra_end)},
            "yoga": {"name": self.yoga_name, "end": format_time(self.yoga_end)},
            "karan": {"name": self.karana_name, "end": ""},
            "timings": {k: format_time(v) for k, v in self.timings.items()},
            "sunrise": format_time(self.sunrise),
            "sunset": format_time(self.sunset),
            "bengali_date": str(self.bengali_date),
            "bengali_month": self.bengali_month,
            "bengali_year": str(self.bengali_year)
        }
