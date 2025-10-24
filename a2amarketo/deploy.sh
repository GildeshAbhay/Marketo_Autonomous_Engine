#!/bin/bash

# Google Cloud Run Deployment Script for A2A Marketo
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -e  # Exit on error

ENVIRONMENT=${1:-production}
PROJECT_ID="your-gcp-project-id"  # Replace with your GCP project ID
REGION="us-central1"  # Replace with your preferred region

echo "🚀 Deploying A2A Marketo to Google Cloud Run"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📦 Enabling required Google Cloud APIs..."
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com

# Build and deploy each service
echo ""
echo "🏗️  Building and deploying services..."

# 1. Deploy Marketo Agent
echo ""
echo "1️⃣  Deploying Marketo Agent..."
gcloud builds submit ./marketo_agent \
  --tag gcr.io/$PROJECT_ID/marketo-agent:latest \
  --timeout=20m

gcloud run deploy marketo-agent \
  --image gcr.io/$PROJECT_ID/marketo-agent:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars DEPLOYMENT_ENV=$ENVIRONMENT \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,MARKETO_CLIENT_ID=MARKETO_CLIENT_ID:latest,MARKETO_CLIENT_SECRET=MARKETO_CLIENT_SECRET:latest,MARKETO_IDENTITY_BASE=MARKETO_IDENTITY_BASE:latest,MARKETO_REST_BASE=MARKETO_REST_BASE:latest

# Get Marketo Agent URL
MARKETO_AGENT_URL=$(gcloud run services describe marketo-agent --region $REGION --format 'value(status.url)')
echo "✅ Marketo Agent deployed at: $MARKETO_AGENT_URL"

# 2. Deploy WebSearch Agent
echo ""
echo "2️⃣  Deploying WebSearch Agent..."
gcloud builds submit ./websearch_agent \
  --tag gcr.io/$PROJECT_ID/websearch-agent:latest \
  --timeout=20m

gcloud run deploy websearch-agent \
  --image gcr.io/$PROJECT_ID/websearch-agent:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars DEPLOYMENT_ENV=$ENVIRONMENT \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest

# Get WebSearch Agent URL
WEBSEARCH_AGENT_URL=$(gcloud run services describe websearch-agent --region $REGION --format 'value(status.url)')
echo "✅ WebSearch Agent deployed at: $WEBSEARCH_AGENT_URL"

# 3. Deploy MCP Server
echo ""
echo "3️⃣  Deploying MCP Server..."
gcloud builds submit ./marketo_agent/mcp-servers \
  --tag gcr.io/$PROJECT_ID/mcp-server:latest \
  --timeout=20m

gcloud run deploy mcp-server \
  --image gcr.io/$PROJECT_ID/mcp-server:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 5 \
  --set-env-vars DEPLOYMENT_ENV=$ENVIRONMENT \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,MARKETO_CLIENT_ID=MARKETO_CLIENT_ID:latest,MARKETO_CLIENT_SECRET=MARKETO_CLIENT_SECRET:latest,MARKETO_IDENTITY_BASE=MARKETO_IDENTITY_BASE:latest,MARKETO_REST_BASE=MARKETO_REST_BASE:latest

# Get MCP Server URL
MCP_SERVER_URL=$(gcloud run services describe mcp-server --region $REGION --format 'value(status.url)')
echo "✅ MCP Server deployed at: $MCP_SERVER_URL"

# 4. Deploy Host Agent
echo ""
echo "4️⃣  Deploying Host Agent..."
gcloud builds submit ./host_agent_marketo \
  --tag gcr.io/$PROJECT_ID/host-agent:latest \
  --timeout=20m

gcloud run deploy host-agent \
  --image gcr.io/$PROJECT_ID/host-agent:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --max-instances 10 \
  --set-env-vars DEPLOYMENT_ENV=$ENVIRONMENT,MARKETO_AGENT_URL=$MARKETO_AGENT_URL,WEBSEARCH_AGENT_URL=$WEBSEARCH_AGENT_URL,MCP_SERVER_URL=$MCP_SERVER_URL \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,MARKETO_CLIENT_ID=MARKETO_CLIENT_ID:latest,MARKETO_CLIENT_SECRET=MARKETO_CLIENT_SECRET:latest,MARKETO_IDENTITY_BASE=MARKETO_IDENTITY_BASE:latest,MARKETO_REST_BASE=MARKETO_REST_BASE:latest

# Get Host Agent URL
HOST_AGENT_URL=$(gcloud run services describe host-agent --region $REGION --format 'value(status.url)')
echo "✅ Host Agent deployed at: $HOST_AGENT_URL"

# 5. Deploy Backend
echo ""
echo "5️⃣  Deploying Backend..."
gcloud builds submit ./backend \
  --tag gcr.io/$PROJECT_ID/backend:latest \
  --timeout=20m

gcloud run deploy backend \
  --image gcr.io/$PROJECT_ID/backend:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars DEPLOYMENT_ENV=$ENVIRONMENT,MARKETO_AGENT_URL=$MARKETO_AGENT_URL,WEBSEARCH_AGENT_URL=$WEBSEARCH_AGENT_URL,MCP_SERVER_URL=$MCP_SERVER_URL \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,SECRET_KEY=JWT_SECRET_KEY:latest,SUPABASE_DATABASE_URL=SUPABASE_DATABASE_URL:latest,MARKETO_CLIENT_ID=MARKETO_CLIENT_ID:latest,MARKETO_CLIENT_SECRET=MARKETO_CLIENT_SECRET:latest,MARKETO_IDENTITY_BASE=MARKETO_IDENTITY_BASE:latest,MARKETO_REST_BASE=MARKETO_REST_BASE:latest

# Get Backend URL
BACKEND_URL=$(gcloud run services describe backend --region $REGION --format 'value(status.url)')
echo "✅ Backend deployed at: $BACKEND_URL"

# 6. Deploy Frontend
echo ""
echo "6️⃣  Deploying Frontend..."
gcloud builds submit ./frontend \
  --tag gcr.io/$PROJECT_ID/frontend:latest \
  --timeout=20m

gcloud run deploy frontend \
  --image gcr.io/$PROJECT_ID/frontend:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --timeout 60 \
  --max-instances 10 \
  --set-env-vars DEPLOYMENT_ENV=$ENVIRONMENT

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe frontend --region $REGION --format 'value(status.url)')
echo "✅ Frontend deployed at: $FRONTEND_URL"

# Update backend with frontend URL (for CORS)
echo ""
echo "🔄 Updating backend with frontend URL for CORS..."
gcloud run services update backend \
  --region $REGION \
  --update-env-vars FRONTEND_URL=$FRONTEND_URL

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📝 Service URLs:"
echo "   Frontend:       $FRONTEND_URL"
echo "   Backend:        $BACKEND_URL"
echo "   Host Agent:     $HOST_AGENT_URL"
echo "   Marketo Agent:  $MARKETO_AGENT_URL"
echo "   WebSearch:      $WEBSEARCH_AGENT_URL"
echo "   MCP Server:     $MCP_SERVER_URL"
echo ""
echo "🔐 Next steps:"
echo "   1. Update frontend JavaScript to use: $BACKEND_URL"
echo "   2. Test the frontend at: $FRONTEND_URL"
echo "   3. Set up custom domain (optional)"