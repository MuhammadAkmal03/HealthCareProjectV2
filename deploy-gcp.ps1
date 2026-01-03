# Quick Deploy Script for Google Cloud Run
# This script automates the deployment process

Write-Host "HealthPro2 GCP Deployment Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Google Cloud SDK (gcloud) is not installed!" -ForegroundColor Red
    Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

Write-Host "Google Cloud SDK detected" -ForegroundColor Green

# Get project ID
Write-Host "`nStep 1: Project Configuration" -ForegroundColor Yellow
$projectId = Read-Host "Enter your GCP Project ID (or press Enter for 'healthpro2-app')"

if ([string]::IsNullOrWhiteSpace($projectId)) {
    $projectId = "healthpro2-app"
    Write-Host "Creating new project: $projectId..." -ForegroundColor Cyan
    gcloud projects create $projectId --name="HealthPro2 API"
}

Write-Host "Setting project to: $projectId" -ForegroundColor Cyan
gcloud config set project $projectId

# Get region
Write-Host "`nStep 2: Region Selection" -ForegroundColor Yellow
Write-Host "Available regions:"
Write-Host "  1. us-central1 (Iowa, USA)"
Write-Host "  2. us-east1 (South Carolina, USA)"
Write-Host "  3. europe-west1 (Belgium)"
Write-Host "  4. asia-southeast1 (Singapore)"
$regionChoice = Read-Host "Select region (1-4, default: 1)"

$region = switch ($regionChoice) {
    "2" { "us-east1" }
    "3" { "europe-west1" }
    "4" { "asia-southeast1" }
    default { "us-central1" }
}

Write-Host "Selected region: $region" -ForegroundColor Green
gcloud config set run/region $region

# Enable required APIs
Write-Host "`nStep 3: Enabling Required APIs..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Cyan

gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

Write-Host "APIs enabled successfully" -ForegroundColor Green

# Get environment variables
Write-Host "`nStep 4: Environment Variables" -ForegroundColor Yellow
$googleKey = Read-Host "Enter your GOOGLE_API_KEY (for Gemini)"
$pineconeKey = Read-Host "Enter your PINECONE_API_KEY"

# GCS Bucket for Analytics Data Persistence
Write-Host "`nStep 5: Analytics Data Storage (GCS Bucket)" -ForegroundColor Yellow
$defaultBucket = "$projectId-analytics"
$gcsBucket = Read-Host "Enter GCS bucket name for analytics data (default: $defaultBucket)"
if ([string]::IsNullOrWhiteSpace($gcsBucket)) {
    $gcsBucket = $defaultBucket
}

Write-Host "Enabling Cloud Storage API..." -ForegroundColor Cyan
gcloud services enable storage.googleapis.com

Write-Host "Creating bucket $gcsBucket if needed..." -ForegroundColor Cyan
$bucketExists = gsutil ls -b "gs://$gcsBucket" 2>$null
if (-not $bucketExists) {
    gsutil mb -l $region "gs://$gcsBucket"
    Write-Host "Created bucket: $gcsBucket" -ForegroundColor Green
} else {
    Write-Host "Bucket already exists: $gcsBucket" -ForegroundColor Green
}

# Deploy
Write-Host "`nStep 6: Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "This will take 5-10 minutes. Please be patient..." -ForegroundColor Cyan

gcloud run deploy healthpro2-api --source . --platform managed --region $region --allow-unauthenticated --port 8000 --memory 2Gi --cpu 2 --timeout 300 --max-instances 10 --set-env-vars "GOOGLE_API_KEY=$googleKey,PINECONE_API_KEY=$pineconeKey,GCS_BUCKET_NAME=$gcsBucket"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDeployment Successful!" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "1. Your API is now live! Check the URL above" -ForegroundColor White
    Write-Host "2. Test it: curl YOUR_URL/" -ForegroundColor White
    Write-Host "3. View API docs: YOUR_URL/docs" -ForegroundColor White
    Write-Host "4. Update your frontend CORS settings with the new URL" -ForegroundColor White
    Write-Host "`nView logs:" -ForegroundColor Cyan
    Write-Host "gcloud run services logs tail healthpro2-api --region $region" -ForegroundColor White
} else {
    Write-Host "`nDeployment failed. Check the error messages above." -ForegroundColor Red
    Write-Host "For help, see: DEPLOYMENT_GUIDE.md" -ForegroundColor Yellow
}
