[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$errors = [System.Collections.Generic.List[string]]::new()
function Fail([string]$Message) { $errors.Add($Message) }

foreach ($tool in @('git','node')) { if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { Fail "Required tool is unavailable: $tool" } }
$branch = if (-not [string]::IsNullOrWhiteSpace($env:PREFLIGHT_GIT_BRANCH)) {
  $env:PREFLIGHT_GIT_BRANCH
} else {
  git -C $root branch --show-current
}
if ([string]::IsNullOrWhiteSpace($branch)) { Fail 'Git branch could not be determined.' }
if ($env:ALLOW_DIRTY_GIT -ne 'true' -and (git -C $root status --porcelain)) { Fail 'Git state is not clean or explicitly approved.' }
if ($env:IMAGE_REFERENCE -notmatch '^[a-z0-9][a-z0-9._/-]*(?::[A-Za-z0-9._-]+|@sha256:[a-f0-9]{64})$') { Fail 'IMAGE_REFERENCE format is invalid.' }

& (Join-Path $PSScriptRoot 'validate-environment.ps1')
if (-not $?) { Fail 'Environment validation failed.' }

$requiredFiles = @(
  'docs/adr/ADR-001-production-hosting-architecture.md',
  'docs/infrastructure/production-infrastructure-specification.md',
  'docs/infrastructure/production-release-gates.md',
  'deploy/health/health-check-contract.md',
  'backend/scripts/check_migrations.py'
)
foreach ($file in $requiredFiles) { if (-not (Test-Path (Join-Path $root $file))) { Fail "Required artifact is missing: $file" } }
& node (Join-Path $root 'scripts/validate-frontend.mjs')
if ($LASTEXITCODE -ne 0) { Fail 'Frontend runtime configuration policy is invalid.' }

if ($errors.Count) { foreach ($message in $errors) { Write-Error $message }; Write-Output 'Preflight failed; no deployment was performed.'; exit 1 }
Write-Output 'Preflight passed; no deployment, database connection, image push, or cloud action was performed.'

