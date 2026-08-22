# Publish Mnemovela-open mirror + binaries to a GitHub release (full core->open flow).
#
# Covers the complete open-release flow from the AGENTS.md tagging workflow:
#   1. Mirror the core into Mnemovela-open (publish_open.py --apply)
#   2. Commit + push the mirror changes on open main
#   3. Tag + push the same vX.Y.Z on open
#   4. Build cross-platform binaries and attach them to the GitHub release
#      (release body taken from docs/RELEASE-vX.Y.Z.md)
#
# Uses Invoke-RestMethod with `gh auth token` for the GitHub API (the HTTPS
# proxy blocks gh's own HTTP client; gh is only used to mint the token).
#
# Prerequisites: gh CLI authenticated, Go toolchain, core tag exists.
# Run from the private repo root.
#
# Usage:
#   .\scripts\publish_release.ps1 <tag>
#
# Example:
#   .\scripts\publish_release.ps1 v0.15.0

param([string] $Tag)

$ErrorActionPreference = "Stop"

if (-not $Tag) {
    Write-Host "Usage: publish_release.ps1 <tag>" -ForegroundColor Red
    exit 1
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$openDir = Join-Path $repoRoot "..\Mnemovela-open"

# --- 1. Mirror core -> open -------------------------------------------------
Push-Location $repoRoot
try {
    Write-Host "Mirroring core -> open ($Tag)..."
    & py -3.13 scripts\publish_open.py --apply
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }

# --- 2. Commit + push the mirror changes -------------------------------------
git -C $openDir add -A
$dirty = git -C $openDir status --porcelain
if ($dirty) {
    git -C $openDir commit -m "chore: mirror sync (core $Tag state)"
    git -C $openDir push origin main
} else {
    Write-Host "Open mirror has no changes beyond the previous sync."
}

# --- 3. Tag + push open ------------------------------------------------------
Write-Host "Tagging Mnemovela-open $Tag..."
if (git -C $openDir rev-parse -q --verify "refs/tags/$Tag") {
    Write-Host "Tag $Tag already exists on open; re-pointing to HEAD."
    git -C $openDir tag -d $Tag
    git -C $openDir push origin ":refs/tags/$Tag"
}
git -C $openDir tag -a $Tag -m "$Tag"
git -C $openDir push origin $Tag

# --- 4. Build binaries --------------------------------------------------------
Write-Host "Building binaries for all platforms..."
Push-Location $repoRoot
try {
    & py -3.13 scripts\build_open_binaries.py --all
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }

# --- 5. Create the GitHub release --------------------------------------------
$notes = "Prebuilt Mnemovela embedded server binaries for $Tag.`n`n- mnemovela-http: JSON-RPC-over-HTTP + REST`n- mnemovela-grpc: gRPC`n- mnemovela-jsonrpc-stdio: JSON-RPC over stdio`n- mnemovela-mcp-stdio: MCP server over stdio`n`nBuilt with CGO_ENABLED=0, embedded backends only.`n`nPlatforms: windows/amd64, linux/amd64, darwin/amd64, darwin/arm64.`n`nAssets are named `<binary>-<platform>-<arch>` (e.g. `mnemovela-http-linux-amd64`); `checksums-<platform>-<arch>.txt` per platform.`n`nSee BINARY-LICENSE.md for distribution terms."
$releaseDoc = Join-Path $repoRoot "docs\RELEASE-$Tag.md"
if (Test-Path $releaseDoc) {
    $notes = [System.IO.File]::ReadAllText((Resolve-Path $releaseDoc)) + "`n`n---`n`n" + $notes
}

$token = gh auth token
$headers = @{ Authorization = "Bearer $token"; Accept = "application/vnd.github+json" }
$uri = "https://api.github.com/repos/axisrobo/mnemovela-open/releases"

# Delete an existing release for this tag, if any, so re-runs are idempotent.
try {
    $existing = Invoke-RestMethod -Method Get -Headers $headers -Uri "$uri/tags/$Tag"
    if ($existing) {
        Invoke-RestMethod -Method Delete -Headers $headers -Uri "$uri/$($existing.id)"
        Write-Host "Removed existing release $Tag (id $($existing.id))."
    }
} catch {
    Write-Host "No existing release for $Tag; creating fresh."
}

$body = @{ tag_name = $Tag; name = $Tag; body = $notes } | ConvertTo-Json -Depth 3
$release = Invoke-RestMethod -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Uri $uri -Body ([System.Text.Encoding]::UTF8.GetBytes($body))

# Upload binary assets (platform-prefixed names so all platforms coexist).
# dist/open layout: dist/open/<platform-arch>/<binary>[.exe] + checksums.txt.
$platDirs = Get-ChildItem -Directory (Join-Path $repoRoot "dist\open") -ErrorAction SilentlyContinue
foreach ($dir in $platDirs) {
    $plat = $dir.Name
    $bins = Get-ChildItem $dir.FullName -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^(mnemovela-|checksums)" }
    foreach ($bin in $bins) {
        $full = $bin.Name
        $base = $full
        if ($full -like "*.exe") { $base = $full.Substring(0, $full.Length - 4) }
        $assetName = ""
        if ($full -eq "checksums.txt") {
            $assetName = "checksums-" + $plat + ".txt"
        } elseif ($full -like "*.exe") {
            $assetName = $base + "-" + $plat + ".exe"
        } else {
            $assetName = $base + "-" + $plat
        }
        $name = [System.Uri]::EscapeDataString($assetName)
        $assetUri = $release.upload_url -replace "\{\?name,label\}", "" + "?name=" + $name
        $assetBody = [System.IO.File]::ReadAllBytes($bin.FullName)
        try {
            Invoke-RestMethod -Method Post -Headers @{ Authorization = "Bearer $token"; Accept = "application/vnd.github+json"; "Content-Type" = "application/octet-stream" } -Uri $assetUri -Body $assetBody | Out-Null
            Write-Host "  uploaded ${assetName}"
        } catch {
            Write-Host "  FAILED upload ${assetName}: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

Write-Host "Done. Verify at https://github.com/axisrobo/mnemovela-open/releases/tag/$Tag"
