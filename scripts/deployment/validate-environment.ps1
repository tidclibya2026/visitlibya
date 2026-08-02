[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$errors = [System.Collections.Generic.List[string]]::new()
$required = @(
  'APP_ENV','DEBUG','DATABASE_URL','JWT_SECRET_KEY','CORS_ORIGINS','TRUSTED_HOSTS',
  'FORWARDED_ALLOW_IPS','DATABASE_SSL_MODE','DATABASE_CONNECT_TIMEOUT','DATABASE_POOL_SIZE',
  'DATABASE_MAX_OVERFLOW','DATABASE_POOL_TIMEOUT','DATABASE_POOL_RECYCLE','LOG_LEVEL',
  'ENABLE_DOCS','ENABLE_REDOC','ENABLE_OPENAPI','PORT','WEB_CONCURRENCY','API_PREFIX',
  'JWT_ALGORITHM','ACCESS_TOKEN_EXPIRE_MINUTES'
)

function Get-EnvValue([string]$Name) { [Environment]::GetEnvironmentVariable($Name, 'Process') }
function Add-ValidationError([string]$Message) { $errors.Add($Message) }
function Test-IntegerRange([string]$Name, [int]$Minimum, [int]$Maximum) {
  $raw = Get-EnvValue $Name
  $number = 0
  if (-not [int]::TryParse($raw, [ref]$number) -or $number -lt $Minimum -or $number -gt $Maximum) {
    Add-ValidationError "$Name must be an integer in the approved range."
  }
}

foreach ($name in $required) {
  if ([string]::IsNullOrWhiteSpace((Get-EnvValue $name))) { Add-ValidationError "$name is required." }
}

$appEnv = Get-EnvValue 'APP_ENV'
if ($appEnv -notin @('staging','production')) { Add-ValidationError 'APP_ENV must be staging or production.' }
if ($appEnv -eq 'production' -and (Get-EnvValue 'DEBUG').ToLowerInvariant() -ne 'false') {
  Add-ValidationError 'DEBUG must be false in production.'
}

$databaseUrl = Get-EnvValue 'DATABASE_URL'
if ($databaseUrl) {
  $match = [regex]::Match($databaseUrl, '^postgresql(?:\+psycopg)?://[^\s/@:]+(?::[^\s/@]*)?@(?<host>\[[^\]]+\]|[^\s/:?#]+)(?::\d+)?/[^\s?#]+$')
  if (-not $match.Success) { Add-ValidationError 'DATABASE_URL must be a structurally valid PostgreSQL URL.' }
  elseif ($appEnv -eq 'production' -and $match.Groups['host'].Value.Trim('[',']').ToLowerInvariant() -in @('localhost','127.0.0.1','::1')) {
    Add-ValidationError 'Production DATABASE_URL must not use a loopback host.'
  }
  if ($appEnv -eq 'production' -and $databaseUrl -match '^sqlite') { Add-ValidationError 'SQLite is prohibited in production.' }
}

$jwt = Get-EnvValue 'JWT_SECRET_KEY'
if ($jwt) {
  $weak = $jwt.ToLowerInvariant() -match 'placeholder|replace|example|change-me|test-only|<|>'
  $unique = @($jwt.ToCharArray() | Sort-Object -Unique).Count
  if ($jwt.Length -lt 48 -or $unique -lt 12 -or $weak) { Add-ValidationError 'JWT_SECRET_KEY fails minimum structural quality.' }
}

$origins = @((Get-EnvValue 'CORS_ORIGINS') -split ',' | Where-Object { $_ })
foreach ($origin in $origins) {
  $uri = $null
  if ($origin -eq '*' -or $origin.EndsWith('/') -or -not [uri]::TryCreate($origin, [UriKind]::Absolute, [ref]$uri) -or
      $uri.Scheme -notin @('http','https') -or -not [string]::IsNullOrEmpty($uri.UserInfo) -or
      $uri.AbsolutePath -ne '/' -or -not [string]::IsNullOrEmpty($uri.Query) -or -not [string]::IsNullOrEmpty($uri.Fragment)) {
    Add-ValidationError 'CORS_ORIGINS contains an invalid origin.'
  }
}
if ($appEnv -eq 'production' -and $origins -notcontains 'https://tidclibya2026.github.io') {
  Add-ValidationError 'Production CORS_ORIGINS must contain the confirmed exact frontend origin.'
}

foreach ($hostName in @((Get-EnvValue 'TRUSTED_HOSTS') -split ',' | Where-Object { $_ })) {
  if ($hostName -eq '*' -or $hostName -notmatch '^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$') {
    Add-ValidationError 'TRUSTED_HOSTS contains invalid syntax.'
  }
}

foreach ($proxy in @((Get-EnvValue 'FORWARDED_ALLOW_IPS') -split ',' | Where-Object { $_ })) {
  if ($proxy -eq '*') { Add-ValidationError 'Wildcard proxy trust is prohibited.'; continue }
  $parts = $proxy.Split('/', 2)
  $address = $null
  if (-not [Net.IPAddress]::TryParse($parts[0], [ref]$address)) { Add-ValidationError 'FORWARDED_ALLOW_IPS contains invalid IP/CIDR syntax.'; continue }
  if ($parts.Count -eq 2) {
    $prefix = 0; $maximum = if ($address.AddressFamily -eq [Net.Sockets.AddressFamily]::InterNetwork) { 32 } else { 128 }
    if (-not [int]::TryParse($parts[1], [ref]$prefix) -or $prefix -lt 0 -or $prefix -gt $maximum) { Add-ValidationError 'FORWARDED_ALLOW_IPS contains an invalid CIDR prefix.' }
  }
}

Test-IntegerRange 'PORT' 1024 65535
Test-IntegerRange 'WEB_CONCURRENCY' 1 64

if ($errors.Count) {
  foreach ($message in $errors) { Write-Error $message }
  Write-Output "Environment validation failed with $($errors.Count) error(s); values were not displayed."
  exit 1
}
Write-Output 'Environment validation passed; values were not displayed.'

