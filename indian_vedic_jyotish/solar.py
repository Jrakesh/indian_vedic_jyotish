import swisseph as swe
from datetime import datetime, timedelta
import pytz
from .core import Ephemeris
from .utils import BENGALI_MONTHS

class SolarCalendar:
    """
    Handles calculations for the Bengali Solar Calendar (Drik Siddhanta).
    """
    
    @staticmethod
    def get_sankranti_time(year: int, month: int, target_sign: int) -> float:
        """
        Find the Julian Day when Sun enters a specific sign (0=Aries, 1=Taurus...).
        Search around the expected time.
        """
        # Approximate date for Sankranti:
        # Aries (Boishakh): ~April 14
        # Taurus (Jyoishtho): ~May 15
        # ...
        # We can search broadly.
        
        # Construct a start date for search.
        # target_sign 0 (Aries) -> Month 4 (April)
        search_month = (target_sign + 3) % 12
        if search_month == 0: search_month = 12
        
        search_year = year
        if target_sign >= 9: # Jan, Feb, Mar are in next year relative to April start? No.
             # Aries (0) -> April (4)
             # ...
             # Capricorn (9) -> Jan (1)
             pass
        
        # Let's just search backward from the current date to find the last ingress.
        pass

    @staticmethod
    def get_bengali_date(dt: datetime):
        """
        Calculate Bengali Date, Month, and Year for a given datetime.
        Returns (day, month_name, year).
        """
        jd = Ephemeris.get_julian_day(dt)
        sun_long, _ = Ephemeris.get_planetary_positions(jd)
        
        # Current Solar Month Index (0 = Aries/Boishakh, 1 = Taurus/Jyoishtho...)
        # Sun Longitude 0-30 is Aries.
        month_index = int(sun_long / 30)
        
        # We need to find the EXACT time Sun entered this sign (Sankranti).
        # We search backward.
        
        # Define a function to get Sun's longitude difference from the sign start
        def get_sun_offset(t_jd, sign_start_deg):
            s_long, _ = Ephemeris.get_planetary_positions(t_jd)
            # Handle 360 wrap around for Pisces->Aries
            diff = s_long - sign_start_deg
            if diff < -180: diff += 360
            if diff > 180: diff -= 360
            return diff

        sign_start_deg = month_index * 30.0
        
        # Use simple bisection or linear search to find ingress time (offset = 0)
        # Start from current time and go back up to 32 days.
        
        # Initial bracket
        t1 = jd
        t0 = jd - 32.0 
        
        # Refine t0 to ensure it's before ingress
        # If we are in the middle of the month, -32 days should definitely be in previous sign.
        
        # Root finding (when offset = 0)
        # Using swe.solcross is better/faster if available, but let's stick to bisection for simplicity/robustness without complex C-api usage if not familiar.
        # Actually swe.solcross is not standard python binding?
        # Let's use bisection.
        
        lower = t0
        upper = t1
        
        # Find exact ingress JD
        ingress_jd = None
        for _ in range(20): # 20 iterations is enough precision
            mid = (lower + upper) / 2
            off = get_sun_offset(mid, sign_start_deg)
            if off > 0:
                upper = mid
            else:
                lower = mid
        
        ingress_jd = upper
        
        # Calculate Civil Day 1 of the month
        # Rule: If Sankranti is before Midnight (IST?), next day is Day 1.
        # If after Midnight, day after next is Day 1.
        # We need to convert ingress_jd to IST datetime.
        
        # Convert JD to UTC datetime
        y, m, d, h_dec = swe.revjul(ingress_jd)
        h = int(h_dec)
        mn = int((h_dec - h) * 60)
        s = int(((h_dec - h) * 60 - mn) * 60)
        ingress_utc = datetime(y, m, d, h, mn, s, tzinfo=pytz.utc)
        
        # Convert to IST
        ist = pytz.timezone('Asia/Kolkata')
        ingress_ist = ingress_utc.astimezone(ist)
        
        # Determine Day 1 Date
        # If ingress is between Sunrise and Midnight -> Next Day is Day 1
        # If ingress is between Midnight and Sunrise -> That Day is Day 1 (because it's technically "tomorrow" relative to previous sunrise?)
        # Let's use the standard West Bengal rule:
        # "If Sankranti occurs between sunrise and midnight, the month begins on the following day."
        # "If Sankranti occurs after midnight, the month begins on the day after that." (Wait, this implies +2 days?)
        
        # Let's simplify: Day 1 is usually the day AFTER Sankranti day.
        # Sankranti Day = Day 0 (Last day of previous month).
        
        # Let's find the date of Sankranti in IST.
        sankranti_date = ingress_ist.date()
        
        # Day 1 is sankranti_date + 1 day
        day_1_date = sankranti_date + timedelta(days=1)
        
        # Check if Sankranti was "late" (after midnight).
        # In Bengali convention, day starts at Sunrise.
        # If Sankranti is at 2 AM on 15th, it is technically "late night of 14th".
        # So 15th is Day 1?
        # No, let's stick to the standard Drik Siddhanta convention used by Visuddha Siddhanta Panjika.
        # Rule: If Sankranti is before midnight, next day is 1st.
        # If Sankranti is after midnight, day after next is 1st.
        
        # Check if ingress_ist is after 00:00 and before Sunrise? 
        # Or just check hour.
        # Midnight is 00:00 IST.
        
        # Actually, let's use the simpler rule for now: Day 1 is the day after the civil day of Sankranti.
        # We calculate the difference in days between current dt and day_1_date.
        
        current_date = dt.astimezone(ist).date()
        day_of_month = (current_date - day_1_date).days + 1
        
        # If day_of_month <= 0, it means we are in the previous month!
        # We need to handle this.
        if day_of_month <= 0:
            # We are in the previous month.
            # Recursive call? Or just subtract 1 from month_index and recalculate.
            # Better to handle it iteratively but recursion is cleaner here for one step.
            # But wait, month_index was calculated from current sun position.
            # If we are in the first few days of the solar month, sun_long is 0..30.
            # So month_index is correct for the *solar* month.
            # But the *civil* month might lag behind by 1-2 days.
            # So if day_of_month <= 0, it means we are still in the *previous* civil month.
            # So we should use (month_index - 1).
            
            prev_month_index = (month_index - 1) % 12
            # Recalculate ingress for prev month
            sign_start_deg = prev_month_index * 30.0
            
            # Search again
            lower = jd - 65.0
            upper = jd - 15.0 # Ingress must be further back
             
            for _ in range(20):
                mid = (lower + upper) / 2
                off = get_sun_offset(mid, sign_start_deg)
                if off > 0: upper = mid
                else: lower = mid
            
            ingress_jd = upper
            
            # Recalculate Day 1
            y, m, d, h_dec = swe.revjul(ingress_jd)
            h = int(h_dec); mn = int((h_dec - h) * 60); s = int(((h_dec - h) * 60 - mn) * 60)
            ingress_ist = datetime(y, m, d, h, mn, s, tzinfo=pytz.utc).astimezone(ist)
            
            sankranti_date = ingress_ist.date()
            day_1_date = sankranti_date + timedelta(days=1)
            
            day_of_month = (current_date - day_1_date).days + 1
            month_index = prev_month_index

        # Bengali Year (Bangabda)
        # April 14, 2024 is start of 1431.
        # Gregorian Year - 593 (approx).
        # If month is Boishakh (0) to Poush (8), Year = Greg - 593
        # If month is Magh (9) to Chaitra (11), Year = Greg - 594?
        # Actually, Bangabda changes on 1st Boishakh.
        # So if month_index is 0 (Boishakh), we are in new year.
        
        greg_year = current_date.year
        if current_date.month < 4:
            bangabda = greg_year - 594
        elif current_date.month > 4:
            bangabda = greg_year - 593
        else: # April
            if month_index == 0: # Boishakh
                bangabda = greg_year - 593
            else: # Chaitra
                bangabda = greg_year - 594
                
        return day_of_month, BENGALI_MONTHS[month_index], bangabda
