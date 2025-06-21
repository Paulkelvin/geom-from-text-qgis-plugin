# Setup Development Mode for geom_from_text_optimized
# This creates a symbolic link so changes are automatically reflected in QGIS

param(
    [switch]$Remove,
    [switch]$Force
)

$qgisPluginsPath = "C:\Users\paulo\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins"
$devPath = Get-Location
$pluginName = "geom_from_text_optimized"
$targetPath = Join-Path $qgisPluginsPath $pluginName

Write-Host "GEOM FROM TEXT OPTIMIZED - DEVELOPMENT MODE SETUP" -ForegroundColor Cyan
Write-Host ("=" * 60)

if ($Remove) {
    Write-Host "Removing development mode..." -ForegroundColor Yellow
    
    # Check if symbolic link exists
    if (Test-Path $targetPath -PathType Container) {
        try {
            # Remove the symbolic link
            Remove-Item $targetPath -Force -Recurse
            Write-Host "Symbolic link removed successfully" -ForegroundColor Green
        } catch {
            Write-Host ("Error removing symbolic link: {0}" -f $_) -ForegroundColor Red
            Write-Host "   Make sure QGIS is closed and try again" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No symbolic link found to remove" -ForegroundColor Blue
    }
    return
}

# Check if QGIS is running
$qgisProcesses = Get-Process -Name "qgis-bin" -ErrorAction SilentlyContinue
if ($qgisProcesses) {
    Write-Host "WARNING: QGIS is currently running!" -ForegroundColor Yellow
    Write-Host "   Please close QGIS before setting up development mode" -ForegroundColor Yellow
    Write-Host "   Or use -Force to continue anyway" -ForegroundColor Yellow
    
    if (-not $Force) {
        return
    }
}

# Check if target already exists
if (Test-Path $targetPath) {
    Write-Host ("Target path already exists: {0}" -f $targetPath) -ForegroundColor Yellow
    
    if ($Force) {
        Write-Host "Removing existing target..." -ForegroundColor Yellow
        Remove-Item $targetPath -Force -Recurse
    } else {
        Write-Host "   Use -Force to overwrite, or -Remove to clean up" -ForegroundColor Yellow
        return
    }
}

# Create symbolic link
Write-Host "Creating symbolic link..." -ForegroundColor Blue
Write-Host ("   From: {0}" -f $devPath) -ForegroundColor Gray
Write-Host ("   To: {0}" -f $targetPath) -ForegroundColor Gray

try {
    # Create symbolic link (requires admin privileges)
    New-Item -ItemType SymbolicLink -Path $targetPath -Target $devPath -Force
    Write-Host "Symbolic link created successfully!" -ForegroundColor Green
} catch {
    Write-Host ("Failed to create symbolic link: {0}" -f $_) -ForegroundColor Red
    Write-Host "   This might require administrator privileges" -ForegroundColor Yellow
    Write-Host "   Alternative: Use the sync script instead" -ForegroundColor Yellow
    return
}

Write-Host ""
Write-Host "DEVELOPMENT MODE SETUP COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "Changes to your development folder will automatically appear in QGIS" -ForegroundColor Green
Write-Host "No need to reinstall the plugin after changes" -ForegroundColor Green
Write-Host "Just reload the plugin in QGIS: Plugins -> Manage -> Reload Plugin" -ForegroundColor Green
Write-Host ""
Write-Host "To remove development mode, run:" -ForegroundColor Cyan
Write-Host "   .\setup_dev_mode.ps1 -Remove" -ForegroundColor Gray
Write-Host ""
Write-Host "You can now start QGIS and test your plugin!" -ForegroundColor Green 