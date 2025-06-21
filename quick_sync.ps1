# Quick Sync for geom_from_text_optimized
# Always copies all files for reliable development

$qgisPluginsPath = "C:\Users\paulo\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins"
$sourcePath = Get-Location
$targetPath = Join-Path $qgisPluginsPath "geom_from_text_optimized"

Write-Host "QUICK SYNC - geom_from_text_optimized" -ForegroundColor Cyan
Write-Host ("=" * 50)

# Check if QGIS is running
$qgisProcesses = Get-Process -Name "qgis-bin" -ErrorAction SilentlyContinue
if ($qgisProcesses) {
    Write-Host "QGIS is running - changes will be applied after reload" -ForegroundColor Yellow
}

# Create target directory if it doesn't exist
if (-not (Test-Path $targetPath)) {
    Write-Host "Creating target directory..." -ForegroundColor Blue
    New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
}

# Get list of files to sync (exclude certain files)
$excludePatterns = @("*.log", "*.tmp", "__pycache__", ".git")

# Get files in root directory
$rootFiles = Get-ChildItem -Path $sourcePath -File | Where-Object {
    $shouldInclude = $true
    foreach ($pattern in $excludePatterns) {
        if ($_.FullName -like "*$pattern*") {
            $shouldInclude = $false
            break
        }
    }
    return $shouldInclude
}

# Get files in subdirectories
$subFiles = Get-ChildItem -Path $sourcePath -Recurse -File | Where-Object {
    $shouldInclude = $true
    foreach ($pattern in $excludePatterns) {
        if ($_.FullName -like "*$pattern*") {
            $shouldInclude = $false
            break
        }
    }
    return $shouldInclude
}

$sourceFiles = $rootFiles + $subFiles

$copiedCount = 0

foreach ($file in $sourceFiles) {
    # Calculate relative path correctly
    if ($file.Directory.FullName -eq $sourcePath) {
        # Root file - just use filename
        $relativePath = $file.Name
        $targetFile = Join-Path $targetPath $file.Name
    } else {
        # Subdirectory file - calculate relative path from source
        $relativePath = $file.FullName.Substring($sourcePath.Length + 1)
        $targetFile = Join-Path $targetPath $relativePath
    }
    
    $targetDir = Split-Path $targetFile -Parent
    
    # Create target directory if needed
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    try {
        Copy-Item $file.FullName $targetFile -Force
        Write-Host ("COPIED: {0}" -f $relativePath) -ForegroundColor Green
        $copiedCount++
    } catch {
        Write-Host ("ERROR: {0} - {1}" -f $relativePath, $_) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "SYNC SUMMARY:" -ForegroundColor Cyan
Write-Host ("   Files copied: {0}" -f $copiedCount) -ForegroundColor Green
Write-Host ("   Total files: {0}" -f $copiedCount) -ForegroundColor White

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Go to QGIS -> Plugins -> Manage and Install Plugins" -ForegroundColor White
Write-Host "   2. Find 'geom_from_text_optimized'" -ForegroundColor White
Write-Host "   3. Click 'Reload Plugin'" -ForegroundColor White
Write-Host "   4. Test your changes!" -ForegroundColor White 