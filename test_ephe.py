import swisseph as swe
import os

def test_ephe():
    # print(f"Swiss Ephemeris Version: {swe.version()}")
    print(f"Default Ephe Path: {swe.get_library_path()}")
    
    # Try to calculate Sun position with Swiss Ephemeris flag
    jd = swe.julday(2024, 1, 1, 12.0)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    
    try:
        res = swe.calc_ut(jd, swe.SUN, flags)
        print(f"Calculation (SWIEPH): {res}")
    except Exception as e:
        print(f"Calculation (SWIEPH) Failed: {e}")
        
    # Try with Moshier fallback
    flags_mosh = swe.FLG_MOSEPH | swe.FLG_SPEED
    try:
        res = swe.calc_ut(jd, swe.SUN, flags_mosh)
        print(f"Calculation (MOSEPH): {res}")
    except Exception as e:
        print(f"Calculation (MOSEPH) Failed: {e}")

if __name__ == "__main__":
    test_ephe()
