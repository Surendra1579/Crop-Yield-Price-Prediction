import logging
import requests
from functools import lru_cache
from typing import Tuple, Optional

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rainfall_service")

# Fallback baseline annual rainfall values (in mm) for major Indian States and Districts
HISTORICAL_DISTRICT_RAINFALL = {
    # Andhra Pradesh
    ("ANDHRA PRADESH", "ELURU"): 1150.0,
    ("ANDHRA PRADESH", "WEST GODAVARI"): 1150.0,
    ("ANDHRA PRADESH", "EAST GODAVARI"): 1200.0,
    ("ANDHRA PRADESH", "GUNTUR"): 850.0,
    ("ANDHRA PRADESH", "KRISHNA"): 1030.0,
    ("ANDHRA PRADESH", "VISAKHAPATNAM"): 1200.0,
    ("ANDHRA PRADESH", "ANANTAPUR"): 560.0,
    ("ANDHRA PRADESH", "CHITTOOR"): 930.0,
    ("ANDHRA PRADESH", "KURNOOL"): 670.0,
    ("ANDHRA PRADESH", "PRAKASAM"): 870.0,
    ("ANDHRA PRADESH", "SRIKAKULAM"): 1160.0,
    ("ANDHRA PRADESH", "VIZIANAGARAM"): 1130.0,
    ("ANDHRA PRADESH", "Y.S.R."): 700.0,
    ("ANDHRA PRADESH", "KADAPA"): 700.0,
    
    # Karnataka
    ("KARNATAKA", "BANGALORE URBAN"): 970.0,
    ("KARNATAKA", "BELAGAVI"): 810.0,
    ("KARNATAKA", "MYSURU"): 790.0,
    
    # Tamil Nadu
    ("TAMIL NADU", "CHENNAI"): 1380.0,
    ("TAMIL NADU", "COIMBATORE"): 650.0,
    ("TAMIL NADU", "MADURAI"): 840.0,

    # Maharashtra
    ("MAHARASHTRA", "PUNE"): 740.0,
    ("MAHARASHTRA", "NAGPUR"): 1090.0,
    ("MAHARASHTRA", "NASHIK"): 700.0,

    # Uttar Pradesh
    ("UTTAR PRADESH", "LUCKNOW"): 980.0,
    ("UTTAR PRADESH", "KANPUR"): 830.0,
    ("UTTAR PRADESH", "VARANASI"): 1000.0,
    
    # Punjab
    ("PUNJAB", "LUDHIANA"): 680.0,
    ("PUNJAB", "AMRITSAR"): 650.0,

    # Gujarat
    ("GUJARAT", "AHMEDABAD"): 750.0,
    ("GUJARAT", "SURAT"): 1200.0,
}

# State-level default average fallback (mm)
STATE_DEFAULT_RAINFALL = {
    "ANDHRA PRADESH": 960.0,
    "ASSAM": 2800.0,
    "BIHAR": 1180.0,
    "CHHATTISGARH": 1300.0,
    "GUJARAT": 800.0,
    "HARYANA": 600.0,
    "HIMACHAL PRADESH": 1250.0,
    "JAMMU AND KASHMIR": 1000.0,
    "JHARKHAND": 1200.0,
    "KARNATAKA": 1150.0,
    "KERALA": 3000.0,
    "MADHYA PRADESH": 1020.0,
    "MAHARASHTRA": 1100.0,
    "ODISHA": 1450.0,
    "PUNJAB": 650.0,
    "RAJASTHAN": 550.0,
    "TAMIL NADU": 990.0,
    "TELANGANA": 900.0,
    "UTTAR PRADESH": 950.0,
    "UTTARKHAND": 1500.0,
    "WEST BENGAL": 1750.0,
}

NATIONAL_DEFAULT_RAINFALL = 1100.0


def geocode_district(state: str, district: str) -> Optional[Tuple[float, float]]:
    """
    Geocode State and District using Open-Meteo Geocoding API.
    Returns (latitude, longitude) or None if resolution fails.
    """
    clean_district = district.strip()
    clean_state = state.strip()
    query = f"{clean_district}, {clean_state}, India"
    
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": clean_district,
        "count": 5,
        "language": "en",
        "format": "json"
    }
    headers = {"User-Agent": "AgriPredict-System/1.0"}
    
    try:
        logger.info(f"[Geocoding] Querying Open-Meteo for: '{query}'")
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if results:
                # First check for exact matching admin1 (state) or result in India
                for item in results:
                    if item.get("country_code") == "IN":
                        lat = float(item["latitude"])
                        lon = float(item["longitude"])
                        logger.info(f"[Geocoding OK] Found coordinates for '{clean_district}': ({lat}, {lon})")
                        return (lat, lon)
                
                # Fallback to first result
                lat = float(results[0]["latitude"])
                lon = float(results[0]["longitude"])
                logger.info(f"[Geocoding OK] Found fallback coordinates: ({lat}, {lon})")
                return (lat, lon)
    except Exception as e:
        logger.warning(f"[Geocoding Warning] Failed to geocode '{query}': {e}")
        
    return None


def fetch_precipitation_from_open_meteo(lat: float, lon: float, year: int) -> Optional[float]:
    """
    Fetch annual cumulative precipitation (in mm) from Open-Meteo Archive API.
    If requested year is current or future, query the most recent complete calendar year (e.g. 2023).
    """
    # For weather archive data, choose a completed historical year if requested year is >= 2024
    target_year = year if year <= 2023 else 2023
    start_date = f"{target_year}-01-01"
    end_date = f"{target_year}-12-31"

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata"
    }
    headers = {"User-Agent": "AgriPredict-System/1.0"}

    try:
        logger.info(f"[Weather API] Fetching annual rainfall for ({lat}, {lon}) for year {target_year}")
        res = requests.get(url, params=params, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            daily_precip = data.get("daily", {}).get("precipitation_sum", [])
            valid_vals = [p for p in daily_precip if p is not None]
            if valid_vals:
                total_rainfall = round(sum(valid_vals), 1)
                logger.info(f"[Weather API OK] Total precipitation calculated: {total_rainfall} mm")
                return total_rainfall
    except Exception as e:
        logger.warning(f"[Weather API Warning] Failed to fetch precipitation: {e}")

    return None


@lru_cache(maxsize=256)
def get_annual_rainfall(state: str, district: str, crop_year: int = 2024) -> Tuple[float, str]:
    """
    Main function to obtain annual rainfall (mm) for a given location.
    Cached using LRU cache for high performance on repeated queries.

    Returns:
        (rainfall_mm: float, source_info: str)
    """
    norm_state = state.strip().upper()
    norm_district = district.strip().upper()

    # Step 1: Geocode location
    coords = geocode_district(state, district)
    if coords:
        lat, lon = coords
        # Step 2: Fetch precipitation from Open-Meteo Weather API
        rainfall_val = fetch_precipitation_from_open_meteo(lat, lon, crop_year)
        if rainfall_val is not None and rainfall_val > 0:
            target_yr = crop_year if crop_year <= 2023 else 2023
            return rainfall_val, f"Open-Meteo API ({target_yr})"

    # Step 3: Fallback 1 - Historical District Lookup
    lookup_key = (norm_state, norm_district)
    if lookup_key in HISTORICAL_DISTRICT_RAINFALL:
        val = HISTORICAL_DISTRICT_RAINFALL[lookup_key]
        logger.info(f"[Fallback District] Using historical district average for {district}: {val} mm")
        return val, f"Historical District Baseline ({district.title()})"

    # Step 4: Fallback 2 - State Average
    if norm_state in STATE_DEFAULT_RAINFALL:
        val = STATE_DEFAULT_RAINFALL[norm_state]
        logger.info(f"[Fallback State] Using historical state average for {state}: {val} mm")
        return val, f"Historical State Average ({state.title()})"

    # Step 5: Fallback 3 - National Average
    logger.info(f"[Fallback National] Using national average rainfall: {NATIONAL_DEFAULT_RAINFALL} mm")
    return NATIONAL_DEFAULT_RAINFALL, "National Baseline Average"
