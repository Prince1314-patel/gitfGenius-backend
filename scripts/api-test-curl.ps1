# GiftGenius API - Comprehensive curl-based test script
# Run with: .\scripts\api-test-curl.ps1
# Requires: backend running on http://localhost:8000

$base = "http://localhost:8000"
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$user1Email = "curltest1_$timestamp@example.com"
$user2Email = "curltest2_$timestamp@example.com"
$results = @()
$token1 = $null
$token2 = $null
$contactId1 = $null
$contactId2 = $null
$user2ContactId = $null
$testDir = "scripts\curl-test-bodies"
if (-not (Test-Path $testDir)) { New-Item -ItemType Directory -Path $testDir -Force | Out-Null }

function Run-CurlTest {
    param([string]$Name, [string]$Method, [string]$Url, [object]$Body = $null, [string]$Token = $null)
    $bodyFile = $null
    if ($Body -ne $null) {
        $bodyFile = "$testDir\body_$([Guid]::NewGuid().ToString('N').Substring(0,8)).json"
        if ($Body -is [string]) { $Body | Set-Content -Path $bodyFile -Encoding UTF8 -NoNewline }
        else { $Body | ConvertTo-Json -Compress | Set-Content -Path $bodyFile -Encoding UTF8 -NoNewline }
    }
    $curlArgs = @("-s", "-w", "`n%{http_code}|%{time_total}", "-X", $Method, $Url)
    if ($bodyFile) { $curlArgs += @("-H", "Content-Type: application/json", "-d", "@$bodyFile") }
    if ($Token) { $curlArgs += @("-H", "Authorization: Bearer $Token") }
    $out = & curl.exe @curlArgs 2>&1
    if ($bodyFile -and (Test-Path $bodyFile)) { Remove-Item $bodyFile -Force }
    $lines = $out -split "`n"
    $last = $lines[-1]
    $code = ($last -split "\|")[0]
    $time = ($last -split "\|")[1]
    $bodyOut = ($lines[0..([Math]::Max(0, $lines.Length-2))] -join "`n").Trim()
    return @{ Name = $Name; Code = $code; Time = $time; Body = $bodyOut }
}

Write-Host "=== GiftGenius API Full Test Suite ===" -ForegroundColor Cyan
Write-Host "Base: $base | Timestamp: $timestamp`n" -ForegroundColor Gray

# --- 1. PUBLIC / HEALTH ---
$r = Run-CurlTest -Name "GET / root" -Method GET -Url "$base/"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "GET /health" -Method GET -Url "$base/health"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

# --- 2. AUTH: REGISTER ---
$r = Run-CurlTest -Name "POST register (email+password only)" -Method POST -Url "$base/api/v1/auth/register" -Body (@{ email = $user1Email; password = "SecurePass123!" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
if ($r.Code -eq "200" -or $r.Code -eq "201") {
    $json = $r.Body | ConvertFrom-Json
    $token1 = $json.data.access_token
    Write-Host "  -> Token received (length $($token1.Length))" -ForegroundColor Green
}
$r = Run-CurlTest -Name "POST register (with full_name)" -Method POST -Url "$base/api/v1/auth/register" -Body (@{ email = $user2Email; password = "PassWord99!"; full_name = "Curl Test User" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
if ($r.Code -eq "200" -or $r.Code -eq "201") {
    $token2 = ($r.Body | ConvertFrom-Json).data.access_token
}
$r = Run-CurlTest -Name "POST register duplicate email" -Method POST -Url "$base/api/v1/auth/register" -Body (@{ email = $user1Email; password = "SecurePass123!" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST register missing email" -Method POST -Url "$base/api/v1/auth/register" -Body (@{ password = "SecurePass123!" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST register short password" -Method POST -Url "$base/api/v1/auth/register" -Body (@{ email = "short@example.com"; password = "short" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST register invalid email" -Method POST -Url "$base/api/v1/auth/register" -Body (@{ email = "not-an-email"; password = "SecurePass123!" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST register empty body" -Method POST -Url "$base/api/v1/auth/register" -Body "{}"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST register malformed JSON" -Method POST -Url "$base/api/v1/auth/register" -Body "{invalid"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

# --- 3. AUTH: LOGIN ---
$r = Run-CurlTest -Name "POST login valid" -Method POST -Url "$base/api/v1/auth/login" -Body (@{ email = $user1Email; password = "SecurePass123!" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST login wrong password" -Method POST -Url "$base/api/v1/auth/login" -Body (@{ email = $user1Email; password = "WrongPass123!" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST login non-existent email" -Method POST -Url "$base/api/v1/auth/login" -Body (@{ email = "nonexistent$timestamp@example.com"; password = "SecurePass123!" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST login missing fields" -Method POST -Url "$base/api/v1/auth/login" -Body "{}"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

# --- 4. AUTH: PROFILE ---
$r = Run-CurlTest -Name "GET profile with token" -Method GET -Url "$base/api/v1/auth/profile" -Token $token1
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "GET profile without token" -Method GET -Url "$base/api/v1/auth/profile"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "GET profile invalid token" -Method GET -Url "$base/api/v1/auth/profile" -Token "invalid.jwt.token"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

# --- 5. CONTACTS ---
$r = Run-CurlTest -Name "POST contact without auth" -Method POST -Url "$base/api/v1/contacts" -Body (@{ name = "Alice"; relationship_type = "Friend" })
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "POST contact valid" -Method POST -Url "$base/api/v1/contacts" -Body (@{ name = "Alice Friend"; relationship_type = "Friend"; birthday = "1990-05-15" }) -Token $token1
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
if ($r.Code -eq "201" -and $r.Body) {
    $contactId1 = ($r.Body | ConvertFrom-Json).data.id
    Write-Host "  -> Contact ID: $contactId1" -ForegroundColor Green
}
$r = Run-CurlTest -Name "POST contact minimal (name only)" -Method POST -Url "$base/api/v1/contacts" -Body (@{ name = "Bob" }) -Token $token1
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
if ($r.Code -eq "201" -and $r.Body) { $contactId2 = ($r.Body | ConvertFrom-Json).data.id }
$r = Run-CurlTest -Name "POST contact as user2" -Method POST -Url "$base/api/v1/contacts" -Body (@{ name = "Charlie"; relationship_type = "Colleague" }) -Token $token2
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
if ($r.Code -eq "201" -and $r.Body) { $user2ContactId = ($r.Body | ConvertFrom-Json).data.id }
$r = Run-CurlTest -Name "POST contact empty name" -Method POST -Url "$base/api/v1/contacts" -Body (@{ name = "" }) -Token $token1
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

$r = Run-CurlTest -Name "GET contacts list" -Method GET -Url "$base/api/v1/contacts" -Token $token1
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "GET contacts without auth" -Method GET -Url "$base/api/v1/contacts"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

if ($contactId1) {
    $r = Run-CurlTest -Name "GET contact by id" -Method GET -Url "$base/api/v1/contacts/$contactId1" -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "GET contact by id without auth" -Method GET -Url "$base/api/v1/contacts/$contactId1"
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "GET contact other user (403)" -Method GET -Url "$base/api/v1/contacts/$contactId1" -Token $token2
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
}
$r = Run-CurlTest -Name "GET contact invalid UUID" -Method GET -Url "$base/api/v1/contacts/not-a-uuid" -Token $token1
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$fakeUuid = "00000000-0000-0000-0000-000000000000"
$r = Run-CurlTest -Name "GET contact non-existent UUID" -Method GET -Url "$base/api/v1/contacts/$fakeUuid" -Token $token1
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

# --- 6. MEMORIES ---
if ($contactId1) {
    $r = Run-CurlTest -Name "POST memory without auth" -Method POST -Url "$base/api/v1/contacts/$contactId1/memories" -Body (@{ content = "Some memory" })
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "POST memory valid" -Method POST -Url "$base/api/v1/contacts/$contactId1/memories" -Body (@{ content = "Alice loves matcha tea" }) -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "POST memory empty content" -Method POST -Url "$base/api/v1/contacts/$contactId1/memories" -Body (@{ content = "" }) -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "POST memory to other user contact (403)" -Method POST -Url "$base/api/v1/contacts/$contactId1/memories" -Body (@{ content = "Hack" }) -Token $token2
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "POST memory to non-existent contact" -Method POST -Url "$base/api/v1/contacts/$fakeUuid/memories" -Body (@{ content = "Test" }) -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "GET memories list" -Method GET -Url "$base/api/v1/contacts/$contactId1/memories" -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Name)"
    $r = Run-CurlTest -Name "GET memories without auth" -Method GET -Url "$base/api/v1/contacts/$contactId1/memories"
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "GET memories other user (403)" -Method GET -Url "$base/api/v1/contacts/$contactId1/memories" -Token $token2
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
}

# --- 7. DELETE ---
if ($contactId2) {
    $r = Run-CurlTest -Name "DELETE contact" -Method DELETE -Url "$base/api/v1/contacts/$contactId2" -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
    $r = Run-CurlTest -Name "DELETE contact again (404)" -Method DELETE -Url "$base/api/v1/contacts/$contactId2" -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
}
$r = Run-CurlTest -Name "DELETE contact without auth" -Method DELETE -Url "$base/api/v1/contacts/$contactId1" -Token $null
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
if ($user2ContactId) {
    $r = Run-CurlTest -Name "DELETE other user contact (403)" -Method DELETE -Url "$base/api/v1/contacts/$user2ContactId" -Token $token1
    $results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
}

# --- 8. WRONG METHOD / CORS ---
$r = Run-CurlTest -Name "GET /api/v1/auth/register (405)" -Method GET -Url "$base/api/v1/auth/register"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"
$r = Run-CurlTest -Name "OPTIONS /api/v1/contacts (CORS)" -Method OPTIONS -Url "$base/api/v1/contacts"
$results += $r; Write-Host "[$($r.Code)] $($r.Time)s - $($r.Name)"

# --- 9. RESPONSE TIME ---
Write-Host "`n--- Response time sampling (5x GET /) ---" -ForegroundColor Gray
$times = @()
1..5 | ForEach-Object { $r = Run-CurlTest -Method GET -Url "$base/"; $times += [double]$r.Time }
$avg = ($times | Measure-Object -Average).Average
$results += @{ Name = "GET / avg (5 runs)"; Code = "N/A"; Time = [string]$avg; Body = "" }
Write-Host "  Average: $([math]::Round($avg, 4))s" -ForegroundColor Cyan

$passed = ($results | Where-Object { $_.Code -match "^(200|201)$" }).Count
$clientErr = ($results | Where-Object { $_.Code -match "^(400|401|403|404|405|409|422)$" }).Count
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Total: $($results.Count) | 2xx: $passed | 4xx/5xx: $clientErr"
$results | ConvertTo-Json -Depth 3 | Set-Content -Path "scripts\api-test-results.json" -Encoding UTF8
Write-Host "Results: scripts\api-test-results.json" -ForegroundColor Green
