# Run on the owner's PC with the two original Project archives.
# No intermediate bundle, repacking, public release, or original RGB mod download.
param(
    [Parameter(Mandatory=$true)][string]$FabricTar,
    [Parameter(Mandatory=$true)][string]$NeoForgeZip
)
$ErrorActionPreference = "Stop"
$repo = "sangkukzoa-ctrl/assets"
$branch = "rgb-blocks-legacy-compat-audit"
$tag = "rgbblocks-131-private-original-source"
$files = @(
    @{Path=$FabricTar; Name="RGB-Blocks-1.3.1-Fabric-26.1.2-full-source.tar"; SHA="ae5fffb7b37d7376f4e579491af878b7ed74fbe386b8691751e6d1c538bcb39c"},
    @{Path=$NeoForgeZip; Name="RGB-Blocks-1.3.1-NeoForge-26.1.2-full-source.zip"; SHA="f267b09141811f3eeb64e8247fff1d08ed2e11fdbea6c5b165f52b93e31607e1"}
)
function Invoke-Gh {
    & gh @args
    if ($LASTEXITCODE -ne 0) { throw "GitHub CLI failed: $($args[0]) $($args[1])" }
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "Install GitHub CLI (winget install GitHub.cli), then gh auth login."
}
Invoke-Gh auth status
foreach ($file in $files) {
    $file.Path = (Resolve-Path -LiteralPath $file.Path).Path
    if (-not (Test-Path -LiteralPath $file.Path -PathType Leaf)) {
        throw "Missing original file: $($file.Path)"
    }
    $sha=(Get-FileHash -LiteralPath $file.Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sha -ne $file.SHA) { throw "Wrong original archive SHA256: $($file.Path) ($sha)" }
    Write-Host "Original verified: $($file.Name)" -ForegroundColor Green
}
# Never upload to a published release, even if the same tag already exists.
$json = & gh release view $tag --repo $repo --json isDraft,assets 2>$null
if ($LASTEXITCODE -ne 0) {
    Invoke-Gh release create $tag --repo $repo --target $branch --draft --title "INTERNAL ONLY: RGB Blocks 1.3.1 author source for CI" --notes "Keep DRAFT. Author-original source inputs, not a public mod release."
}
function Assert-Draft {
    $release = Invoke-Gh release view $tag --repo $repo --json isDraft,assets | ConvertFrom-Json
    if ($release.isDraft -ne $true) { throw "Refusing public source release. DRAFT required." }
    if (@($release.assets | Where-Object name -eq "RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst").Count -gt 0) {
        throw "Canonical bundle already present. Use existing canonical provisioning script instead of mixing transports."
    }
}
Assert-Draft
# Fail closed until BOTH remote bytes and draft status have been verified.
Invoke-Gh variable set RGB_OWNER_SOURCE_READY --body "false" --repo $repo
$temp = Join-Path ([IO.Path]::GetTempPath()) ("rgbowner-pair-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temp -Force | Out-Null
try {
    foreach ($file in $files) {
        Assert-Draft
        $upload = $file.Path
        $renamed = $false
        if ((Split-Path -Leaf $upload) -ne $file.Name) {
            $upload = Join-Path $temp $file.Name
            Copy-Item -LiteralPath $file.Path -Destination $upload
            $renamed = $true
        }
        try {
            Invoke-Gh release upload $tag $upload --repo $repo --clobber
        } finally {
            if ($renamed) { Remove-Item -LiteralPath $upload -Force }
        }
        Assert-Draft
        Invoke-Gh release download $tag --repo $repo --pattern $file.Name --dir $temp --clobber
        $download = Join-Path $temp $file.Name
        $remote=(Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($remote -ne $file.SHA) { throw "Remote original SHA mismatch: $($file.Name)" }
        Remove-Item -LiteralPath $download -Force
        Write-Host "Remote DRAFT verified: $($file.Name)" -ForegroundColor Green
    }
    Assert-Draft
    Invoke-Gh variable set RGB_OWNER_SOURCE_READY --body "true" --repo $repo
    foreach ($workflow in @(
        "rgb-blocks-cnb-post-login-and-distant-rapid-bake.yml",
        "rgb-blocks-cnb-seeded-chaos-real-clients.yml"
    )) {
        Invoke-Gh workflow run $workflow --repo $repo --ref $branch
        Write-Host "Dispatched native matrix: $workflow" -ForegroundColor Cyan
    }
    Write-Host "Both original archives are SHA-verified and remain DRAFT. No public release." -ForegroundColor Green
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
