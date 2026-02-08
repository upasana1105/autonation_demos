#!/bin/bash
# Deploy AutoNation Streamlit UI to Cloud Run

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"uppdemos"}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME="autonation-appraisal-ui"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=========================================="
echo "Deploying AutoNation UI to Cloud Run"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "=========================================="

# Step 1: Build Docker image
echo ""
echo "📦 Step 1: Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .
echo "✅ Image built successfully"

# Step 2: Push to Container Registry
echo ""
echo "📤 Step 2: Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}:latest
echo "✅ Image pushed successfully"

# Step 3: Deploy to Cloud Run
echo ""
echo "🚀 Step 3: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8501 \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 600 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=1"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📋 Next Steps:"
echo "1. Open the URL in your browser"
echo "2. Test with demo VINs"
echo "3. Monitor logs: gcloud run logs tail ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "=========================================="
