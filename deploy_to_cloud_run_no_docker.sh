#!/bin/bash
# Deploy AutoNation Streamlit UI to Cloud Run (without local Docker)
# Uses Cloud Build to build the image in the cloud

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"uppdemos"}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME="autonation-appraisal-ui"

echo "=========================================="
echo "Deploying AutoNation UI to Cloud Run"
echo "Using Cloud Build (no local Docker needed)"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "=========================================="

# Deploy using source (Cloud Build handles the Docker build)
echo ""
echo "🚀 Deploying to Cloud Run..."
echo "Note: This will build the image in the cloud (takes 5-10 minutes)"

gcloud run deploy ${SERVICE_NAME} \
  --source . \
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
