$ErrorActionPreference = "Stop"

$gcloudPath = (Get-Command gcloud.cmd -ErrorAction Stop).Source
$projectId = "fynura-public-health"
$region = "us-central1"

if (-not (Test-Path -LiteralPath $gcloudPath)) {
    throw "Google Cloud CLI was not found at: $gcloudPath"
}

# Make gcloud available by name in this PowerShell session.
$gcloudBin = Split-Path -Parent $gcloudPath
if (($env:Path -split ";") -notcontains $gcloudBin) {
    $env:Path = "$gcloudBin;$env:Path"
}

Write-Host "Initializing Google Cloud CLI..."
& $gcloudPath init

Write-Host "Creating local Application Default Credentials for Vertex AI..."
& $gcloudPath auth application-default login

Write-Host "Configuring Fynura defaults..."
& $gcloudPath config set project $projectId
& $gcloudPath config set run/region $region

Write-Host "Verifying configuration..."
& $gcloudPath auth list
& $gcloudPath config list
& $gcloudPath projects describe $projectId --format="value(projectId,projectNumber)"
if ($LASTEXITCODE -ne 0) {
    throw "The active Google account cannot access project '$projectId'. Sign in with an authorized account or ask a project/organization administrator to grant IAM access, then rerun this script."
}

Write-Host "Assigning the Fynura project as the ADC quota project..."
& $gcloudPath auth application-default set-quota-project $projectId
if ($LASTEXITCODE -ne 0) {
    throw "Could not set the ADC quota project. Confirm the active account has serviceusage.services.use on '$projectId'."
}

Write-Host "Google Cloud CLI is ready for Fynura."
