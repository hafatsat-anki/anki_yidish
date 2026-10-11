param([Parameter(Mandatory=$true)][string]$InstallRoot)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($InstallRoot)
$package = Join-Path $root 'payload-addons'
$target = Join-Path $root 'Data\addons21'
$policyPath = Join-Path $PSScriptRoot 'addon_settings_policy.json'
$policy = Get-Content -LiteralPath $policyPath -Raw -Encoding UTF8 | ConvertFrom-Json
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'addons.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$backup = Join-Path $root ('Data\settings-backups\' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fffffff'))
[IO.Directory]::CreateDirectory($backup) | Out-Null
[IO.Directory]::CreateDirectory($target) | Out-Null
$names = [Collections.Generic.List[string]]::new()
foreach ($addon in $manifest) {
    $name = [string]$addon.deploy
    if ($name -notmatch '^[a-z0-9][a-z0-9-]*$') { throw 'Invalid addon directory in package.' }
    $src = Join-Path $package $name
    $dst = Join-Path $target $name
    if (-not (Test-Path -LiteralPath (Join-Path $src 'meta.json'))) { throw 'Missing addon package.' }
    $saved = Join-Path $backup $name
    [IO.Directory]::CreateDirectory($saved) | Out-Null
    $files = @('config.json', 'meta.json')
    $personal = $policy.user_data_files.PSObject.Properties[$name]
    if ($null -ne $personal) { $files += @($personal.Value) }
    foreach ($file in $files) {
        $existing = Join-Path $dst $file
        if (Test-Path -LiteralPath $existing) {
            $copy = Join-Path $saved $file
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($copy)) | Out-Null
            Copy-Item -LiteralPath $existing -Destination $copy -Force
            if ((Get-FileHash -LiteralPath $existing).Hash -ne (Get-FileHash -LiteralPath $copy).Hash) {
                throw 'Saved settings backup verification failed.'
            }
            if ($file.EndsWith('.json') -and $file -in @('config.json','meta.json')) {
                $obj = Get-Content -LiteralPath $copy -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($obj -isnot [pscustomobject]) { throw 'Existing settings must be a JSON object.' }
            }
        }
    }
    $names.Add($name)
}
# No existing addon directory is deleted. Personal files are absent from package.
foreach ($name in $names) {
    $src = Join-Path $package $name
    $dst = Join-Path $target $name
    [IO.Directory]::CreateDirectory($dst) | Out-Null
    foreach ($entry in Get-ChildItem -LiteralPath $src -Force) {
        Copy-Item -LiteralPath $entry.FullName -Destination $dst -Recurse -Force
    }
}
$shared = Join-Path $target '_shared_libs'
[IO.Directory]::CreateDirectory($shared) | Out-Null
foreach ($entry in Get-ChildItem -LiteralPath (Join-Path $package '_shared_libs') -Force) {
    Copy-Item -LiteralPath $entry.FullName -Destination $shared -Recurse -Force
}
$list = Join-Path $backup 'addons.txt'
[IO.File]::WriteAllLines($list, $names.ToArray(), [Text.Encoding]::Unicode)
& (Join-Path $PSScriptRoot 'merge_modern_theme_config.ps1') -AddonsPath $target -BackupPath $backup -AddonList $list -PolicyPath $policyPath -ReportPath (Join-Path $root 'Data\haf-addon-settings-upgrade.json')
if (-not $?) { throw 'Settings merge failed; backups retained.' }
[IO.File]::WriteAllText((Join-Path $root 'distribution.json'), '{"distribution":"anki-yidish","version":"25.9.2-yi.1","language":"yi"}', [Text.UTF8Encoding]::new($false))
