# OpenEnv Submission Validator for Windows PowerShell (Cloud-Optimized)
param (
    [Parameter(Mandatory=$true)]
    [string]$PingUrl
)

# Clean the URL (Remove trailing slash if present)
$PingUrl = $PingUrl.TrimEnd("/")

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenEnv Submission Validator (Cloud)  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- Step 1: Connectivity Check ---
Write-Host "[$(Get-Date -Format HH:mm:ss)] Step 1/3: Pinging Space at $PingUrl/reset ..."
try {
    # Test if the API is alive and responding
    $response = Invoke-WebRequest -Uri "$PingUrl/reset" -Method Post -Body '{}' -ContentType "application/json" -TimeoutSec 15 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ PASSED -- HF Space is live and responded to /reset" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ FAILED -- HF Space /reset failed. Status: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Hint: Ensure your Space is 'Running' and check your main.py routes." -ForegroundColor Yellow
    exit
}

# --- Step 2: Remote Dockerfile Check ---
Write-Host "[$(Get-Date -Format HH:mm:ss)] Step 2/3: Checking Remote Dockerfile at $PingUrl/Dockerfile ..."
try {
    # This checks the public endpoint we added to main.py
    $dockerCheck = Invoke-WebRequest -Uri "$PingUrl/Dockerfile" -Method Get -UseBasicParsing -MaximumRedirection 5
    if ($dockerCheck.StatusCode -eq 200 -and $dockerCheck.Content -match "FROM") {
        Write-Host "✅ PASSED -- Dockerfile is publicly accessible via API." -ForegroundColor Green
    } else {
        throw "File found but content doesn't look like a Dockerfile."
    }
} catch {
    Write-Host "⚠️  REMOTE CHECK FAILED -- Could not reach /Dockerfile via URL." -ForegroundColor Yellow
    Write-Host "Checking local folder as fallback..." -ForegroundColor Gray
    
    # Check local disk if remote fails
    if (Test-Path ".\Dockerfile") {
        Write-Host "✅ PASSED (Local) -- Dockerfile found in local root." -ForegroundColor Green
    } else {
        Write-Host "❌ FAILED -- No Dockerfile found locally or remotely." -ForegroundColor Red
        exit
    }
}

# --- Step 3: Remote OpenEnv Config Check ---
Write-Host "[$(Get-Date -Format HH:mm:ss)] Step 3/3: Checking for openenv.yaml ..."
try {
    $yamlCheck = Invoke-WebRequest -Uri "$PingUrl/openenv.yaml" -Method Get -UseBasicParsing -MaximumRedirection 5
    if ($yamlCheck.StatusCode -eq 200) {
        Write-Host "✅ PASSED -- openenv.yaml is publicly accessible via API." -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  REMOTE CHECK FAILED -- Checking local file..." -ForegroundColor Yellow
    if (Test-Path ".\openenv.yaml") {
         Write-Host "✅ PASSED (Local) -- openenv.yaml found locally." -ForegroundColor Green
    } else {
         Write-Host "❌ FAILED -- openenv.yaml not found." -ForegroundColor Red
    }
}

# Optional: Run CLI validation if installed
if (Get-Command "openenv" -ErrorAction SilentlyContinue) {
    Write-Host "`n[Local CLI] Running structural validation..." -ForegroundColor Gray
    & openenv validate .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PASSED -- openenv structural check passed." -ForegroundColor Green
    }
}

Write-Host "`n🎉 ALL CHECKS COMPLETED! Your cloud environment is healthy." -ForegroundColor Cyan