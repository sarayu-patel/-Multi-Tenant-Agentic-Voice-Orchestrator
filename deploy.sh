#!/bin/bash
# Deploy to GCP Cloud Run — run this once after setting the variables below.
# Prerequisites: gcloud CLI installed and authenticated (gcloud auth login)

set -e

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="voice-agent"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Building and pushing Docker image..."
gcloud builds submit --tag "$IMAGE"

echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "MONGODB_URI=$MONGODB_URI" \
  --set-env-vars "MONGODB_DB_NAME=voice_agent" \
  --set-env-vars "VAPI_API_KEY=$VAPI_API_KEY" \
  --set-env-vars "VAPI_PHONE_NUMBER_ID=$VAPI_PHONE_NUMBER_ID" \
  --set-env-vars "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"

echo ""
echo "Deployed. Your webhook URL is:"
gcloud run services describe "$SERVICE_NAME" --region "$REGION" \
  --format "value(status.url)" | sed 's|$|/api/webhooks/vapi|'
