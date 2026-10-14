# gen_stubs.ps1 — regenerate the committed gRPC/protobuf stubs for the Go client.
#
# The client is STANDALONE: the generated stubs live in this module under
# internal/mnemovelav1 with `option go_package` pointing at THIS module, not the
# engine. We therefore generate from a TEMP COPY of the shared contract
# (contracts/mnemovela.v1.proto) whose go_package option is overridden.
#
# Prereqs (installed once, pinned to the Go 1.25.0 toolchain to avoid pulling a
# newer patch toolchain over the network):
#   $env:GOTOOLCHAIN="go1.25.0"
#   go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.11
#   go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.6.2
#
# Run from clients/go:
#   pwsh -File scripts/gen_stubs.ps1

$ErrorActionPreference = "Stop"
$env:CGO_ENABLED = "0"
$env:GOTOOLCHAIN = "go1.25.0"
$env:PATH += ";$(go env GOPATH)\bin"

$repoRoot = Resolve-Path "$PSScriptRoot\..\..\.."
$srcProto = Join-Path $repoRoot "contracts\mnemovela.v1.proto"

$tmp = Join-Path $env:TEMP "mnemegen"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

# Copy the shared contract to a flat filename and override go_package so the
# stubs are emitted into THIS module's internal/mnemovelav1 package (never modify
# the shared contract in place).
$proto = Get-Content $srcProto -Raw
$proto = $proto -replace 'option go_package = ".*";', 'option go_package = "github.com/axisrobo/mnemovela-open/clients/go/internal/mnemovelav1;mnemovelav1";'
Set-Content -Path (Join-Path $tmp "mnemovela_v1.proto") -Value $proto -NoNewline

Set-Content -Path (Join-Path $tmp "buf.yaml") -Value "version: v2`n"

$genYaml = @"
version: v2
plugins:
  - local: protoc-gen-go
    out: internal/mnemovelav1
    opt: paths=source_relative
  - local: protoc-gen-go-grpc
    out: internal/mnemovelav1
    opt: paths=source_relative
"@
Set-Content -Path (Join-Path $tmp "buf.gen.yaml") -Value $genYaml

New-Item -ItemType Directory -Force -Path "internal\mnemovelav1" | Out-Null

# protoc is not on PATH; use buf, which drives the locally-installed plugins.
go run github.com/bufbuild/buf/cmd/buf@v1.55.1 generate $tmp --template (Join-Path $tmp "buf.gen.yaml")

Write-Host "Generated internal/mnemovelav1/*.pb.go"
