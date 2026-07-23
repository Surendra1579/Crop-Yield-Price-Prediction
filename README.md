# 🌾 AI-Powered Crop Yield & Commodity Price Prediction System

An intelligent Machine Learning-based web application designed to predict **crop yield** and forecast **agricultural commodity prices** using historical, environmental, and market data.

The system combines Machine Learning models with a **FastAPI backend** and a modern **React.js frontend** to provide farmers, agricultural stakeholders, researchers, and market analysts with useful data-driven insights.

---

## 📌 Project Overview

Agriculture is highly influenced by environmental conditions, crop characteristics, and fluctuating market prices. Accurate crop yield estimation and commodity price prediction can help support better agricultural planning and decision-making.

This project provides two major prediction modules:

### 🌱 Crop Yield Prediction

Predicts expected crop yield based on agricultural and environmental factors such as:

- State
- District
- Crop
- Crop Year
- Season
- Cultivated Area
- Annual Rainfall
- Fertilizer Usage
- Pesticide Usage

The system is designed to automatically determine rainfall information based on the selected location, reducing the need for manual rainfall input.

### 📈 Commodity Price Prediction

Predicts agricultural commodity prices using historical market data and time-series features such as:

- State
- District
- Market
- Commodity
- Variety
- Grade
- Historical Modal Price
- Previous Price Trends
- Lag Features
- Rolling Average Features
- Target Prediction Date

---

## ✨ Key Features

- 🌾 Machine Learning-based Crop Yield Prediction
- 📈 Agricultural Commodity Price Prediction
- 🌧️ Automatic location-based rainfall integration
- 📍 State, district, and market-based predictions
- 🏷️ Commodity variety and grade selection
- 📊 Historical price trend analysis
- 🕒 Time-series feature engineering for price prediction
- ⚡ FastAPI-powered prediction APIs
- 💻 Interactive React.js frontend
- 🔄 Frontend and backend API integration
- 🤖 Trained ML models for real-time predictions
- 🎯 Data-driven agricultural insights

---

## 🛠️ Tech Stack

### Frontend

- React.js
- JavaScript
- HTML5
- CSS3

### Backend

- Python
- FastAPI
- Uvicorn

### Machine Learning & Data Processing

- Scikit-learn
- Pandas
- NumPy
- Joblib

### ML Techniques

- Regression Algorithms
- Data Preprocessing
- Feature Engineering
- Categorical Encoding
- Time-Series Features
- Lag Features
- Rolling Mean Features

### Deployment

- Render – Backend deployment
- Netlify / Vercel – Frontend deployment

---

## 🏗️ System Architecture

```text
                 ┌─────────────────────┐
                 │      User Input     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   React.js Frontend │
                 └──────────┬──────────┘
                            │
                       REST API
                            │
                            ▼
                 ┌─────────────────────┐
                 │   FastAPI Backend   │
                 └──────────┬──────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
     ┌─────────────────┐        ┌─────────────────┐
     │   Crop Yield    │        │ Commodity Price │
     │ Prediction Model│        │ Prediction Model│
     └────────┬────────┘        └────────┬────────┘
              │                          │
              ▼                          ▼
     ┌─────────────────┐        ┌─────────────────┐
     │ Predicted Yield │        │ Predicted Price │
     └─────────────────┘        └─────────────────┘
```

---

## 🌧️ Automatic Rainfall Integration

Instead of requiring users to manually enter annual rainfall, the system can automatically obtain rainfall information based on the selected:

```text
State
  ↓
District
  ↓
Location Identification
  ↓
Rainfall Data Retrieval
  ↓
Annual Rainfall Calculation
  ↓
Crop Yield ML Model
  ↓
Yield Prediction
```

This improves the user experience and reduces manual data entry.

> **Note:** The rainfall value supplied to the model should follow the same unit, scale, and definition used in the model's training dataset.

---

## 📊 Machine Learning Workflow

```text
Dataset Collection
        ↓
Data Cleaning
        ↓
Data Preprocessing
        ↓
Exploratory Data Analysis
        ↓
Feature Engineering
        ↓
Train-Test Split
        ↓
Model Training
        ↓
Model Evaluation
        ↓
Best Model Selection
        ↓
Model Serialization (.pkl)
        ↓
FastAPI Integration
        ↓
React Frontend
        ↓
Prediction Results
```

---

## 📈 Commodity Price Feature Engineering

The commodity price prediction model can use historical price patterns through features such as:

```text
Price_Lag_1
Price_Lag_7
Price_Lag_14
Price_Lag_30
Rolling_Mean_7
Rolling_Mean_14
Rolling_Mean_30
Month
Day
Day_of_Week
```

These features help the model understand historical price movements and market trends.

---

## 📂 Project Structure

```text
crop-yield-price-prediction/
│
├── backend/
│   ├── data/
│   │   └── datasets/
│   │
│   ├── models/
│   │   ├── crop_yield_model.pkl
│   │   └── crop_price_model.pkl
│   │
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   │
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   └── package.json
│
└── README.md
```

> The actual folder structure may vary depending on the implementation.

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.x
- Node.js
- npm
- Git

---

## 1️⃣ Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd crop-yield-price-prediction
```

---

## 2️⃣ Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
python -m uvicorn main:app --reload
```

The backend will normally run at:

```text
http://127.0.0.1:8000
```

FastAPI API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

---

## 3️⃣ Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL displayed in the terminal.

---

## 🔌 API Integration

The React frontend communicates with the FastAPI backend using REST API requests.

Example prediction flow:

```text
User Input
    ↓
React Frontend
    ↓
HTTP Request
    ↓
FastAPI Endpoint
    ↓
Data Preprocessing
    ↓
Trained ML Model
    ↓
Prediction
    ↓
JSON Response
    ↓
Result Displayed to User
```

---

## 📊 Model Evaluation

The models can be evaluated using regression metrics such as:

- MAE – Mean Absolute Error
- RMSE – Root Mean Squared Error
- R² Score

Example commodity price model results obtained during development:

| Metric | Score |
|---|---:|
| MAE | 250.43 |
| RMSE | 571.43 |
| R² Score | 0.9576 |

> Model performance can vary depending on the dataset, validation strategy, prediction horizon, and unseen market conditions.

---

## 🖼️ Screenshots

Add your application screenshots here.

### Home Page

```text
Add screenshot here
```

### Crop Yield Prediction

```text
Add screenshot here
```

### Commodity Price Prediction

```text
Add screenshot here
```

---

## 🔮 Future Enhancements

- 🌦️ Real-time and historical weather data integration
- 🌧️ Automated rainfall calculation
- 🌡️ Temperature and humidity integration
- 🛰️ Satellite-based agricultural data integration
- 🧪 Soil health and soil type analysis
- 📊 Interactive agricultural analytics dashboard
- 📉 Advanced time-series forecasting
- 🤖 Improved ML models with hyperparameter optimization
- 🗺️ Location-based crop recommendations
- 📱 Mobile-responsive interface
- 🌐 Multi-language support for farmers

---

## ⚠️ Disclaimer

The predictions generated by this application are based on historical data and Machine Learning models. Actual crop yields and commodity prices may vary due to weather conditions, market fluctuations, government policies, supply and demand, natural disasters, and other external factors.

The predictions should be considered as decision-support information and not as guaranteed outcomes.

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository.
2. Create a new feature branch.
3. Make your changes.
4. Commit your changes.
5. Push the branch.
6. Create a Pull Request.

---

## 👨‍💻 Author

**Kommalapati Naga Surendra**

B.Tech – Artificial Intelligence & Machine Learning

---

## ⭐ Support

If you find this project useful, consider giving the repository a **⭐ Star** on GitHub.

Your support helps encourage further improvements and development.
