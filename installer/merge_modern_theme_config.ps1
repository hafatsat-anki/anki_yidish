[CmdletBinding(DefaultParameterSetName='Single')]
param(
    [Parameter(Mandatory=$true, ParameterSetName='Single')][string]$InstalledConfig,
    [Parameter(ParameterSetName='Single')][string]$SavedConfig,
    [Parameter(ParameterSetName='Single')][string]$InstalledMeta,
    [Parameter(ParameterSetName='Single')][string]$SavedMeta,
    [Parameter(ParameterSetName='Single')][string]$AddonName = 'modern-theme',
    [Parameter(Mandatory=$true, ParameterSetName='Batch')][string]$AddonsPath,
    [Parameter(Mandatory=$true, ParameterSetName='Batch')][string]$BackupPath,
    [Parameter(Mandatory=$true, ParameterSetName='Batch')][string]$AddonList,
    [Parameter(ParameterSetName='Batch')][string]$ReportPath,
    [string]$PolicyPath
)
$ErrorActionPreference = 'Stop'
if (-not $PolicyPath) { $PolicyPath = Join-Path $PSScriptRoot 'addon_settings_policy.json' }

# Shared installer upgrade: missing fields come from the new package, saved values win.
# Arrays are user-owned lists, not dictionaries: never merge them by array index.
function Merge-Settings($Defaults, $Saved, [string]$Location) {
    foreach ($property in $Saved.PSObject.Properties) {
        $existing = $Defaults.PSObject.Properties[$property.Name]
        if ($null -ne $existing -and $null -eq $property.Value -and $null -ne $existing.Value) {
            Write-Output "Restored null setting: $Location.$($property.Name)"
            continue
        }
        if ($null -ne $existing -and $existing.Value -is [System.Management.Automation.PSCustomObject]) {
            if ($null -eq $property.Value) {
                Write-Output "Restored missing object: $Location.$($property.Name)"
            } elseif ($property.Value -is [System.Management.Automation.PSCustomObject]) {
                Merge-Settings $existing.Value $property.Value "$Location.$($property.Name)"
            } else {
                throw "Expected a settings object at $Location.$($property.Name). Original settings are backed up."
            }
        } else {
            $Defaults | Add-Member -MemberType NoteProperty -Name $property.Name -Value $property.Value -Force
        }
    }
}
function Read-Settings([string]$Path) {
    $value = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8) | ConvertFrom-Json
    if ($value -isnot [System.Management.Automation.PSCustomObject]) {
        throw "Configuration must be a JSON object: $Path"
    }
    return $value
}
function Get-Setting($Object, [string[]]$Keys) {
    foreach ($key in $Keys) {
        if ($Object -isnot [System.Management.Automation.PSCustomObject]) { return @{ Present = $false; Value = $null } }
        $property = $Object.PSObject.Properties[$key]
        if ($null -eq $property) { return @{ Present = $false; Value = $null } }
        $Object = $property.Value
    }
    return @{ Present = $true; Value = $Object }
}
function Set-Setting($Object, [string[]]$Keys, $Value) {
    for ($index = 0; $index -lt $Keys.Count - 1; $index++) {
        $key = $Keys[$index]
        if ($null -eq $Object.PSObject.Properties[$key]) {
            $Object | Add-Member -MemberType NoteProperty -Name $key -Value ([pscustomobject]@{})
        }
        $Object = $Object.PSObject.Properties[$key].Value
    }
    $Object | Add-Member -MemberType NoteProperty -Name $Keys[-1] -Value $Value -Force
}
function Write-Settings([string]$Path, $Value) {
    $temporary = $Path + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 100), (New-Object Text.UTF8Encoding($false)))
        if (Test-Path -LiteralPath $Path) {
            for ($attempt = 0; $attempt -lt 4; $attempt++) {
                try {
                    [IO.File]::Replace($temporary, $Path, [NullString]::Value)
                    break
                } catch {
                    $fileError = $_.Exception
                    while ($fileError.InnerException) { $fileError = $fileError.InnerException }
                    $windowsError = $fileError.HResult -band 0xFFFF
                    # Sharing/lock violations and ERROR_UNABLE_TO_REMOVE_REPLACED.
                    # Retry the atomic operation only; never delete or overwrite as a fallback.
                    if ($windowsError -in @(32, 33, 1175) -and $attempt -lt 3 -and
                        (Test-Path -LiteralPath $temporary) -and (Test-Path -LiteralPath $Path)) {
                        Start-Sleep -Milliseconds (100 * ($attempt + 1))
                        continue
                    }
                    throw "Atomic settings replacement failed at $Path (Windows error ${windowsError}): $($fileError.Message)"
                }
            }
        } else {
            [IO.File]::Move($temporary, $Path)
        }
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
    }
}
function Upgrade-AddonSettings(
    [string]$InstalledConfig, [string]$SavedConfig, [string]$InstalledMeta,
    [string]$SavedMeta, [string]$AddonName, $Policy
) {
    $hasPackageConfig = Test-Path -LiteralPath $InstalledConfig
    $hasSavedConfig = $SavedConfig -and (Test-Path -LiteralPath $SavedConfig)
    $hasSavedMeta = $SavedMeta -and (Test-Path -LiteralPath $SavedMeta)
    $defaults = if ($hasPackageConfig) { Read-Settings $InstalledConfig } else { [pscustomobject]@{} }
    $packageDefaults = ($defaults | ConvertTo-Json -Depth 100) | ConvertFrom-Json
    $saved = [pscustomobject]@{}
    $rawOverrides = $null
    $release = $null
    if ($AddonName -eq 'modern-theme' -and $hasPackageConfig) {
        $release = $defaults.distribution_version
        if ($release -isnot [string] -or [string]::IsNullOrWhiteSpace($release)) {
            throw 'The new package is missing distribution_version.'
        }
    }
    if ($hasSavedConfig) {
        $saved = Read-Settings $SavedConfig
        Merge-Settings $defaults $saved "$AddonName.config"
    }
    if ($null -ne $release) { $defaults.distribution_version = $release }
    $meta = $null
    if ($InstalledMeta) {
        $meta = if (Test-Path -LiteralPath $InstalledMeta) { Read-Settings $InstalledMeta } else { [pscustomobject]@{} }
        if ($hasSavedMeta) {
            $savedMetadata = Read-Settings $SavedMeta
            foreach ($property in $savedMetadata.PSObject.Properties) {
                if ($policy.package_meta_fields -notcontains $property.Name) {
                    $meta | Add-Member -MemberType NoteProperty -Name $property.Name -Value $property.Value -Force
                }
            }
        }
        if ($null -ne $meta.PSObject.Properties['disabled'] -and $meta.disabled -isnot [bool]) { throw 'meta.disabled must be a boolean.' }
        if ($policy.forced_disabled -contains $AddonName) { Set-Setting $meta @('disabled') $true }
        $overrides = $meta.PSObject.Properties['config']
        if ($null -ne $overrides) {
            if ($null -eq $overrides.Value) {
                Write-Output "Restored null user configuration: $AddonName.meta.config"
            } elseif ($overrides.Value -is [System.Management.Automation.PSCustomObject]) {
                $rawOverrides = $overrides.Value
                # Anki uses a shallow dict.update. Complete nested overrides BEFORE it loads them.
                $effective = ($defaults | ConvertTo-Json -Depth 100) | ConvertFrom-Json
                Merge-Settings $effective $overrides.Value "$AddonName.meta.config"
                if ($null -ne $release) { $effective.distribution_version = $release }
                $meta.config = $effective
            } else {
                throw "Expected a settings object at $AddonName.meta.config. Original settings are backed up."
            }
            if ($null -eq $overrides.Value) { $meta.config = $defaults }
        }
    }
    $packageFields = $policy.package_config.PSObject.Properties[$AddonName]
    if ($null -ne $packageFields) {
        foreach ($keys in $packageFields.Value) {
            $setting = Get-Setting $packageDefaults $keys
            if ($setting.Present) {
                Set-Setting $defaults $keys $setting.Value
                if ($null -ne $meta -and $null -ne $meta.PSObject.Properties['config']) {
                    Set-Setting $meta.config $keys $setting.Value
                }
            }
        }
    }
    $markers = $policy.migration_markers.PSObject.Properties[$AddonName]
    if (($hasSavedConfig -or $hasSavedMeta) -and $null -ne $markers) {
        foreach ($marker in $markers.Value) {
            $old = Get-Setting $saved $marker.path
            $oldOverride = Get-Setting $rawOverrides $marker.path
            $value = if ($old.Present) { $old.Value } else { $marker.initial }
            Set-Setting $defaults $marker.path $value
            if ($null -ne $meta -and $null -ne $meta.PSObject.Properties['config']) {
                $effectiveValue = if ($oldOverride.Present) { $oldOverride.Value } else { $value }
                Set-Setting $meta.config $marker.path $effectiveValue
            }
        }
    }
    # Parse and validate both layers before modifying either destination.
    if ($hasPackageConfig -or $hasSavedConfig) { Write-Settings $InstalledConfig $defaults }
    if ($null -ne $meta) { Write-Settings $InstalledMeta $meta }
    Write-Output "Upgraded settings: $AddonName"
}

$clock = [Diagnostics.Stopwatch]::StartNew()
$completed = [Collections.Generic.List[object]]::new()
$currentAddon = $null
try {
    $policy = Read-Settings $PolicyPath
    if ($policy.schema_version -ne 1) { throw 'Unsupported settings policy version.' }
    if ($PSCmdlet.ParameterSetName -eq 'Single') {
        Upgrade-AddonSettings $InstalledConfig $SavedConfig $InstalledMeta $SavedMeta $AddonName $policy
    } else {
        # NSIS supplies only classified distribution folders that have settings.
        # Validate every name before modifying any destination. Never infer ownership.
        $names = [Collections.Generic.List[string]]::new()
        $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($name in [IO.File]::ReadAllLines($AddonList)) {
            if (-not $name -or $name -ne $name.Trim() -or $name -in @('.', '..', '_shared_libs') -or
                $name.EndsWith('.') -or $name.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0 -or
                -not $seen.Add($name)) { throw "Invalid or duplicate add-on folder: $name" }
            $names.Add($name)
        }
        foreach ($name in $names) {
            $currentAddon = $name
            $addonClock = [Diagnostics.Stopwatch]::StartNew()
            Upgrade-AddonSettings (Join-Path $AddonsPath "$name/config.json") `
                (Join-Path $BackupPath "$name/config.json") (Join-Path $AddonsPath "$name/meta.json") `
                (Join-Path $BackupPath "$name/meta.json") $name $policy
            $completed.Add([pscustomobject]@{ addon = $name; elapsed_ms = $addonClock.ElapsedMilliseconds })
        }
        if ($ReportPath) {
            Write-Settings $ReportPath ([pscustomobject]@{
                schema_version = 1; success = $true; addon_count = $completed.Count
                elapsed_ms = $clock.ElapsedMilliseconds; addons = @($completed.ToArray())
            })
        }
        Write-Output "Upgraded $($completed.Count) add-ons in $($clock.ElapsedMilliseconds) ms (one PowerShell process)."
    }
    exit 0
} catch {
    if ($PSCmdlet.ParameterSetName -eq 'Batch' -and $ReportPath) {
        try {
            Write-Settings $ReportPath ([pscustomobject]@{
                schema_version = 1; success = $false; failed_addon = $currentAddon
                addon_count = $completed.Count; elapsed_ms = $clock.ElapsedMilliseconds
                addons = @($completed.ToArray())
            })
        } catch { Write-Output 'Could not write the settings upgrade report.' }
    }
    Write-Output ('Configuration upgrade failed: ' + $_.Exception.Message)
    exit 1
}
