# Alternative Deployment Script - Build Locally, Push to GCR
# This avoids network issues with large uploads

Write-Host "HealthPro2 GCP Deployment - Local Build" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Google Cloud SDK is not installed!" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed or not running!" -ForegroundColor Red
    exit 1
}

Write-Host "Prerequisites detected`n" -ForegroundColor Green

# Get project ID
$projectId = Read-Host "Enter your GCP Project ID (default: alphasignal-480013)"
if ([string]::IsNullOrWhiteSpace($projectId)) {
    $projectId = "alphasignal-480013"
}

Write-Host "Using project: $projectId" -ForegroundColor Cyan
gcloud config set project $projectId

# Get region
$region = Read-Host "Enter region (default: us-central1)"
if ([string]::IsNullOrWhiteSpace($region)) {
    $region = "us-central1"
}

# Get environment variables
Write-Host "`nEnvironment Variables" -ForegroundColor Yellow
$googleKey = Read-Host "Enter your GOOGLE_API_KEY"
$pineconeKey = Read-Host "Enter your PINECONE_API_KEY"

# GCS Bucket for Analytics Data Persistence
Write-Host "`nAnalytics Data Storage (GCS Bucket)" -ForegroundColor Yellow
$defaultBucket = "$projectId-analytics"
$gcsBucket = Read-Host "Enter GCS bucket name for analytics data (default: $defaultBucket)"
if ([string]::IsNullOrWhiteSpace($gcsBucket)) {
    $gcsBucket = $defaultBucket
}

Write-Host "Enabling Cloud Storage API..." -ForegroundColor Cyan
gcloud services enable storage.googleapis.com

Write-Host "Creating bucket '$gcsBucket' if needed..." -ForegroundColor Cyan
$bucketExists = gsutil ls -b "gs://$gcsBucket" 2>$null
if (-not $bucketExists) {
    gsutil mb -l $region "gs://$gcsBucket"
    Write-Host "Created bucket: $gcsBucket" -ForegroundColor Green
} else {
    Write-Host "Bucket already exists: $gcsBucket" -ForegroundColor Green
}

# Configure Docker for GCR
Write-Host "`nConfiguring Docker for Google Container Registry..." -ForegroundColor Yellow
gcloud auth configure-docker

# Build image locally
$imageName = "gcr.io/$projectId/healthpro2-api:latest"
Write-Host "`nBuilding Docker image locally..." -ForegroundColor Yellow
Write-Host "This may take a few minutes...`n" -ForegroundColor Cyan

docker build -t $imageName .

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nDocker build failed!" -ForegroundColor Red
    exit 1
}

# Push to Google Container Registry
Write-Host "`nPushing image to Google Container Registry..." -ForegroundColor Yellow
Write-Host "This may take a few minutes...`n" -ForegroundColor Cyan

docker push $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nDocker push failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "`nDeploying to Cloud Run..." -ForegroundColor Yellow

gcloud run deploy healthpro2-api `
    --image $imageName `
    --platform managed `
    --region $region `
    --allow-unauthenticated `
    --port 8000 `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars "GOOGLE_API_KEY=$googleKey,PINECONE_API_KEY=$pineconeKey,GCS_BUCKET_NAME=$gcsBucket"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDeployment Successful!" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "1. Your API is now live! Check the URL above" -ForegroundColor White
    Write-Host "2. Test it with: curl YOUR_URL/" -ForegroundColor White
    Write-Host "3. View API docs at: YOUR_URL/docs" -ForegroundColor White
    Write-Host "`nView logs with:" -ForegroundColor Cyan
    Write-Host "gcloud run services logs tail healthpro2-api --region $region" -ForegroundColor White
} else {
    Write-Host "`nDeployment failed. Check the error messages above." -ForegroundColor Red
}
