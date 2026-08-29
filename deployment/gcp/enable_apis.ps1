$ErrorActionPreference = "Stop"
$projectId = "fynura-public-health"
gcloud config set project $projectId
gcloud services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com logging.googleapis.com cloudtrace.googleapis.com --project $projectId

