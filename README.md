# AutoNation Vehicle Appraisal Demo

AI-powered vehicle appraisal system using Google ADK, Gemini, and BigQuery to improve trade-in win rates.

## Features

- **🖼️ Multimodal Vision Analysis**: Upload vehicle photos and let Gemini detect damage, aftermarket mods, and estimate reconditioning costs
- **📊 Real-Time Market Intelligence**: Instant comparable vehicle pricing from KBB, CarGurus, and local dealers
- **🤖 AI-Powered Pricing**: Gemini analyzes market data and provides transparent pricing recommendations with confidence scores
- **📈 Win Rate Prediction** (v1.1): BigQuery ML model predicts probability of winning trade at different price points

## Architecture

The system uses **Google ADK (Agent Development Kit)** to orchestrate three specialized agents:

1. **Market Intelligence Agent** (gemini-2.5-flash) - Aggregates comparable vehicle data
2. **Vision Analyst Agent** (gemini-2.5-pro) - Analyzes photos to assess condition
3. **Pricing Strategist Agent** (gemini-2.5-pro) - Generates optimal offer with reasoning

## Tech Stack

- **Orchestration**: Google ADK (Agent Development Kit)
- **LLMs**: Gemini 2.5 Pro, Gemini 2.5 Flash
- **Data**: BigQuery (historical trades, market comps)
- **Storage**: Cloud Storage (vehicle photos)
- **Frontend**: Streamlit
- **Deployment**: Cloud Run
- **APIs**: KBB ICO, CarGurus, Google Maps

## Prerequisites

- Python 3.10+
- Google Cloud Platform account
- GCP Project ID: `uppdemos` (with APIs enabled)
- Service account with permissions:
  - Vertex AI User
  - BigQuery Data Editor
  - Storage Object Admin

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd autonation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
- `GCP_PROJECT_ID=uppdemos`
- `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json`
- Set API keys to `MOCK` for development without real APIs

### 3. Generate Synthetic Data (Optional for Demo)

```bash
# Generate 10K synthetic historical trades
python scripts/generate_synthetic_data.py

# Load data to BigQuery
python scripts/load_to_bigquery.py
```

### 4. Run Streamlit App

```bash
streamlit run ui/streamlit_app.py
```

The app will open at `http://localhost:8501`

## Usage

1. **Enter VIN**: Input a vehicle identification number (use demo VINs for testing)
2. **Upload Photos**: Add 4-8 vehicle images (exterior, interior, wheels, engine bay)
3. **Get Results**: System analyzes and returns:
   - Market comparables with pricing
   - AI-detected condition issues
   - Recommended offer price with reasoning
   - Confidence score

## Demo VINs

For testing, use these pre-configured demo VINs:

| VIN | Description | Expected Result |
|-----|-------------|-----------------|
| `VIN_001_WINNER` | Clean vehicle with aftermarket wheels | High-value offer, 89% win rate |
| `VIN_002_LOSS` | Subtle damage that static tools miss | Shows AI vision advantage |
| `VIN_003_GEOARB` | High regional demand variance | Geo-arbitrage insight |
| `VIN_004_HIGHRECON` | Heavy damage requiring repair | Adjusted offer for recon costs |
| `VIN_005_FASTMOVER` | Popular trim, low mileage | Aggressive offer recommended |

## Project Structure

```
autonation/
├── claude.md                 # Project context and design docs
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── agents/                  # ADK agent implementations
│   ├── market_intelligence.py
│   ├── vision_analyst.py
│   └── pricing_strategist.py
├── tools/                   # Custom tools for agents
│   ├── api_mocks.py        # Mock API responses
│   └── bigquery_tools.py   # BigQuery utilities
├── workflows/              # ADK workflows
│   └── appraisal_workflow.py
├── ui/                     # Streamlit frontend
│   └── streamlit_app.py
├── data/                   # Demo and synthetic data
│   ├── demo_vins.csv
│   └── sample_photos/
├── scripts/                # Utility scripts
│   ├── generate_synthetic_data.py
│   └── load_to_bigquery.py
└── tests/                  # Test cases
    ├── test_agents.py
    ├── test_workflow.py
    └── test_ui.py
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=tools --cov=workflows

# Run specific test file
pytest tests/test_agents.py -v
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 agents/ tools/ workflows/

# Type checking
mypy agents/ tools/ workflows/
```

## Deployment to Cloud Run

### 1. Build Docker Image

```bash
# Build image
docker build -t gcr.io/uppdemos/autonation-appraisal:latest .

# Test locally
docker run -p 8501:8501 \
  -e GCP_PROJECT_ID=uppdemos \
  gcr.io/uppdemos/autonation-appraisal:latest
```

### 2. Push to Container Registry

```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Push image
docker push gcr.io/uppdemos/autonation-appraisal:latest
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy autonation-appraisal \
  --image gcr.io/uppdemos/autonation-appraisal:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=uppdemos
```

## API Integration

### Mock Mode (Default for Development)

Set API keys to `MOCK` in `.env`:
```
KBB_API_KEY=MOCK
CARGURUS_API_KEY=MOCK
```

The system will use pre-cached demo data for fast, reliable demos.

### Live API Mode

1. Obtain API keys from KBB and CarGurus
2. Update `.env` with real credentials
3. System will make live API calls for current market data

## Synthetic Data Generation

The demo includes scripts to generate realistic synthetic data:

### Historical Trades (10,000 records)
```python
python scripts/generate_synthetic_data.py --trades 10000
```

Generates:
- Realistic VINs, make/model/year distributions
- Market prices with regional variance
- Win/loss outcomes based on offer competitiveness
- Days-to-sale and profit margins

### Market Comparables (5 Demo VINs)
Pre-cached comparable listings for fast demo performance without API latency.

## Troubleshooting

### Authentication Errors
```bash
# Set application default credentials
gcloud auth application-default login

# Or export service account path
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### BigQuery Permission Denied
```bash
# Grant necessary roles
gcloud projects add-iam-policy-binding uppdemos \
  --member="serviceAccount:YOUR-SA@uppdemos.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

### Streamlit Connection Issues
- Check firewall settings
- Ensure port 8501 is available
- Verify `.env` configuration

## Roadmap

### MVP v1.0 (Current)
- [x] Market Intelligence Agent
- [x] Vision Analyst Agent
- [x] Pricing Strategist Agent
- [x] Streamlit UI
- [x] Mock API integration

### v1.1 (Next)
- [ ] BigQuery ML win rate predictor
- [ ] RAG for reconditioning cost estimation
- [ ] Real-time API integration (KBB, CarGurus)
- [ ] Geo-arbitrage with Google Maps

### v1.2 (Future)
- [ ] Multi-region deployment
- [ ] A/B testing framework
- [ ] Performance analytics dashboard
- [ ] Batch appraisal mode

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `pytest`
3. Format code: `black .`
4. Commit changes: `git commit -m "Add feature"`
5. Push to GitHub/GitLab
6. Create pull request

## License

Proprietary - AutoNation Demo Project

## Contact

For questions or support, contact the development team.

---

**Note**: This is a demo/prototype. For production use, add:
- Authentication/authorization
- Rate limiting
- Comprehensive error handling
- Monitoring and logging
- Data privacy compliance
- API key rotation
