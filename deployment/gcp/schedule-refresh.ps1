$ErrorActionPreference = 'Stop'
$gcloudPath = (Get-Command gcloud.cmd -ErrorAction Stop).Source
$projectId = 'fynura-public-health'
$identity = "fynura-scheduler@$projectId.iam.gserviceaccount.com"
& $gcloudPath services enable cloudscheduler.googleapis.com --project $projectId --quiet
if ($LASTEXITCODE -ne 0) { throw 'Scheduler API enablement failed' }
$accounts = & $gcloudPath iam service-accounts list --project $projectId --format='value(email)'
if ($LASTEXITCODE -ne 0) { throw 'Identity lookup failed' }
if ($identity -notin $accounts) {
    & $gcloudPath iam service-accounts create fynura-scheduler --project $projectId --display-name='Fynura evidence refresh caller' --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Scheduler identity creation failed' }
}
# No broad project role: the application verifies this exact OIDC identity.
$jobs = & $gcloudPath scheduler jobs list --project $projectId --location us-central1 --format='value(name)'
if ($LASTEXITCODE -ne 0) { throw 'Scheduler lookup failed' }
$mode = if ($jobs -match '/fynura-evidence-refresh$') { 'update' } else { 'create' }
& $gcloudPath scheduler jobs $mode http fynura-evidence-refresh --project $projectId --location us-central1 --schedule='0 */12 * * *' --time-zone=Etc/UTC --uri='https://fynura-g7sjcbc4ua-uc.a.run.app/internal/refresh' --http-method=POST --oidc-service-account-email=$identity --oidc-token-audience='https://fynura-g7sjcbc4ua-uc.a.run.app' --attempt-deadline=300s --quiet
if ($LASTEXITCODE -ne 0) { throw 'Scheduler configuration failed' }
