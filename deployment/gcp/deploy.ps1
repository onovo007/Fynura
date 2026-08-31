$ErrorActionPreference = "Stop"
$projectId = "fynura-public-health"
$region = if ($env:GOOGLE_CLOUD_LOCATION) { $env:GOOGLE_CLOUD_LOCATION } else { "us-central1" }
$gcloudPath = (Get-Command gcloud.cmd -ErrorAction Stop).Source
$buildServiceAccount = "projects/$projectId/serviceAccounts/fynura-build@$projectId.iam.gserviceaccount.com"
$chatModel = if ($env:FYNURA_CHAT_MODEL) { $env:FYNURA_CHAT_MODEL } else { "gemini-3.7-flash" }

& $gcloudPath run deploy fynura --source . --project $projectId --region $region --build-service-account $buildServiceAccount --no-traffic --tag validation --update-env-vars "FYNURA_CHAT_MODEL=$chatModel,FYNURA_CHAT_LOCATION=global" --quiet
if ($LASTEXITCODE -ne 0) { throw "Cloud Run deployment failed." }

# Existing auth, secrets, service identity and production traffic are preserved.
# Verify the validation revision before explicitly promoting its traffic.

& $gcloudPath run services describe fynura --project $projectId --region $region --format="value(status.url)"
