# Indian Vedic Jyotish Library

A Python library for accurate Indian Astrology calculations, focusing on **Drik Siddhanta** and **Bengali Panjika** rules.

## Features
- **Core Engine**: Built on `pyswisseph` (Swiss Ephemeris) for high precision.
- **Location**: Defaults to Kolkata, India.
- **Panchang**: Tithi, Nakshatra, Yoga, Karana, Vara.
- **Bengali Calendar**: Solar date (e.g., 1st Boishakh) based on Surya Sankranti.
- **Timings**: Sunrise, Sunset, Rahu Kalam, Yama Gandam, Abhijit Muhurat.

## Installation

```bash
pip install .
```

## Usage

```python
from datetime import datetime
from indian_vedic_jyotish import Panchang

dt = datetime(2024, 4, 14, 10, 0, 0) # Poila Boishakh
p = Panchang(dt)

print(p.tithi)
print(p.nakshatra)
print(p.bengali_date)
```
