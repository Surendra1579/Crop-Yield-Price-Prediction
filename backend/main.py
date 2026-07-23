import sklearn.compose._column_transformer as ct

class _RemainderColsList(list):
    def __setstate__(self, state):
        if isinstance(state, dict) and "data" in state:
            self.extend(state["data"])
        elif isinstance(state, (list, tuple)):
            self.extend(state)

if not hasattr(ct, "_RemainderColsList"):
    ct._RemainderColsList = _RemainderColsList

from pathlib import Path
from datetime import date
from typing import Optional

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rainfall_service import get_annual_rainfall


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

YIELD_MODEL_PATH = BASE_DIR / "models" / "crop_yield_model.pkl"
PRICE_MODEL_PATH = BASE_DIR / "models" / "crop_price_model.pkl"
PRICE_DATA_PATH = BASE_DIR / "data" / "commodity_price.csv"


# =========================================================
# CREATE FASTAPI APP
# =========================================================

app = FastAPI(
    title="Crop Yield & Price Prediction API",
    description="API for predicting crop yield and crop market prices",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

frontend_dir = BASE_DIR.parent / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


# =========================================================
# LOAD MODELS
# =========================================================

try:
    yield_model = joblib.load(YIELD_MODEL_PATH)
    print("[OK] Crop Yield Model loaded successfully!")
except Exception as e:
    print(f"[ERROR] Error loading Crop Yield Model: {e}")
    yield_model = None


try:
    price_model = joblib.load(PRICE_MODEL_PATH)
    print("[OK] Crop Price Model loaded successfully!")
except Exception as e:
    print(f"[ERROR] Error loading Crop Price Model: {e}")
    price_model = None


# =========================================================
# LOAD HISTORICAL PRICE DATA
# =========================================================

try:
    price_data = pd.read_csv(PRICE_DATA_PATH)

    # Rename original dataset columns
    price_data = price_data.rename(
        columns={
            "District Name": "District",
            "Market Name": "Market",
            "Min Price (Rs./Quintal)": "Min_Price",
            "Max Price (Rs./Quintal)": "Max_Price",
            "Modal Price (Rs./Quintal)": "Modal_Price",
            "Min_x0020_Price": "Min_Price",
            "Max_x0020_Price": "Max_Price",
            "Modal_x0020_Price": "Modal_Price",
            "Price Date": "Arrival_Date",
        }
    )

    # Remove unnecessary serial number
    price_data = price_data.drop(
        columns=["Sl no."],
        errors="ignore"
    )

    # Convert date
    price_data["Arrival_Date"] = pd.to_datetime(
        price_data["Arrival_Date"],
        dayfirst=True,
        errors="coerce"
    )

    # Convert price to numeric
    price_data["Modal_Price"] = pd.to_numeric(
        price_data["Modal_Price"],
        errors="coerce"
    )

    # Remove invalid rows
    price_data = price_data.dropna(
        subset=[
            "Arrival_Date",
            "Modal_Price"
        ]
    )

    price_data = price_data[
        price_data["Modal_Price"] > 0
    ].copy()

    # Sort historical data
    price_data = price_data.sort_values(
        "Arrival_Date"
    ).reset_index(drop=True)

    print(
        f"[OK] Historical price data loaded successfully: "
        f"{len(price_data)} rows"
    )

except Exception as e:
    print(
        f"[ERROR] Error loading historical price data: {e}"
    )

    price_data = pd.DataFrame()


# =========================================================
# INPUT MODELS
# =========================================================

class YieldInput(BaseModel):
    Crop: str
    Crop_Year: int
    Season: str
    State: str
    District: Optional[str] = None
    Area: float
    Annual_Rainfall: Optional[float] = None
    Fertilizer: float
    Pesticide: float


class PriceInput(BaseModel):
    State: str
    District: str
    Market: str
    Commodity: str
    Variety: str
    Grade: str
    Prediction_Date: date


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Crop Yield & Price Prediction API is running",
        "yield_model_loaded": yield_model is not None,
        "price_model_loaded": price_model is not None,
        "historical_price_rows": len(price_data)
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "yield_model": (
            "loaded"
            if yield_model is not None
            else "not loaded"
        ),
        "price_model": (
            "loaded"
            if price_model is not None
            else "not loaded"
        ),
        "price_data": (
            "loaded"
            if not price_data.empty
            else "not loaded"
        )
    }


# =========================================================
# YIELD PREDICTION
# =========================================================

@app.post("/predict-yield")
def predict_yield(data: YieldInput):

    if yield_model is None:
        raise HTTPException(
            status_code=500,
            detail="Crop Yield Model is not loaded."
        )

    try:
        # Determine annual rainfall automatically if not manually provided
        rainfall_val = data.Annual_Rainfall
        rainfall_source = "User Input"

        if rainfall_val is None or rainfall_val <= 0:
            district_name = data.District if data.District else "Default"
            rainfall_val, rainfall_source = get_annual_rainfall(
                state=data.State,
                district=district_name,
                crop_year=data.Crop_Year
            )

        # Convert input Area from Acres to Hectares for ML Model (1 Acre = 0.404686 Hectares)
        area_acres = data.Area
        area_hectares = area_acres * 0.404686

        input_data = pd.DataFrame(
            [{
                "Crop": data.Crop,
                "Crop_Year": data.Crop_Year,
                "Season": data.Season,
                "State": data.State,
                "Area": area_hectares,
                "Annual_Rainfall": rainfall_val,
                "Fertilizer": data.Fertilizer,
                "Pesticide": data.Pesticide,
            }]
        )

        prediction_per_ha = float(yield_model.predict(input_data)[0])
        prediction_per_acre = round(prediction_per_ha * 0.404686, 2)
        total_production = round(prediction_per_acre * area_acres, 2)

        return {
            "success": True,
            "predicted_yield_per_acre": prediction_per_acre,
            "total_production_tons": total_production,
            "area_acres": area_acres,
            "annual_rainfall_used": rainfall_val,
            "rainfall_source": rainfall_source
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Yield prediction failed: {str(e)}"
        )



# =========================================================
# PRICE PREDICTION
# =========================================================

@app.post("/predict-price")
def predict_price(data: PriceInput):

    if price_model is None:
        raise HTTPException(
            status_code=500,
            detail="Crop Price Model is not loaded."
        )

    if price_data.empty:
        raise HTTPException(
            status_code=500,
            detail="Historical price data is not loaded."
        )

    try:

        # -----------------------------------------
        # Filter historical data
        # -----------------------------------------

        filtered_data = price_data[
            (
                price_data["State"].astype(str)
                == data.State
            )
            &
            (
                price_data["District"].astype(str)
                == data.District
            )
            &
            (
                price_data["Market"].astype(str)
                == data.Market
            )
            &
            (
                price_data["Commodity"].astype(str)
                == data.Commodity
            )
            &
            (
                price_data["Variety"].astype(str)
                == data.Variety
            )
        ].copy()

        # Use only prices before prediction date
        prediction_date = pd.Timestamp(
            data.Prediction_Date
        )

        filtered_data = filtered_data[
            filtered_data["Arrival_Date"]
            < prediction_date
        ]

        filtered_data = filtered_data.sort_values(
            "Arrival_Date"
        )

        # If strict match has fewer than 7 records, broaden fallback to commodity/variety
        if len(filtered_data) < 7:
            fallback = price_data[
                (price_data["Commodity"].astype(str) == data.Commodity) &
                (price_data["Variety"].astype(str) == data.Variety)
            ].copy()
            if len(fallback) < 7:
                fallback = price_data[price_data["Commodity"].astype(str) == data.Commodity].copy()
            if len(fallback) >= 1:
                filtered_data = fallback.sort_values("Arrival_Date")

        # Extract modal prices
        avail_prices = filtered_data["Modal_Price"].dropna().tolist() if not filtered_data.empty else [2500.0]
        if len(avail_prices) < 7:
            first_p = avail_prices[0]
            historical_prices = ([first_p] * (7 - len(avail_prices))) + avail_prices
        else:
            historical_prices = avail_prices[-7:]

        price_lag_1 = historical_prices[-1]
        price_lag_7 = historical_prices[0]
        rolling_mean_7 = sum(historical_prices) / len(historical_prices)

        # -----------------------------------------
        # Date features
        # -----------------------------------------

        year = prediction_date.year
        month = prediction_date.month
        day = prediction_date.day
        day_of_week = prediction_date.dayofweek

        # -----------------------------------------
        # Create model input
        # -----------------------------------------

        input_data = pd.DataFrame(
            [{
                "State": data.State,
                "District": data.District,
                "Market": data.Market,
                "Commodity": data.Commodity,
                "Variety": data.Variety,
                "Grade": data.Grade,
                "Year": year,
                "Month": month,
                "Day": day,
                "DayOfWeek": day_of_week,
                "Price_Lag_1": price_lag_1,
                "Price_Lag_7": price_lag_7,
                "Rolling_Mean_7": rolling_mean_7,
            }]
        )

        # -----------------------------------------
        # Predict
        # -----------------------------------------

        prediction = price_model.predict(
            input_data
        )[0]

        return {
            "success": True,

            "commodity": data.Commodity,

            "market": data.Market,

            "prediction_date": str(
                data.Prediction_Date
            ),

            "predicted_price": round(
                float(prediction),
                2
            ),

            "unit": "Rs./Quintal",

            "historical_features": {
                "previous_price": round(
                    float(price_lag_1),
                    2
                ),
                "seventh_previous_price": round(
                    float(price_lag_7),
                    2
                ),
                "seven_price_average": round(
                    float(rolling_mean_7),
                    2
                )
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Price prediction failed: {str(e)}"
        )


# =========================================================
# STATE ALIASES & DISTRICT DICTIONARIES
# =========================================================

STATE_ALIASES = {
    "uttarakhand": "uttrakhand",
    "uttrakhand": "uttrakhand",
    "jammu & kashmir": "jammu and kashmir",
    "jammu and kashmir": "jammu and kashmir",
}

ALL_STATE_DISTRICTS = {
    "Andhra Pradesh": [
        "Anakapalli", "Anantapur", "Annamayya", "Bapatla", "Chittoor", "Chittor",
        "East Godavari", "Eluru", "Guntur", "Kakinada", "Konaseema", "Krishna",
        "Kurnool", "NTR (Vijayawada)", "Nandyal", "Nellore", "Palnadu", "Prakasam",
        "Sri Sathya Sai", "Srikakulam", "Tirupati", "Visakhapatnam", "Vizianagaram",
        "West Godavari", "YSR Kadapa"
    ],
    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon",
        "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar",
        "Khammam", "Kumuram Bheem", "Mahabubabad", "Mahabubnagar", "Mancherial",
        "Medak", "Medchal Malkajgiri", "Mulugu", "Nalgonda", "Narayanpet",
        "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Ranga Reddy",
        "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
    ],
    "Tamil Nadu": [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
        "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
        "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris",
        "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga",
        "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
        "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"
    ],
    "Karnataka": [
        "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar",
        "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada",
        "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu",
        "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga",
        "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"
    ],
    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana",
        "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna",
        "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded",
        "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad",
        "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"
    ],
    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Banaskanth", "Bharuch",
        "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka",
        "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Junagarh", "Kheda",
        "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal",
        "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Vadodara(Baroda)", "Valsad"
    ]
}


DISTRICT_MARKETS = {
    # Andhra Pradesh
    "guntur": ["Guntur Chilli Yard (APMC)", "Guntur Wholesale Grain Market", "Tenali Mandi", "Narasaraopet Market"],
    "krishna": ["Vijayawada APMC Mandi", "Gudivada Grain Market", "Machilipatnam Market", "Jaggaiahpeta Mandi"],
    "chittoor": ["Chittoor APMC Mandi", "Kalikiri", "Madanapalle Tomato Market", "Punganur Mandi", "Vayalapadu"],
    "chittor": ["Chittoor APMC Mandi", "Kalikiri", "Madanapalle Tomato Market", "Punganur Mandi", "Vayalapadu"],
    "east godavari": ["Kakinada Commercial Mandi", "Rajahmundry Grain Market", "Ravulapalem Banana Market"],
    "west godavari": ["Eluru APMC Market", "Tadepalligudem Mandi", "Bhimavaram Market", "Tanuku Mandi"],
    "kurnool": ["Kurnool Main Mandi", "Yemmiganur Market", "Adoni Cotton Market", "Nandyal Mandi"],
    "nellore": ["Nellore Grain Mandi", "Gudur Market", "Kavali Market"],
    "anantapur": ["Anantapur APMC Mandi", "Hindupur Market", "Kalyandurg Market"],
    "visakhapatnam": ["Anakapalle Jaggery Mandi", "Visakhapatnam APMC Market", "Bheemunipatnam Market"],
    "srikakulam": ["Srikakulam Mandi", "Palasa Cashew Market", "Tekkali Market"],
    "vizianagaram": ["Vizianagaram Grain Mandi", "Bobbili Market", "Salur Market"],
    "prakasam": ["Ongole Mandi", "Chirala Market", "Markapur Tobacco Market"],
    "ysr kadapa": ["Kadapa APMC Mandi", "Proddatur Market", "Rayachoti Market"],
    "tirupati": ["Tirupati APMC Market", "Srikalahasti Market"],
    "kakinada": ["Kakinada Commercial Market", "Peddapuram Mandi"],
    "nandyal": ["Nandyal APMC Market", "Allagadda Market"],
    "bapatla": ["Bapatla Mandi", "Chirala Market"],
    "eluru": ["Eluru APMC Market", "Jangareddygudem Mandi"],
    "palnadu": ["Narasaraopet Mandi", "Piduguralla Market"],
    "ntr (vijayawada)": ["Vijayawada Wholesale Market", "Jaggaiahpeta Mandi"],
    "sri sathya sai": ["Hindupur Silk & Grain Mandi", "Kadiri Market"],

    # Telangana
    "hyderabad": ["Bowenpally Agricultural Market", "Gudimalkapur Mandi", "Kothapet Fruit Market"],
    "warangal": ["Warangal Grain & Chilli Yard", "Khammam Mandi", "Narsampet Market"],
    "karimnagar": ["Karimnagar APMC Market", "Jagtial Mandi", "Peddapatt Market"],
    "nizamabad": ["Nizamabad Turmeric & Grain Yard", "Kamareddy Market"],
    "khammam": ["Khammam Cotton & Chilli Market", "Wyra Market"],

    # Tamil Nadu
    "chennai": ["Koyambedu Wholesale Market Complex"],
    "coimbatore": ["Mettupalayam Market", "Coimbatore APMC Mandi", "Pollachi Market"],
    "madurai": ["Mattuthavani Central Market", "Madurai APMC Mandi"],
    "salem": ["Salem Central Mandi", "Attur Market"],
    "erode": ["Erode Turmeric Market Yard", "Gobichettipalayam Market"],

    # Karnataka
    "bengaluru urban": ["Yeshwanthpur APMC Yard", "Binny Mill Market", "KR Market"],
    "mysuru": ["Bandipalya APMC Yard", "Devaraja Market"],
    "belagavi": ["Belagavi APMC Market", "Gokak Mandi"],

    # Maharashtra
    "pune": ["Gultekdi Market Yard", "Pimpri Mandi"],
    "nashik": ["Lasalgaon Onion Yard (Asia's Largest)", "Pimplegaon Mandi", "Nashik APMC"],
    "nagpur": ["Kalamna Market Yard", "Nagpur Cotton & Orange Mandi"],

    # Gujarat
    "ahmedabad": ["Jamalpur Wholesale Market", "Vasna APMC Market", "Naroda Mandi"],
    "surat": ["Surat APMC Market Yard", "Navsari Mandi"],
    "rajkot": ["Rajkot Bedi APMC Market Yard", "Gondal APMC Market Yard"],
    "amreli": ["Damnagar Market", "Savarkundla Market", "Amreli Main Mandi"],
    "anand": ["Anand APMC Market", "Umreth Mandi"],
}


# =========================================================
# GET STATES
# =========================================================

@app.get("/states")
def get_states():

    if price_data.empty:
        return []

    raw_states = price_data["State"].dropna().astype(str).str.strip().unique().tolist()
    
    # Standardize display names
    formatted = set()
    for st in raw_states:
        if st.lower() == "uttrakhand":
            formatted.add("Uttarakhand")
        else:
            formatted.add(st)

    return sorted(list(formatted))


# =========================================================
# GET DISTRICTS
# =========================================================

@app.get("/districts/{state}")
def get_districts(state: str):

    st_clean = state.strip().lower()
    st_target = STATE_ALIASES.get(st_clean, st_clean)

    csv_dists = set()
    if not price_data.empty:
        filtered = price_data[
            price_data["State"].astype(str).str.strip().str.lower() == st_target
        ]
        csv_dists = set(filtered["District"].dropna().astype(str).str.strip().unique().tolist())

    std_dists = set()
    for st_key, dist_list in ALL_STATE_DISTRICTS.items():
        if st_key.lower() == st_clean or st_key.lower() == st_target:
            std_dists.update(dist_list)

    all_dists = sorted(list(csv_dists | std_dists))
    return all_dists if all_dists else sorted(list(csv_dists))


# =========================================================
# GET MARKETS
# =========================================================

@app.get("/markets/{state}/{district}")
def get_markets(state: str, district: str):

    st_clean = state.strip().lower()
    st_target = STATE_ALIASES.get(st_clean, st_clean)
    dist_clean = district.strip().lower()

    # 1. Markets from dataset for this specific district
    csv_markets = set()
    if not price_data.empty:
        filtered = price_data[
            (price_data["State"].astype(str).str.strip().str.lower() == st_target) &
            (price_data["District"].astype(str).str.strip().str.lower() == dist_clean)
        ]
        csv_markets = set(filtered["Market"].dropna().astype(str).str.strip().unique().tolist())

    # 2. District-specific markets from dictionary
    dict_markets = set(DISTRICT_MARKETS.get(dist_clean, []))

    all_markets = sorted(list(csv_markets | dict_markets))

    if not all_markets:
        # Fallback to district APMC Market name
        dist_title = district.strip().title()
        all_markets = [f"{dist_title} APMC Mandi", f"{dist_title} Main Market"]

    return all_markets


# =========================================================
# GET COMMODITIES
# =========================================================

@app.get("/commodities")
def get_commodities(state: str = None, district: str = None, market: str = None):

    if price_data.empty:
        return []

    filtered = price_data.copy()
    if state:
        st_clean = state.strip().lower()
        st_target = STATE_ALIASES.get(st_clean, st_clean)
        filtered = filtered[filtered["State"].astype(str).str.strip().str.lower() == st_target]
    if district:
        filtered = filtered[filtered["District"].astype(str).str.strip().str.lower() == district.strip().lower()]
    if market:
        filtered = filtered[filtered["Market"].astype(str).str.strip().str.lower() == market.strip().lower()]

    commodities = sorted(filtered["Commodity"].dropna().astype(str).str.strip().unique().tolist())
    if not commodities:
        commodities = sorted(price_data["Commodity"].dropna().astype(str).str.strip().unique().tolist())

    return commodities


# =========================================================
# GET VARIETIES
# =========================================================

def _fetch_varieties(state: str = None, district: str = None, market: str = None, commodity: str = None):
    if price_data.empty:
        return ["Standard Variety", "Hybrid", "Average (Whole)", "FAQ", "Other"]

    filtered = price_data.copy()
    if state:
        st_clean = state.strip().lower()
        st_target = STATE_ALIASES.get(st_clean, st_clean)
        filtered = filtered[filtered["State"].astype(str).str.strip().str.lower() == st_target]
    if district:
        filtered = filtered[filtered["District"].astype(str).str.strip().str.lower() == district.strip().lower()]
    if market:
        filtered = filtered[filtered["Market"].astype(str).str.strip().str.lower() == market.strip().lower()]
    if commodity:
        filtered = filtered[filtered["Commodity"].astype(str).str.strip().str.lower() == commodity.strip().lower()]

    res = sorted(filtered["Variety"].dropna().astype(str).str.strip().unique().tolist())
    if not res and commodity:
        res = sorted(
            price_data[price_data["Commodity"].astype(str).str.strip().str.lower() == commodity.strip().lower()]["Variety"]
            .dropna().astype(str).str.strip().unique().tolist()
        )
    if not res:
        res = sorted(price_data["Variety"].dropna().astype(str).str.strip().unique().tolist())
    if not res:
        res = ["Standard Variety", "Hybrid", "Average (Whole)", "FAQ", "Other"]

    return res


@app.get("/varieties")
def get_varieties_query(state: str = None, district: str = None, market: str = None, commodity: str = None):
    return _fetch_varieties(state, district, market, commodity)


@app.get("/varieties/{state}/{district}/{market}/{commodity}")
def get_varieties_path(state: str, district: str, market: str, commodity: str):
    return _fetch_varieties(state, district, market, commodity)


# =========================================================
# GET GRADES
# =========================================================

def _fetch_grades(state: str = None, district: str = None, market: str = None, commodity: str = None, variety: str = None):
    if price_data.empty:
        return ["FAQ", "Non-FAQ", "Medium", "Large", "Small"]

    filtered = price_data.copy()
    if state:
        st_clean = state.strip().lower()
        st_target = STATE_ALIASES.get(st_clean, st_clean)
        filtered = filtered[filtered["State"].astype(str).str.strip().str.lower() == st_target]
    if district:
        filtered = filtered[filtered["District"].astype(str).str.strip().str.lower() == district.strip().lower()]
    if market:
        filtered = filtered[filtered["Market"].astype(str).str.strip().str.lower() == market.strip().lower()]
    if commodity:
        filtered = filtered[filtered["Commodity"].astype(str).str.strip().str.lower() == commodity.strip().lower()]
    if variety:
        filtered = filtered[filtered["Variety"].astype(str).str.strip().str.lower() == variety.strip().lower()]

    res = sorted(filtered["Grade"].dropna().astype(str).str.strip().unique().tolist())
    if not res and variety:
        res = sorted(
            price_data[price_data["Variety"].astype(str).str.strip().str.lower() == variety.strip().lower()]["Grade"]
            .dropna().astype(str).str.strip().unique().tolist()
        )
    if not res:
        res = sorted(price_data["Grade"].dropna().astype(str).str.strip().unique().tolist())
    if not res:
        res = ["FAQ", "Non-FAQ", "Medium", "Large", "Small"]

    return res


@app.get("/grades")
def get_grades_query(state: str = None, district: str = None, market: str = None, commodity: str = None, variety: str = None):
    return _fetch_grades(state, district, market, commodity, variety)


@app.get("/grades/{state}/{district}/{market}/{commodity}/{variety}")
def get_grades_path(state: str, district: str, market: str, commodity: str, variety: str):
    return _fetch_grades(state, district, market, commodity, variety)


# =========================================================
# GET YIELD OPTIONS
# =========================================================

@app.get("/yield-options")
def get_yield_options():

    crops = []
    seasons = []
    states = []

    if yield_model is not None:
        try:
            cat_encoder = yield_model.named_steps["preprocessor"].named_transformers_["cat"]
            cats = cat_encoder.categories_
            crops = [str(c).strip() for c in cats[0]]
            seasons = [str(s).strip() for s in cats[1]]
            states = [str(st).strip() for st in cats[2]]
        except Exception:
            pass

    return {
        "crops": sorted(list(set(crops))),
        "seasons": sorted(list(set(seasons))),
        "states": sorted(list(set(states)))
    }