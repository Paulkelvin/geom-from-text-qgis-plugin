# Sync to ZIP for geom_from_text_optimized
# Updates the zip file with latest changes from development folder

$zipPath = "C:\Users\paulo\Downloads\geom_from_text_optimized.zip"
$sourcePath = (Get-Location).ProviderPath

Write-Host "SYNC TO ZIP - geom_from_text_optimized" -ForegroundColor Cyan
Write-Host ("=" * 50)

# Check if source directory exists
if (-not (Test-Path $sourcePath)) {
    Write-Host "ERROR: Source directory not found!" -ForegroundColor Red
    exit 1
}

# Remove existing zip if it exists
if (Test-Path $zipPath) {
    Write-Host "Removing existing zip file..." -ForegroundColor Blue
    Remove-Item $zipPath -Force
}

# Get list of files to include (exclude certain files)
$excludePatterns = @("*.log", "*.tmp", "__pycache__", ".git", "*.zip")
$sourceFiles = Get-ChildItem -Path $sourcePath -Recurse -File | Where-Object {
    $shouldInclude = $true
    foreach ($pattern in $excludePatterns) {
        if ($_.FullName -like "*$pattern*") {
            $shouldInclude = $false
            break
        }
    }
    return $shouldInclude
}

Write-Host "Creating new zip file with latest changes..." -ForegroundColor Blue

# Create temporary directory for zip contents with proper structure
$tempDir = Join-Path $env:TEMP "geom_from_text_optimized_temp"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Create the plugin folder inside temp directory
$pluginFolder = Join-Path $tempDir "geom_from_text_optimized"
New-Item -ItemType Directory -Path $pluginFolder -Force | Out-Null

# Copy files to plugin folder, preserving only the path relative to the plugin folder
$copiedCount = 0
foreach ($file in $sourceFiles) {
    $relativePath = $file.FullName.Substring($sourcePath.Length + 1).TrimStart('\','/')
    $targetFile = Join-Path $pluginFolder $relativePath
    $targetDir = Split-Path $targetFile -Parent
    
    # Create target directory if needed
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    # Copy file
    Copy-Item $file.FullName $targetFile -Force
    Write-Host ("COPIED: {0}" -f $relativePath) -ForegroundColor Green
    $copiedCount++
}

# Create zip file from the temp directory (which contains the plugin folder)
Write-Host "Compressing files..." -ForegroundColor Blue
try {
    Compress-Archive -Path "$tempDir\geom_from_text_optimized" -DestinationPath $zipPath -Force
    Write-Host "ZIP file created successfully!" -ForegroundColor Green
} catch {
    Write-Host ("ERROR creating zip: {0}" -f $_) -ForegroundColor Red
    exit 1
}

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

Write-Host ""
Write-Host "ZIP SYNC SUMMARY:" -ForegroundColor Cyan
Write-Host ("   Files included: {0}" -f $copiedCount) -ForegroundColor Green
Write-Host ("   Zip location: {0}" -f $zipPath) -ForegroundColor White
Write-Host ("   Zip size: {0:N0} KB" -f ((Get-Item $zipPath).Length / 1KB)) -ForegroundColor White
Write-Host "   Zip structure: geom_from_text_optimized/ (plugin folder)" -ForegroundColor White

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Go to QGIS -> Plugins -> Manage and Install Plugins" -ForegroundColor White
Write-Host "   2. Click 'Install from ZIP'" -ForegroundColor White
Write-Host "   3. Select: C:\Users\paulo\Downloads\geom_from_text_optimized.zip" -ForegroundColor White
Write-Host "   4. Install the plugin" -ForegroundColor White
Write-Host "   5. Run this script again after any changes to update the zip" -ForegroundColor White

Write-Host ""
Write-Host "TIP: Run this script after every code change to keep the zip updated!" -ForegroundColor Cyan 