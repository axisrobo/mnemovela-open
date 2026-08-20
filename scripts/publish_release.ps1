# Publish Mnemovela-open binaries to a GitHub release.
#
# Prerequisites: gh CLI authenticated, Go toolchain, git tag for the release.
# Run from the private repo root.
#
# Usage:
#   publish_release.ps1 <tag>
#
# Example:
#   .\scripts\publish_release.ps1 v0.1.0

param([string] $Tag)

$ErrorActionPreference = "Stop"

if (-not $Tag) {
    Write-Host "Usage: publish_release.ps1 <tag>" -ForegroundColor Red
    exit 1
}

Write-Host "Building binaries for all platforms..."
python scripts/build_open_binaries.py --all
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$openDir = "D:\profile\paper-code\Mnemovela-open"
Write-Host "Tagging Mnemovela-open $Tag..."
git -C $openDir tag $Tag
git -C $openDir push origin $Tag

Write-Host "Creating release and uploading binaries..."
gh release create $Tag dist/open/**/* `
    --repo axisrobo/mnemovela-open `
    --title "Mnemovela-open $Tag" `
    --notes "Prebuilt Mnemovela embedded server binaries for $Tag.`n`n- mnemovela-http: JSON-RPC-over-HTTP + REST`n- mnemovela-grpc: gRPC`n- mnemovela-jsonrpc-stdio: JSON-RPC over stdio`n- mnemovela-mcp-stdio: MCP server over stdio`n`nBuilt with CGO_ENABLED=0, embedded backends only.`n`nPlatforms: windows/amd64, linux/amd64, darwin/amd64, darwin/arm64.`n`nSee BINARY-LICENSE.md for distribution terms."

Write-Host "Done. Verify at https://github.com/axisrobo/mnemovela-open/releases/tag/$Tag"