const API_BASE_URL = 'http://127.0.0.1:8000';

let priceChart = null;

// =========================================================
// INITIALIZATION
// =========================================================

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  checkServerHealth();
  loadYieldDropdowns();
  loadPriceStates();
  setupFormListeners();
  
  // Set default prediction date to today
  const today = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById('price-date');
  if (dateInput) dateInput.value = today;
});

// =========================================================
// TAB NAVIGATION
// =========================================================

function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(target).classList.add('active');
    });
  });
}

// =========================================================
// SERVER HEALTH CHECK
// =========================================================

async function checkServerHealth() {
  const statusBadge = document.getElementById('server-status-badge');
  const statusText = document.getElementById('server-status-text');

  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('API server unreachable');
    
    const data = await response.json();
    statusBadge.style.display = 'flex';
    statusText.textContent = 'API Connected (FastAPI v1.0)';
    
    // Update stats banner
    document.getElementById('stat-yield-status').textContent = data.yield_model === 'loaded' ? 'Active' : 'Offline';
    document.getElementById('stat-price-status').textContent = data.price_model === 'loaded' ? 'Active' : 'Offline';
    
    const homeRes = await fetch(`${API_BASE_URL}/`);
    const homeData = await homeRes.json();
    document.getElementById('stat-records-count').textContent = (homeData.historical_price_rows || 2733).toLocaleString();

  } catch (err) {
    statusText.textContent = 'API Offline';
    statusBadge.style.background = 'rgba(239, 68, 68, 0.15)';
    statusBadge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    statusBadge.style.color = '#f87171';
    showToast('Failed to connect to backend server at http://127.0.0.1:8000', 'error');
  }
}

// =========================================================
// YIELD FORM DROPDOWNS
// =========================================================

async function loadYieldDropdowns() {
  try {
    const res = await fetch(`${API_BASE_URL}/yield-options`);
    const data = await res.json();

    populateSelect('yield-crop', data.crops || [], 'Select Crop');
    populateSelect('yield-season', data.seasons || [], 'Select Season');
    populateSelect('yield-state', data.states || [], 'Select State');
  } catch (err) {
    console.error('Error loading yield options:', err);
  }
}

// =========================================================
// PRICE FORM CASCADING DROPDOWNS
// =========================================================

async function loadPriceStates() {
  try {
    const res = await fetch(`${API_BASE_URL}/states`);
    const states = await res.json();
    populateSelect('price-state', states, 'Select State');
  } catch (err) {
    console.error('Error loading states:', err);
  }
}

function setupFormListeners() {
  // Cascading dropdown for Crop Yield Predictor State -> District
  const yieldStateSelect = document.getElementById('yield-state');
  const yieldDistrictSelect = document.getElementById('yield-district');
  if (yieldStateSelect && yieldDistrictSelect) {
    yieldStateSelect.addEventListener('change', async () => {
      const state = yieldStateSelect.value;
      resetSelect(yieldDistrictSelect, 'Select District');
      if (!state) return;
      try {
        const res = await fetch(`${API_BASE_URL}/districts/${encodeURIComponent(state)}`);
        const districts = await res.json();
        populateSelect('yield-district', districts, 'Select District');
      } catch (err) {
        console.error('Error fetching districts for yield form:', err);
      }
    });
  }

  // Cascading dropdowns for price predictor
  const stateSelect = document.getElementById('price-state');
  const districtSelect = document.getElementById('price-district');
  const marketSelect = document.getElementById('price-market');
  const commoditySelect = document.getElementById('price-commodity');
  const varietySelect = document.getElementById('price-variety');

  stateSelect.addEventListener('change', async () => {
    const state = stateSelect.value;
    resetSelect(districtSelect, 'Select District');
    resetSelect(marketSelect, 'Select Market');
    resetSelect(commoditySelect, 'Select Commodity');
    resetSelect(varietySelect, 'Select Variety');
    resetSelect(document.getElementById('price-grade'), 'Select Grade');

    if (!state) return;
    const res = await fetch(`${API_BASE_URL}/districts/${encodeURIComponent(state)}`);
    const districts = await res.json();
    populateSelect('price-district', districts, 'Select District');
  });

  districtSelect.addEventListener('change', async () => {
    const state = stateSelect.value;
    const district = districtSelect.value;
    resetSelect(marketSelect, 'Select Market');
    resetSelect(commoditySelect, 'Select Commodity');
    resetSelect(varietySelect, 'Select Variety');
    resetSelect(document.getElementById('price-grade'), 'Select Grade');

    if (!district) return;
    const res = await fetch(`${API_BASE_URL}/markets/${encodeURIComponent(state)}/${encodeURIComponent(district)}`);
    const markets = await res.json();
    populateSelect('price-market', markets, 'Select Market');
  });

  marketSelect.addEventListener('change', async () => {
    const state = stateSelect.value;
    const district = districtSelect.value;
    const market = marketSelect.value;

    resetSelect(commoditySelect, 'Select Commodity');
    resetSelect(varietySelect, 'Select Variety');
    resetSelect(document.getElementById('price-grade'), 'Select Grade');

    if (!market) return;
    const url = `${API_BASE_URL}/commodities?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}&market=${encodeURIComponent(market)}`;
    const res = await fetch(url);
    const commodities = await res.json();
    populateSelect('price-commodity', commodities, 'Select Commodity');
  });

  commoditySelect.addEventListener('change', async () => {
    const state = stateSelect.value;
    const district = districtSelect.value;
    const market = marketSelect.value;
    const commodity = commoditySelect.value;

    resetSelect(varietySelect, 'Select Variety');
    resetSelect(document.getElementById('price-grade'), 'Select Grade');

    if (!commodity) return;
    const url = `${API_BASE_URL}/varieties?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}&market=${encodeURIComponent(market)}&commodity=${encodeURIComponent(commodity)}`;
    const res = await fetch(url);
    const varieties = await res.json();
    populateSelect('price-variety', varieties, 'Select Variety');

    // Auto-select first variety if available and trigger grade loading
    if (varieties && varieties.length > 0) {
      varietySelect.value = varieties[0];
      varietySelect.dispatchEvent(new Event('change'));
    }
  });

  varietySelect.addEventListener('change', async () => {
    const state = stateSelect.value;
    const district = districtSelect.value;
    const market = marketSelect.value;
    const commodity = commoditySelect.value;
    const variety = varietySelect.value;
    const gradeSelect = document.getElementById('price-grade');

    resetSelect(gradeSelect, 'Select Grade');

    if (!variety) return;
    const url = `${API_BASE_URL}/grades?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}&market=${encodeURIComponent(market)}&commodity=${encodeURIComponent(commodity)}&variety=${encodeURIComponent(variety)}`;
    const res = await fetch(url);
    const grades = await res.json();
    populateSelect('price-grade', grades, 'Select Grade');

    // Auto-select first grade if available
    if (grades && grades.length > 0) {
      gradeSelect.value = grades[0];
    }
  });

  // Submit Forms
  document.getElementById('yield-form').addEventListener('submit', handleYieldSubmit);
  document.getElementById('price-form').addEventListener('submit', handlePriceSubmit);
}

// =========================================================
// PREDICTION HANDLERS
// =========================================================

async function handleYieldSubmit(e) {
  e.preventDefault();

  const payload = {
    Crop: document.getElementById('yield-crop').value,
    Crop_Year: parseInt(document.getElementById('yield-year').value),
    Season: document.getElementById('yield-season').value,
    State: document.getElementById('yield-state').value,
    District: document.getElementById('yield-district').value,
    Area: parseFloat(document.getElementById('yield-area').value),
    Fertilizer: parseFloat(document.getElementById('yield-fertilizer').value),
    Pesticide: parseFloat(document.getElementById('yield-pesticide').value)
  };

  const submitBtn = document.getElementById('yield-submit-btn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span>Calculating...</span>';

  try {
    const res = await fetch(`${API_BASE_URL}/predict-yield`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Yield prediction failed');

    displayYieldResult(data, payload);
    showToast('Yield Prediction Calculated Successfully!');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span>🚀 Predict Crop Yield</span>';
  }
}

function displayYieldResult(data, payload) {
  const container = document.getElementById('yield-result-container');
  const yieldPerAcre = data.predicted_yield_per_acre ?? (data.predicted_yield ? Number((data.predicted_yield * 0.404686).toFixed(2)) : 0);
  const areaAcres = payload.Area;
  const totalProduction = (data.total_production_tons ?? Number((yieldPerAcre * areaAcres).toFixed(2))).toLocaleString(undefined, { maximumFractionDigits: 2 });
  const rainfallUsed = data.annual_rainfall_used || 0;
  const rainfallSource = data.rainfall_source || 'Calculated';

  const formattedYield = yieldPerAcre.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  container.innerHTML = `
    <div class="prediction-output-box">
      <div class="result-label">Predicted Yield Rate</div>
      <div class="result-value-big">${formattedYield}</div>
      <div class="result-unit">Metric Tons per Acre (t/acre)</div>
    </div>
    
    <div class="metrics-breakdown">
      <div class="metric-item">
        <div class="metric-item-label">Total Cultivated Area</div>
        <div class="metric-item-val">${areaAcres} Acres</div>
      </div>
      <div class="metric-item">
        <div class="metric-item-label">Est. Total Production (${areaAcres} Acres)</div>
        <div class="metric-item-val" style="color: #34d399;">${totalProduction} Tons</div>
      </div>
      <div class="metric-item">
        <div class="metric-item-label">Annual Rainfall Used</div>
        <div class="metric-item-val" style="color: #38bdf8;">${rainfallUsed} mm</div>
        <div style="font-size: 0.72rem; color: #8e9b97; margin-top: 2px;">${rainfallSource}</div>
      </div>
    </div>
  `;
}

async function handlePriceSubmit(e) {
  e.preventDefault();

  const payload = {
    State: document.getElementById('price-state').value,
    District: document.getElementById('price-district').value,
    Market: document.getElementById('price-market').value,
    Commodity: document.getElementById('price-commodity').value,
    Variety: document.getElementById('price-variety').value,
    Grade: document.getElementById('price-grade').value,
    Prediction_Date: document.getElementById('price-date').value
  };

  const submitBtn = document.getElementById('price-submit-btn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span>Forecasting Price...</span>';

  try {
    const res = await fetch(`${API_BASE_URL}/predict-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Price prediction failed');

    displayPriceResult(data, payload);
    showToast('Market Price Forecasted Successfully!');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span>📈 Forecast Market Price</span>';
  }
}

function displayPriceResult(data, payload) {
  const container = document.getElementById('price-result-container');
  const priceVal = data.predicted_price || 0;
  const features = data.historical_features || {};

  container.innerHTML = `
    <div class="prediction-output-box prediction-output-amber">
      <div class="result-label">Predicted Market Price</div>
      <div class="result-value-big" style="color: #fbbf24;">₹ ${priceVal.toLocaleString()}</div>
      <div class="result-unit result-unit-amber">Rs. per Quintal (${payload.Commodity})</div>
    </div>

    <div class="metrics-breakdown">
      <div class="metric-item">
        <div class="metric-item-label">Prev. Day Price</div>
        <div class="metric-item-val">₹ ${(features.previous_price || 0).toLocaleString()}</div>
      </div>
      <div class="metric-item">
        <div class="metric-item-label">7-Day Prev. Price</div>
        <div class="metric-item-val">₹ ${(features.seventh_previous_price || 0).toLocaleString()}</div>
      </div>
      <div class="metric-item">
        <div class="metric-item-label">7-Day Avg. Price</div>
        <div class="metric-item-val" style="color: #fbbf24;">₹ ${(features.seven_price_average || 0).toLocaleString()}</div>
      </div>
    </div>

    <div class="chart-container">
      <canvas id="priceTrendChart"></canvas>
    </div>
  `;

  renderPriceChart(features, priceVal, payload.Prediction_Date);
}

function renderPriceChart(features, predictedPrice, targetDate) {
  const ctx = document.getElementById('priceTrendChart');
  if (!ctx) return;

  if (priceChart) priceChart.destroy();

  const labels = ['7 Days Ago', 'Prev Day', '7-Day Avg', `Target (${targetDate})` ];
  const datasetValues = [
    features.seventh_previous_price || 0,
    features.previous_price || 0,
    features.seven_price_average || 0,
    predictedPrice
  ];

  priceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Price Trajectory (Rs./Quintal)',
        data: datasetValues,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.15)',
        borderWidth: 3,
        pointBackgroundColor: ['#d97706', '#d97706', '#f59e0b', '#10b981'],
        pointRadius: 6,
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#8e9b97', font: { family: 'Inter' } } }
      },
      scales: {
        x: { ticks: { color: '#8e9b97' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#8e9b97' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

// =========================================================
// UTILS
// =========================================================

function populateSelect(elementId, items, placeholder = null) {
  const select = document.getElementById(elementId);
  if (!select) return;
  
  select.innerHTML = '';
  if (placeholder) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = placeholder;
    select.appendChild(opt);
  }

  items.forEach(item => {
    const opt = document.createElement('option');
    opt.value = item;
    opt.textContent = item;
    select.appendChild(opt);
  });
}

function resetSelect(selectElement, placeholder) {
  if (!selectElement) return;
  selectElement.innerHTML = `<option value="">${placeholder}</option>`;
}

function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type === 'error' ? 'toast-error' : ''}`;
  toast.innerHTML = `
    <span>${type === 'error' ? '❌' : '✅'}</span>
    <div>${message}</div>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}
