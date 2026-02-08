# AutoNation Vehicle Appraisal Demo - Project Context

## Project Overview
AI-powered vehicle appraisal system to improve AutoNation's trade-in win rate by providing:
- Real-time market intelligence (eliminate 2-day timing gap)
- Multimodal vision analysis of vehicle photos
- Gemini-powered pricing recommendations with transparent reasoning

## Business Problem
AutoNation needs competitive trade-in offers to win against CarMax, Carvana, etc. Better vehicle condition assessment + faster market intelligence = higher win rates and profitability.

## Key Differentiators (MVP v1.0)
1. **Multimodal Vision AI** ⭐ - Detects aftermarket mods and damage that static tools (Inventory Plus) miss
2. **Real-Time Market Intelligence** - Instant side-by-side comparison from KBB, CarGurus, local dealers
3. **Transparent AI Reasoning** - Gemini explains every pricing decision with confidence scores

## Tech Stack
- **GCP Project ID**: `uppdemos` (APIs already enabled)
- **Region**: `us-central1` (standard), `global` (for Gemini 3 models)
- **Orchestration**: Google ADK (Agent Development Kit) - use ADK prototyping skill
- **LLM Models**:
  - `gemini-2.5-pro`: Pricing strategist (complex reasoning) + Vision analyst (multimodal)
  - `gemini-2.5-flash`: Market intelligence agent (speed)
  - `gemini-3-flash-preview`: Future upgrade (global endpoint only)
  - `gemini-2.5-flash-image`: Image generation (if needed)
- **Data Warehouse**: BigQuery (historical trades, market comps)
- **Storage**: Cloud Storage (vehicle photos)
- **Frontend**: Streamlit
- **Deployment**: Cloud Run
- **External APIs**:
  - KBB ICO API (Instant Cash Offer)
  - CarGurus API
  - Google Maps Platform API (geo-arbitrage)

---

## MVP v1.0 Features (Priority Order)

### 1. Multimodal Vision Analysis (HIGHEST VALUE)
- **Input**: 4-8 vehicle photos (exterior, interior, wheels, engine bay)
- **Processing**: Gemini 2.5 Pro vision model
- **Output**:
  - Condition grade (Excellent/Good/Fair/Poor)
  - Detected issues (scratches, dents, stains, rust)
  - Aftermarket modifications (wheels, audio, tint, spoilers)
  - Estimated reconditioning cost breakdown
- **Model**: `gemini-2.5-pro` (multimodal capabilities)

### 2. Market Intelligence Agent
- **Input**: VIN + zip code
- **Processing**: Query APIs (mock initially) + filter outliers
- **Output**:
  - 5-10 comparable vehicles with prices
  - Side-by-side comparison table
  - Market summary (avg price, range)
- **Model**: `gemini-2.5-flash` (fast execution)
- **APIs**: KBB, CarGurus, local dealer scraping

### 3. Pricing Strategist Agent
- **Input**: Market data + condition assessment
- **Processing**: Gemini analyzes and generates optimal offer
- **Output**:
  - Recommended offer price
  - Natural language reasoning (why this price?)
  - Confidence score (0-100%)
  - Risk factors
  - Expected profit margin
- **Model**: `gemini-2.5-pro` (complex reasoning)

### 4. Win Rate Predictor (v1.1 - NICE TO HAVE)
- **Note**: Requires real historical data collection first
- **Future**: BigQuery ML model for probability curves

---

## Architecture

```
┌─────────────────────────────────────┐
│  Streamlit Frontend (Cloud Run)      │
│  - VIN Input                         │
│  - Photo Upload (4-8 images)         │
│  - Results Dashboard (3 tabs)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   ADK Sequential Workflow            │
├──────────────────────────────────────┤
│                                      │
│  Agent 1: Market Intelligence        │
│  - Model: gemini-2.5-flash           │
│  - Tools: mock_kbb_api()             │
│  - Tools: mock_cargurus_api()        │
│  - Output: Market comparables        │
│                                      │
│  Agent 2: Vision Analyst             │
│  - Model: gemini-2.5-pro (vision)    │
│  - Input: 4-8 photos                 │
│  - Output: Condition + recon cost    │
│                                      │
│  Agent 3: Pricing Strategist         │
│  - Model: gemini-2.5-pro             │
│  - Input: Market + condition         │
│  - Output: Offer + reasoning         │
│                                      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Data Layer (GCP)              │
│  - BigQuery: historical_trades       │
│  - BigQuery: market_comps (cached)   │
│  - Cloud Storage: vehicle photos     │
└──────────────────────────────────────┘
```

---

## Directory Structure
```
autonation/
├── claude.md                      # This file - project context
├── README.md                      # Setup instructions
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore
├── Dockerfile                     # For Cloud Run deployment
│
├── agents/                        # ADK Agent implementations
│   ├── __init__.py
│   ├── market_intelligence.py    # Agent 1
│   ├── vision_analyst.py         # Agent 2
│   └── pricing_strategist.py     # Agent 3
│
├── tools/                         # Custom tools for agents
│   ├── __init__.py
│   ├── api_mocks.py              # Mock KBB/CarGurus APIs
│   └── bigquery_tools.py         # BigQuery helper functions
│
├── workflows/                     # ADK workflows
│   ├── __init__.py
│   └── appraisal_workflow.py     # Main Sequential Workflow
│
├── ui/                           # Frontend
│   └── streamlit_app.py          # Streamlit interface
│
├── data/                         # Demo and synthetic data
│   ├── demo_vins.csv             # 5 curated demo VINs with stories
│   ├── synthetic_trades.csv      # 10K synthetic historical trades
│   ├── mock_market_comps.json    # Cached market data for demo
│   └── sample_photos/            # Sample vehicle images
│       ├── vin_001/              # 6 photos for demo VIN 1
│       ├── vin_002/
│       └── ...
│
└── scripts/                      # Utility scripts
    ├── generate_synthetic_data.py   # Create fake historical data
    └── load_to_bigquery.py          # Upload data to BQ
```

---

## Synthetic Data Requirements

### 1. Historical Trades Data (10,000 records)
**Purpose**: Provide historical context for pricing decisions

**Fields**:
- `trade_id`: Unique identifier
- `vin`: Vehicle Identification Number
- `make`: Honda, Toyota, Ford, Chevrolet, etc.
- `model`: Accord, Camry, F-150, etc.
- `year`: 2018-2024
- `trim`: EX, LX, Sport, etc.
- `mileage`: 15,000 - 120,000
- `offer_price`: What AutoNation offered
- `market_price`: Market value at time of appraisal
- `competitor_best_offer`: Best competing offer (CarMax/Carvana)
- `won_trade`: Boolean (did customer accept?)
- `days_to_sale`: Time to resell (if won)
- `final_sale_price`: Resale price
- `region`: Southeast, Northeast, Southwest, etc.
- `appraisal_date`: Date of appraisal

**Generation Logic**:
```python
# Realistic win probability based on offer competitiveness
market_price = random(15000, 45000)
offer_price = market_price * random(0.85, 0.98)  # 85-98% of market
price_gap = market_price - offer_price

# Win rate increases as gap decreases
win_probability = 1 / (1 + exp((price_gap - 1500) / 500))
won_trade = random() < win_probability
```

### 2. Market Comparables (Mock Data for 5 Demo VINs)
**Purpose**: Fast demo without waiting for real API calls

**Structure**:
```json
{
  "1HGBH41JXMN109186": {
    "vehicle_info": {
      "make": "Honda",
      "model": "Accord",
      "year": 2022,
      "trim": "EX-L"
    },
    "comparables": [
      {
        "source": "cargurus",
        "price": 24500,
        "mileage": 32000,
        "distance_miles": 8,
        "days_listed": 12,
        "url": "https://cargurus.com/..."
      },
      // ... 4-9 more comps
    ],
    "kbb_instant_offer": 23800,
    "market_summary": {
      "avg_price": 24750,
      "min_price": 23200,
      "max_price": 26500
    }
  }
  // ... 4 more demo VINs
}
```

### 3. Demo VIN Stories (5 Curated Scenarios)

| VIN | Story | Expected Demo Outcome |
|-----|-------|----------------------|
| **VIN_001** | "The Winner" - Clean vehicle with aftermarket wheels | Vision AI: "+$800 value from wheels"<br>Offer: $24,500<br>Win rate: 89% |
| **VIN_002** | "The Loss" - Subtle damage missed by inspectors, lost to Carvana | Vision AI: "Detected bumper scratch (-$400 recon)"<br>Shows how AI prevents losses |
| **VIN_003** | "Geo-Arbitrage" - High demand in Miami, low in Atlanta | "Worth $2,000 more in Miami region"<br>Regional pricing insight |
| **VIN_004** | "High Recon" - Heavy damage requiring $2,500 work | Vision AI: "Dent, paint fade, seat tear"<br>Recon: $2,500<br>Adjusted offer |
| **VIN_005** | "Fast Mover" - Popular trim, low mileage | "High demand - sells in 14 days avg"<br>Aggressive offer recommended |

### 4. Sample Photos (30-40 images total)
**Needed for each demo VIN**:
- 2 exterior (front 3/4, side)
- 2 interior (dashboard, seats)
- 1 wheels (show aftermarket mods)
- 1 engine bay (optional)

**Can use**:
- Stock photos from used car sites
- AI-generated vehicle images (using Imagen)
- Public domain automotive images

---

## Third-Party API Requirements

### 1. KBB ICO API (Kelley Blue Book Instant Cash Offer)
**Purpose**: Get instant market valuation

**Endpoints**:
- `GET /v1/vehicle/vin/{vin}` - Get vehicle details
- `GET /v1/valuation/instant-cash-offer` - Get ICO price

**Data Returned**:
- Instant Cash Offer price
- Trade-in value range (low/high)
- Private party value
- Retail value

**Auth**: API key required
**Pricing**: Contact KBB for enterprise pricing

**Mock Implementation for MVP**:
```python
def mock_kbb_api(vin: str) -> dict:
    return {
        "instant_cash_offer": 23800,
        "trade_in_range": {"low": 23000, "high": 25000},
        "private_party": 25500,
        "retail": 27000
    }
```

### 2. CarGurus API
**Purpose**: Get comparable listings from CarGurus marketplace

**Endpoints**:
- `GET /api/v1/listings/search` - Search by make/model/year/zip
- `GET /api/v1/listings/{id}` - Get specific listing details

**Data Returned**:
- Listing price
- Mileage
- Location/distance
- Days on market
- Listing URL
- Photos

**Auth**: API key required
**Pricing**: Enterprise/partner access required

**Mock Implementation for MVP**:
```python
def mock_cargurus_api(make: str, model: str, year: int, zip_code: str) -> dict:
    return {
        "comparables": [
            {
                "price": 24500,
                "mileage": 32000,
                "distance_miles": 8,
                "days_listed": 12,
                "url": "https://cargurus.com/listing/123"
            },
            # ... more comps
        ]
    }
```

### 3. Google Maps Platform API
**Purpose**: Geo-arbitrage analysis - regional pricing variance

**Endpoints**:
- `Geocoding API`: Convert zip codes to regions
- `Distance Matrix API`: Calculate distances between markets

**Use Case**:
```python
# Get regional pricing from BigQuery
query = """
SELECT region, AVG(final_sale_price) as avg_price
FROM historical_trades
WHERE make = 'Honda' AND model = 'Accord'
GROUP BY region
"""
# Results: Miami avg $26K, Atlanta avg $24K → $2K arbitrage opportunity
```

**Auth**: Google Cloud API key
**Pricing**: Pay-as-you-go (first $200/month free)

### 4. NADA Guides API (Optional - Alternative to KBB)
**Purpose**: Vehicle valuation (alternative data source)

**Similar to KBB**: Provides trade-in, retail, and wholesale values

### 5. AutoTrader API (Optional - Additional comps)
**Purpose**: More market comparable listings

**Similar to CarGurus**: Marketplace listings data

---

## API Integration Strategy

### Phase 1: Mock Data (Week 1)
- Use `api_mocks.py` with hardcoded responses
- Ensures fast demo without API dependencies
- All 5 demo VINs have pre-cached responses

### Phase 2: Hybrid (Week 2)
- Demo VINs use cached data
- Live VINs call real APIs
- Fallback to mock if API fails

### Phase 3: Full Integration (Week 3+)
- All requests use real APIs
- Implement caching layer (15-min TTL)
- Error handling and rate limiting

---

## Environment Variables
```bash
# GCP
GCP_PROJECT_ID=uppdemos
GCP_REGION=us-central1
BIGQUERY_DATASET=autonation_demo
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Third-Party APIs (use "MOCK" for development)
KBB_API_KEY=MOCK
KBB_API_URL=https://api.kbb.com/v1
CARGURUS_API_KEY=MOCK
CARGURUS_API_URL=https://api.cargurus.com/v1
GOOGLE_MAPS_API_KEY=your-maps-api-key

# App Config
STREAMLIT_PORT=8501
LOG_LEVEL=INFO
```

---

## Development Workflow

### Phase 1: Core MVP (This Week)
- [x] Project structure setup
- [ ] Generate synthetic historical trades data
- [ ] Create mock market comp data for 5 demo VINs
- [ ] Build Market Intelligence Agent (gemini-2.5-flash)
- [ ] Build Vision Analyst Agent (gemini-2.5-pro)
- [ ] Build Pricing Strategist Agent (gemini-2.5-pro)
- [ ] Create ADK Sequential Workflow
- [ ] Build Streamlit UI
- [ ] Local testing with 5 demo VINs

### Phase 2: Data Integration (Next Week)
- [ ] Set up BigQuery tables
- [ ] Load synthetic data to BigQuery
- [ ] Cloud Storage bucket for photos
- [ ] Test with larger dataset

### Phase 3: API Integration (Week 3)
- [ ] Integrate real KBB API (if available)
- [ ] Integrate real CarGurus API (if available)
- [ ] Google Maps geo-arbitrage

### Phase 4: Deployment
- [ ] Push to GitHub/GitLab
- [ ] Create Dockerfile
- [ ] Deploy to Cloud Run
- [ ] Test production deployment

---

## Success Metrics for Demo
- **Speed**: VIN + photos → results in <5 seconds
- **Accuracy**: Vision AI detects 3+ condition issues per vehicle
- **Reasoning**: Natural language explanation for every price
- **UI**: Clean, professional, easy to navigate

---

## Demo Script (Feb 25th)
1. **Input**: VIN "1HGBH41JXMN109186" + upload 6 photos
2. **Processing**: Show progress (Analyzing market... Analyzing photos... Generating recommendation...)
3. **Output** (3 tabs):
   - **Tab 1 - Market Intelligence**:
     - 5 comps from CarGurus/KBB
     - Avg market price: $24,750
   - **Tab 2 - Condition Analysis**:
     - AI detected: "Aftermarket wheels (+$800), minor scratches (-$400 recon)"
     - Condition grade: Good
     - Recon cost: $400
   - **Tab 3 - Pricing Recommendation**:
     - **Recommended offer: $24,500**
     - Confidence: 87%
     - Reasoning: "Market avg is $24,750. Vehicle has aftermarket wheels adding value, but requires minor paint work costing $400. Regional demand in Miami is strong..."
     - Expected profit margin: $2,100

---

## Notes
- Use **ADK prototyping skill** to create agents
- Prioritize **vision analysis** - biggest differentiator
- Keep UI simple and fast
- Mock data initially, real APIs later
- BQML win rate predictor is **nice-to-have** (requires real data collection)
