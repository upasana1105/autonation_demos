# AutoNation Appraisal System - Production Deployment Guide

## 🏗️ Deployment Architecture

```
Production Stack:
├── Vertex AI Agent Engine (3 ADK Agents)
│   ├── Market Intelligence Agent
│   ├── Vision Analyst Agent
│   └── Pricing Strategist Agent
├── Cloud Run (Streamlit UI)
├── BigQuery (Data Storage)
│   ├── market_comps table
│   ├── historical_trades table
│   └── demo_vins table
└── Cloud Storage (Photos)
    └── gs://autonation-vehicle-photos/
```

---

## 📋 Prerequisites

### 1. GCP Setup

```bash
# Set project
export GCP_PROJECT_ID="uppdemos"
export GCP_REGION="us-central1"

# Authenticate
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com
```

### 2. Create Staging Bucket

```bash
# Create bucket for Agent Engine staging
export STAGING_BUCKET="gs://autonation-staging-${GCP_PROJECT_ID}"
gsutil mb -p $GCP_PROJECT_ID -l $GCP_REGION $STAGING_BUCKET

# Create bucket for vehicle photos
gsutil mb -p $GCP_PROJECT_ID -l $GCP_REGION gs://autonation-vehicle-photos
```

### 3. Set IAM Permissions

```bash
# Get your email
USER_EMAIL=$(gcloud config get-value account)

# Grant necessary roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="user:${USER_EMAIL}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="user:${USER_EMAIL}" \
  --role="roles/storage.admin"
```

### 4. Create Service Account (for Cloud Run)

```bash
# Create service account
gcloud iam service-accounts create autonation-appraisal-ui \
  --display-name="AutoNation Appraisal UI"

# Grant permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:autonation-appraisal-ui@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:autonation-appraisal-ui@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:autonation-appraisal-ui@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

---

## 🚀 Deployment Steps

### Step 1: Deploy Data to BigQuery

```bash
# Create dataset
bq mk --dataset --location=$GCP_REGION ${GCP_PROJECT_ID}:autonation_demo

# Load mock market comparables
bq load --source_format=NEWLINE_DELIMITED_JSON \
  --autodetect \
  autonation_demo.market_comps \
  data/mock_market_comps.json

# Load demo VINs
bq load --source_format=CSV \
  --autodetect \
  --skip_leading_rows=1 \
  autonation_demo.demo_vins \
  data/demo_vins.csv
```

### Step 2: Deploy ADK Agents to Agent Engine

```bash
# Set environment variables
export STAGING_BUCKET="gs://autonation-staging-${GCP_PROJECT_ID}"
export GCP_PROJECT_ID="uppdemos"
export GCP_REGION="us-central1"

# Run deployment script
python3 deploy_to_agent_engine.py
```

**Expected output:**
```
📦 Deploying autonation-market-intelligence...
   ✅ Deployed successfully!
   Resource: projects/.../agentEngines/...
   URL: https://us-central1-aiplatform.googleapis.com/...

📦 Deploying autonation-vision-analyst...
   ✅ Deployed successfully!

📦 Deploying autonation-pricing-strategist...
   ✅ Deployed successfully!

✅ All 3 agents deployed successfully!
💾 Agent URLs saved to .env.deployed
```

### Step 3: Deploy Streamlit UI to Cloud Run

```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Run deployment script
./deploy_to_cloud_run.sh
```

**Expected output:**
```
📦 Step 1: Building Docker image...
✅ Image built successfully

📤 Step 2: Pushing to Google Container Registry...
✅ Image pushed successfully

🚀 Step 3: Deploying to Cloud Run...
✅ Deployment Complete!

🌐 Service URL: https://autonation-appraisal-ui-xxxxx-uc.a.run.app
```

---

## 🧪 Testing Deployed System

### Test Agent Engine Agents

Create `test_deployed_agents.py`:

```python
import requests
import os

# Load deployed agent URLs
MARKET_URL = os.environ.get("MARKET_INTELLIGENCE_URL")
VISION_URL = os.environ.get("VISION_ANALYST_URL")
PRICING_URL = os.environ.get("PRICING_STRATEGIST_URL")

def test_agent(url, message):
    """Test a deployed agent."""
    response = requests.post(
        url,
        json={"message": message, "user_id": "test-user"}
    )
    return response.json()

# Test market intelligence agent
print("Testing Market Intelligence Agent...")
result = test_agent(MARKET_URL, "Get market data for VIN 1HGBH41JXMN109186")
print(result)
```

### Test Cloud Run UI

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe autonation-appraisal-ui \
  --platform managed \
  --region $GCP_REGION \
  --format 'value(status.url)')

# Open in browser
open $SERVICE_URL

# Or curl test
curl $SERVICE_URL/_stcore/health
```

---

## 📊 Data Migration Strategy

### Current (Local Mock Data)
```
data/
├── mock_market_comps.json  → BigQuery table
├── demo_vins.csv           → BigQuery table
└── sample_photos/          → Cloud Storage bucket
```

### Production (Cloud Storage)

**Option 1: BigQuery for Structured Data** ⭐ RECOMMENDED
```sql
-- Query from agents
SELECT * FROM `uppdemos.autonation_demo.market_comps`
WHERE vin = @vin_param
```

Update `tools/api_mocks.py` to query BigQuery:
```python
from google.cloud import bigquery

def get_market_intelligence(vin: str):
    client = bigquery.Client()
    query = """
        SELECT * FROM `uppdemos.autonation_demo.market_comps`
        WHERE vin = @vin
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("vin", "STRING", vin)
        ]
    )
    results = client.query(query, job_config=job_config).to_dataframe()
    return results.to_dict('records')[0]
```

**Option 2: Cloud Storage for JSON**
```python
from google.cloud import storage

def get_market_intelligence(vin: str):
    client = storage.Client()
    bucket = client.bucket("autonation-market-data")
    blob = bucket.blob("market_comps.json")
    data = json.loads(blob.download_as_text())
    return data.get(vin)
```

---

## 🔄 Update Workflow

### Update Agents

```bash
# Make changes to agents/*.py
# Redeploy
python3 deploy_to_agent_engine.py
```

### Update UI

```bash
# Make changes to ui/streamlit_app.py
# Redeploy
./deploy_to_cloud_run.sh
```

---

## 📈 Monitoring & Logs

### View Agent Engine Logs

```bash
# Cloud Console
https://console.cloud.google.com/vertex-ai/agent-engine

# Or via gcloud (if available)
gcloud ai agent-engines list --region=$GCP_REGION
```

### View Cloud Run Logs

```bash
# Tail logs
gcloud run logs tail autonation-appraisal-ui --region=$GCP_REGION

# View in Cloud Console
https://console.cloud.google.com/run/detail/$GCP_REGION/autonation-appraisal-ui/logs
```

---

## 💰 Cost Estimation

| Service | Usage | Est. Monthly Cost |
|---------|-------|-------------------|
| Agent Engine | 3 agents, scale-to-zero | $50-200 |
| Cloud Run | 1 UI service, scale-to-zero | $20-50 |
| BigQuery | 1 GB storage, minimal queries | $5-10 |
| Cloud Storage | 10 GB photos | $2-5 |
| **Total** | | **~$100-300/month** |

Scale-to-zero keeps costs low during non-use periods.

---

## 🔒 Security Best Practices

1. **Use Service Accounts** - Don't use personal credentials
2. **Restrict IAM Roles** - Least privilege principle
3. **Enable VPC-SC** - For production (optional)
4. **Use Secret Manager** - For API keys
5. **Enable Authentication** - For Cloud Run (if needed)

---

## 🚨 Rollback Procedure

### Rollback Agents

```bash
# List previous versions
gcloud ai agent-engines list --region=$GCP_REGION

# Restore previous version (manual via console)
```

### Rollback UI

```bash
# Deploy previous image
gcloud run deploy autonation-appraisal-ui \
  --image gcr.io/uppdemos/autonation-appraisal-ui:previous-tag \
  --region=$GCP_REGION
```

---

## ✅ Post-Deployment Checklist

- [ ] All 3 agents deployed to Agent Engine
- [ ] BigQuery tables created and loaded
- [ ] Cloud Storage buckets created
- [ ] Streamlit UI deployed to Cloud Run
- [ ] Service account configured with proper IAM roles
- [ ] Tested demo VIN end-to-end
- [ ] Verified logs and monitoring
- [ ] Documented agent URLs in `.env.deployed`
- [ ] Shared Cloud Run URL with team

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue: "Staging bucket not found"**
```bash
# Create bucket
gsutil mb -p $GCP_PROJECT_ID -l $GCP_REGION gs://autonation-staging-$GCP_PROJECT_ID
export STAGING_BUCKET="gs://autonation-staging-$GCP_PROJECT_ID"
```

**Issue: "Permission denied"**
```bash
# Check IAM roles
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"
```

**Issue: "Agent deployment timeout"**
- Reduce `extra_packages` size
- Use requirements.txt instead of inline requirements
- Check staging bucket accessibility

---

## 🎯 Next Steps

1. **Test locally first**: `streamlit run ui/streamlit_app.py`
2. **Deploy agents**: `python3 deploy_to_agent_engine.py`
3. **Deploy UI**: `./deploy_to_cloud_run.sh`
4. **Test production**: Open Cloud Run URL
5. **Monitor**: Check logs and performance
6. **Optimize**: Tune resources based on usage

---

**Ready to deploy!** Start with Step 1: Deploy Data to BigQuery
