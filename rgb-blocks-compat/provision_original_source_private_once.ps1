# One-time local operation by the RGB Blocks author. Requires GitHub CLI (gh).
# A DRAFT release is deliberately not public: preserve All-Rights-Reserved source.
param(
    [string]$SourceBundle = (Join-Path $PSScriptRoot "RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst")
)
$ErrorActionPreference = "Stop"
$repo = "sangkukzoa-ctrl/assets"
$tag = "rgbblocks-131-private-original-source"
$filename = "RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst"
$expected = "1aea93f67e0375ecea72c86a5a72add5488d43d87a6b058dbce93128f250d007"
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI 'gh' must be installed and authenticated (gh auth login)."
}
if (-not (Test-Path -LiteralPath $SourceBundle -PathType Leaf)) {
    throw "Author-original bundle not found: $SourceBundle"
}
$sha=(Get-FileHash -LiteralPath $SourceBundle -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sha -ne $expected) { throw "WRONG original 1.3.1 source SHA256 ($sha)" }
if ((Split-Path -Leaf $SourceBundle) -ne $filename) {
    throw "Keep the exact canonical filename: $filename"
}
$draft= & gh release view $tag --repo $repo --json isDraft --jq ".isDraft" 2>$null
if ($LASTEXITCODE -ne 0) {
    & gh release create $tag --repo $repo --target rgb-blocks-legacy-compat-audit --draft `
        --title "INTERNAL ONLY: RGB Blocks 1.3.1 author source for CI" `
        --notes "Author-provided source input. Keep this release DRAFT; never publish this All-Rights-Reserved source."
    if ($LASTEXITCODE -ne 0) { throw "Cannot create private DRAFT release" }
} elseif ("$draft".Trim().ToLowerInvariant() -ne "true") {
    throw "Refusing to upload to a PUBLIC source release. Draft is required."
}
& gh release upload $tag $SourceBundle --repo $repo --clobber
if ($LASTEXITCODE -ne 0) { throw "Private author-source upload failed" }
# Source must be verified again AFTER GitHub stored it. A successful
# gh release upload return code is not enough: do not enable expensive native
# builds until the exact SHA-pinned archive can be downloaded from DRAFT.
$verifyDir = Join-Path ([IO.Path]::GetTempPath()) ("rgbowner-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $verifyDir -Force | Out-Null
try {
    & gh release download $tag --repo $repo --pattern $filename --dir $verifyDir
    if ($LASTEXITCODE -ne 0) {
        throw "Uploaded author source cannot be re-downloaded from the DRAFT release"
    }
    $verifiedFile=Join-Path $verifyDir $filename
    if (-not (Test-Path -LiteralPath $verifiedFile -PathType Leaf)) {
        throw "GitHub DRAFT source asset is missing after upload: $filename"
    }
    $remoteSha=(Get-FileHash -LiteralPath $verifiedFile -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($remoteSha -ne $expected) {
        throw "GitHub DRAFT source asset SHA-256 mismatch ($remoteSha); CI remains disabled"
    }
    $remoteDraft=& gh release view $tag --repo $repo --json isDraft --jq ".isDraft"
    if ($LASTEXITCODE -ne 0 -or "$remoteDraft".Trim().ToLowerInvariant() -ne "true") {
        throw "DRAFT protection lost; refusing to enable owner-original CI"
    }
    Write-Host "Private GitHub DRAFT source downloaded and verified, SHA-256 $remoteSha" -ForegroundColor Green
}
finally {
    Remove-Item -LiteralPath $verifyDir -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "Original source SHA256 verified, uploaded to GitHub draft release (NOT public)." -ForegroundColor Green
Write-Host "Artifact: $filename"
Write-Host "Release tag: $tag"
Write-Host "The CI now downloads only this pinned author source; no RGB Blocks Modrinth JAR."
# Allow later pushes to run source-gated game CI automatically. Before this
# point they are SKIPPED, not failed on repeated missing-release HTTP 404s.
& gh variable set RGB_OWNER_SOURCE_READY --body "true" --repo $repo
if ($LASTEXITCODE -ne 0) { throw "Cannot activate owner-verified CI source gate" }
Write-Host "Author source verified; CI source gate now activated." -ForegroundColor Green
# Resume both exact 1.20.1/1.21.1 regression matrices immediately.
foreach ($workflow in @(
    "rgb-blocks-cnb-post-login-and-distant-rapid-bake.yml",
    "rgb-blocks-cnb-seeded-chaos-real-clients.yml"
)) {
    & gh workflow run $workflow --repo $repo --ref rgb-blocks-legacy-compat-audit
    if ($LASTEXITCODE -ne 0) {
        throw "Source upload succeeded, but cannot start CI workflow: $workflow"
    }
    Write-Host "Started strict source-first CI: $workflow" -ForegroundColor Cyan
}
