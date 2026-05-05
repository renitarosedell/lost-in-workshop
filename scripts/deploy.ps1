<#
.SYNOPSIS
    Full deployment script for Lost in Workshop — Azure Container Apps + Blob Storage.

.DESCRIPTION
    Runs all deployment steps end-to-end:
      1. Build document bundles
      2. Create Azure infrastructure (ACR, Storage, Container Apps env)
      3. Upload document bundles to Blob Storage
      4. Build and push Docker images
      5. Deploy Container Apps
      6. Patch city_config.yaml with live URLs and redeploy game server

.PARAMETER ResourceGroup
    Azure resource group name. Default: raleigh-workshop

.PARAMETER Location
    Azure region. Default: eastus2

.PARAMETER AcrName
    Azure Container Registry name (must be globally unique). Default: raleighworkshop

.PARAMETER StorageAccount
    Azure Storage account name (must be globally unique). Default: raleighworkshop

.PARAMETER OpenAiEndpoint
    Azure OpenAI endpoint URL (required). Example: https://my-hub.openai.azure.com/

.PARAMETER OpenAiDeployment
    Azure OpenAI model deployment name. Default: gpt-4o-mini

.PARAMETER OpenAiResourceGroup
    Resource group containing the Azure OpenAI account.
    Defaults to the same resource group as the rest of the workshop infrastructure.

.PARAMETER ConfigFile
    Path to a JSON config file. Defaults to scripts/deploy.config.json.
    Copy scripts/deploy.config.json.example to scripts/deploy.config.json and fill in your values.
    Any parameter passed on the command line takes precedence over the config file.

.EXAMPLE
    # Recommended: use a config file
    Copy-Item scripts\deploy.config.json.example scripts\deploy.config.json
    # Edit scripts\deploy.config.json with your values, then:
    .\scripts\deploy.ps1

.EXAMPLE
    # Override individual values from the command line
    .\.\scripts\deploy.ps1 -OpenAiEndpoint "https://my-hub.openai.azure.com/"
#>

[CmdletBinding()]
param(
    [string] $ConfigFile       = (Join-Path $PSScriptRoot "deploy.config.json"),

    [string] $ResourceGroup,
    [string] $Location,
    [string] $AcrName,
    [string] $StorageAccount,
    [string] $Environment,
    [string] $OpenAiEndpoint,
    [string] $OpenAiDeployment,
    [string] $OpenAiResourceGroup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot

# ─── Load config file, then apply CLI overrides ──────────────────────────────

$cfg = @{
    ResourceGroup    = "raleigh-workshop"
    Location         = "eastus2"
    AcrName          = "raleighworkshop"
    StorageAccount   = "raleighworkshop"
    Environment      = "raleigh-env"
    OpenAiEndpoint       = ""
    OpenAiDeployment     = "gpt-4o-mini"
    OpenAiResourceGroup  = ""
}

if (Test-Path $ConfigFile) {
    $json = Get-Content $ConfigFile -Raw | ConvertFrom-Json
    foreach ($key in @($cfg.Keys)) {
        $val = $json.PSObject.Properties[$key]
        if ($null -ne $val -and $val.Value -ne "") {
            $cfg[$key] = $val.Value
        }
    }
    Write-Host "Config loaded from $ConfigFile" -ForegroundColor DarkGray
} else {
    Write-Host "No config file found at $ConfigFile — using defaults and CLI parameters." -ForegroundColor Yellow
    Write-Host "Tip: copy scripts\deploy.config.json.example to scripts\deploy.config.json" -ForegroundColor DarkGray
}

# CLI parameters override config file values
if ($ResourceGroup)    { $cfg.ResourceGroup    = $ResourceGroup }
if ($Location)         { $cfg.Location         = $Location }
if ($AcrName)          { $cfg.AcrName          = $AcrName }
if ($StorageAccount)   { $cfg.StorageAccount   = $StorageAccount }
if ($Environment)      { $cfg.Environment      = $Environment }
if ($OpenAiEndpoint)       { $cfg.OpenAiEndpoint      = $OpenAiEndpoint }
if ($OpenAiDeployment)     { $cfg.OpenAiDeployment    = $OpenAiDeployment }
if ($OpenAiResourceGroup)  { $cfg.OpenAiResourceGroup = $OpenAiResourceGroup }

# Unpack for readability
$ResourceGroup    = $cfg.ResourceGroup
$Location         = $cfg.Location
$AcrName          = $cfg.AcrName
$StorageAccount   = $cfg.StorageAccount
$Environment      = $cfg.Environment
$OpenAiEndpoint      = $cfg.OpenAiEndpoint
$OpenAiDeployment    = $cfg.OpenAiDeployment
$OpenAiResourceGroup = if ($cfg.OpenAiResourceGroup) { $cfg.OpenAiResourceGroup } else { $cfg.ResourceGroup }

function Step([string]$msg) {
    Write-Host ""
    Write-Host "━━━ $msg" -ForegroundColor Cyan
}

function Ok([string]$msg) {
    Write-Host "  ✔ $msg" -ForegroundColor Green
}

function Fail([string]$msg) {
    Write-Host "  ✖ $msg" -ForegroundColor Red
    exit 1
}

# Validate required values
if (-not $OpenAiEndpoint -or $OpenAiEndpoint -like "*<*") {
    Fail "OpenAiEndpoint is not set. Add it to deploy.config.json or pass -OpenAiEndpoint."
}

# ─── Preflight ────────────────────────────────────────────────────────────────

Step "Preflight checks"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { Fail "Azure CLI not found. Install from https://docs.microsoft.com/cli/azure/install-azure-cli" }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Fail "Docker not found. Install Docker Desktop." }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Fail "Python not found. Install Python 3.11+." }

$account = az account show --query name -o tsv 2>$null
if (-not $account) { Fail "Not logged in to Azure. Run 'az login' first." }
Ok "Azure CLI: logged in as subscription '$account'"
Ok "Docker: available"
Ok "Python: available"

# ─── Step 1: Build bundles ───────────────────────────────────────────────────

Step "Step 1/7 — Building document bundles"

Push-Location (Join-Path $RepoRoot "lost-in-raleigh")
python build_bundles.py
if ($LASTEXITCODE -ne 0) { Fail "build_bundles.py failed" }
Pop-Location

Ok "Bundles built in bundles/raleigh/"

# ─── Step 2: Create ACR ──────────────────────────────────────────────────────

Step "Step 2/7 — Creating Azure Container Registry"

$acrExists = az acr show --name $AcrName --resource-group $ResourceGroup --query name -o tsv 2>$null
if ($acrExists) {
    Ok "ACR '$AcrName' already exists, skipping"
} else {
    az acr create `
        --resource-group $ResourceGroup `
        --name $AcrName `
        --sku Basic `
        --admin-enabled true `
        --output none
    Ok "ACR '$AcrName' created"
}

$AcrLoginServer = az acr show --name $AcrName --query loginServer -o tsv
az acr login --name $AcrName --output none
Ok "Logged in to ACR: $AcrLoginServer"

# ─── Step 3: Create Storage + upload bundles ─────────────────────────────────

Step "Step 3/7 — Creating Blob Storage and uploading bundles"

$storageExists = az storage account show --name $StorageAccount --resource-group $ResourceGroup --query name -o tsv 2>$null
if ($storageExists) {
    Ok "Storage account '$StorageAccount' already exists, skipping create"
} else {
    az storage account create `
        --name $StorageAccount `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku Standard_LRS `
        --output none
    Ok "Storage account '$StorageAccount' created"
}

az storage container create `
    --name bundles `
    --account-name $StorageAccount `
    --public-access blob `
    --output none

az storage blob upload-batch `
    --account-name $StorageAccount `
    --destination bundles `
    --source (Join-Path $RepoRoot "bundles\raleigh") `
    --pattern "*.zip" `
    --overwrite `
    --output none

$BlobBase = "https://$StorageAccount.blob.core.windows.net/bundles"
Ok "Bundles uploaded to $BlobBase"

# ─── Step 4: Container Apps environment ──────────────────────────────────────

Step "Step 4/7 — Creating Container Apps environment"

$envExists = az containerapp env show --name $Environment --resource-group $ResourceGroup --query name -o tsv 2>$null
if ($envExists) {
    Ok "Container Apps environment '$Environment' already exists, skipping"
} else {
    az containerapp env create `
        --name $Environment `
        --resource-group $ResourceGroup `
        --location $Location `
        --output none
    Ok "Container Apps environment '$Environment' created"
}

# ─── Step 5: Build and push Docker images ────────────────────────────────────

Step "Step 5/7 — Building and pushing Docker images"

docker build -t "$AcrLoginServer/lost-in-raleigh:latest" (Join-Path $RepoRoot "lost-in-raleigh")
docker push "$AcrLoginServer/lost-in-raleigh:latest"
Ok "Game server image pushed"

docker build -t "$AcrLoginServer/a2a-expert:latest" (Join-Path $RepoRoot "a2a-expert")
docker push "$AcrLoginServer/a2a-expert:latest"
Ok "A2A expert image pushed"

# ─── Step 6: Deploy Container Apps ───────────────────────────────────────────

Step "Step 6/7 — Deploying Container Apps"

$AcrPassword = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv

# Game server
$gameExists = az containerapp show --name lost-in-raleigh --resource-group $ResourceGroup --query name -o tsv 2>$null
if ($gameExists) {
    az containerapp update `
        --name lost-in-raleigh `
        --resource-group $ResourceGroup `
        --image "$AcrLoginServer/lost-in-raleigh:latest" `
        --output none
    Ok "Game server updated"
} else {
    az containerapp create `
        --name lost-in-raleigh `
        --resource-group $ResourceGroup `
        --environment $Environment `
        --image "$AcrLoginServer/lost-in-raleigh:latest" `
        --registry-server $AcrLoginServer `
        --registry-username $AcrName `
        --registry-password $AcrPassword `
        --target-port 8000 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 3 `
        --cpu 0.5 `
        --memory 1Gi `
        --output none
    Ok "Game server deployed"
}

$GameFqdn = az containerapp show `
    --name lost-in-raleigh `
    --resource-group $ResourceGroup `
    --query properties.configuration.ingress.fqdn -o tsv

# A2A expert
$a2aExists = az containerapp show --name a2a-expert --resource-group $ResourceGroup --query name -o tsv 2>$null
if ($a2aExists) {
    az containerapp update `
        --name a2a-expert `
        --resource-group $ResourceGroup `
        --image "$AcrLoginServer/a2a-expert:latest" `
        --output none
    Ok "A2A expert updated"
} else {
    az containerapp create `
        --name a2a-expert `
        --resource-group $ResourceGroup `
        --environment $Environment `
        --image "$AcrLoginServer/a2a-expert:latest" `
        --registry-server $AcrLoginServer `
        --registry-username $AcrName `
        --registry-password $AcrPassword `
        --target-port 8001 `
        --ingress external `
        --min-replicas 1 `
        --max-replicas 3 `
        --cpu 0.25 `
        --memory 0.5Gi `
        --set-env-vars `
            "AZURE_OPENAI_ENDPOINT=$OpenAiEndpoint" `
            "AZURE_OPENAI_DEPLOYMENT_NAME=$OpenAiDeployment" `
        --output none
    Ok "A2A expert deployed"
}

# Assign system-managed identity and grant Cognitive Services OpenAI User role
$A2aPrincipalId = az containerapp identity assign `
    --name a2a-expert `
    --resource-group $ResourceGroup `
    --system-assigned `
    --query principalId -o tsv

# Derive the Azure OpenAI account name from the endpoint URL
# e.g. https://my-hub.openai.azure.com/ -> my-hub
$OpenAiAccountName = $OpenAiEndpoint -replace 'https://', '' -replace '\.openai\.azure\.com.*', ''

$OpenAiResourceId = az cognitiveservices account show `
    --name $OpenAiAccountName `
    --resource-group $OpenAiResourceGroup `
    --query id -o tsv

az role assignment create `
    --assignee $A2aPrincipalId `
    --role "Cognitive Services OpenAI User" `
    --scope $OpenAiResourceId `
    --output none

Ok "Managed identity assigned and 'Cognitive Services OpenAI User' role granted"

$A2aFqdn = az containerapp show `
    --name a2a-expert `
    --resource-group $ResourceGroup `
    --query properties.configuration.ingress.fqdn -o tsv

# ─── Step 7: Patch city_config.yaml and redeploy game server ─────────────────

Step "Step 7/7 — Patching city_config.yaml with live URLs"

$ConfigPath = Join-Path $RepoRoot "lost-in-raleigh\city_config.yaml"
$config = Get-Content $ConfigPath -Raw

$config = $config -replace [regex]::Escape("https://<a2a-expert-host>/a2a"), "https://$A2aFqdn/a2a"
$config = $config -replace [regex]::Escape("https://<blob-storage-host>/bundles/raleigh/"), "$BlobBase/"

Set-Content $ConfigPath $config -NoNewline
Ok "city_config.yaml patched"

# Rebuild and redeploy game server with updated config
docker build -t "$AcrLoginServer/lost-in-raleigh:latest" (Join-Path $RepoRoot "lost-in-raleigh")
docker push "$AcrLoginServer/lost-in-raleigh:latest"
az containerapp update `
    --name lost-in-raleigh `
    --resource-group $ResourceGroup `
    --image "$AcrLoginServer/lost-in-raleigh:latest" `
    --output none
Ok "Game server redeployed with live config"

# ─── Summary ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "  Game server  : https://$GameFqdn"
Write-Host "  MCP endpoint : https://$GameFqdn/mcp"
Write-Host "  Admin UI     : https://$GameFqdn/admin"
Write-Host "  A2A expert   : https://$A2aFqdn/a2a"
Write-Host "  Blob bundles : $BlobBase"
Write-Host ""
Write-Host "  Post this to attendees:" -ForegroundColor Yellow
Write-Host "  MCP_SERVER_URL=https://$GameFqdn/mcp" -ForegroundColor Yellow
Write-Host ""
