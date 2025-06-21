# Sync Plugin Script - Automatically syncs changes to QGIS plugins folder
# Run this script after making changes to sync them to QGIS

$sourcePath = "C:\Users\paulo\Downloads\geom_from_text_optimized"
$targetPath = "C:\Users\paulo\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\geom_from_text_optimized"

Write-Host "Syncing plugin changes..." -ForegroundColor Green
Write-Host "From: $sourcePath" -ForegroundColor Yellow
Write-Host "To: $targetPath" -ForegroundColor Yellow

# Remove target directory if it exists
if (Test-Path $targetPath) {
    Remove-Item -Path $targetPath -Recurse -Force
    Write-Host "Removed existing plugin directory" -ForegroundColor Cyan
}

# Copy current directory to plugins folder
Copy-Item -Path $sourcePath -Destination $targetPath -Recurse -Force

Write-Host "Plugin synced successfully!" -ForegroundColor Green
Write-Host "Now reload the plugin in QGIS:" -ForegroundColor Cyan
Write-Host "1. Go to Plugins -> Manage and Install Plugins" -ForegroundColor White
Write-Host "2. Find 'geom_from_text_optimized'" -ForegroundColor White
Write-Host "3. Click 'Reload Plugin'" -ForegroundColor White
Write-Host "4. Test your changes!" -ForegroundColor White 