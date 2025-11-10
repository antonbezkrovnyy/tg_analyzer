# Automatic analysis of all November ru_python data
# Usage: .\analyze_november_auto.ps1

$ErrorActionPreference = "Stop"

# Configuration
$dataPath = "C:\Users\Мой компьютер\Desktop\python-tg\data\ru_python"
$outputPath = "C:\Users\Мой компьютер\Desktop\tg_analyzer\output\ru_python"
$venvPython = "C:\Users\Мой компьютер\Desktop\tg_analyzer\.venv\Scripts\python.exe"
$scriptPath = "C:\Users\Мой компьютер\Desktop\tg_analyzer\scripts\analyze_full_day.py"
$chat = "ru_python"
$batchSize = 100

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  November ru_python Auto-Analyzer" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get all November 2025 data files
$dataFiles = Get-ChildItem -Path $dataPath -Filter "2025-11-*.json" | Sort-Object Name

if ($dataFiles.Count -eq 0) {
    Write-Host "No data files found for November 2025 in $dataPath" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($dataFiles.Count) data files for November:`n" -ForegroundColor Green

# Check which files need analysis
$toAnalyze = @()
foreach ($file in $dataFiles) {
    $date = $file.BaseName  # e.g., "2025-11-05"
    $outputFile = Join-Path $outputPath "$date.json"
    
    $dataSize = [math]::Round($file.Length / 1KB, 1)
    
    if (Test-Path $outputFile) {
        $outputFileInfo = Get-Item $outputFile
        $outputSize = [math]::Round($outputFileInfo.Length / 1KB, 1)
        
        # Check if data file is newer than output (needs re-analysis)
        if ($file.LastWriteTime -gt $outputFileInfo.LastWriteTime) {
            Write-Host "  [$date] Data: ${dataSize}KB | Output: ${outputSize}KB | Status: " -NoNewline -ForegroundColor White
            Write-Host "NEEDS UPDATE" -ForegroundColor Yellow
            $toAnalyze += $date
        } else {
            Write-Host "  [$date] Data: ${dataSize}KB | Output: ${outputSize}KB | Status: " -NoNewline -ForegroundColor White
            Write-Host "UP-TO-DATE" -ForegroundColor Green
        }
    } else {
        Write-Host "  [$date] Data: ${dataSize}KB | Output: N/A | Status: " -NoNewline -ForegroundColor White
        Write-Host "NEW" -ForegroundColor Cyan
        $toAnalyze += $date
    }
}

if ($toAnalyze.Count -eq 0) {
    Write-Host "`nAll files are up-to-date! Nothing to analyze." -ForegroundColor Green
    exit 0
}

Write-Host "`n$($toAnalyze.Count) file(s) need analysis.`n" -ForegroundColor Yellow
Write-Host "Starting analysis with batch size: $batchSize" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$successCount = 0
$failCount = 0
$startTime = Get-Date

foreach ($date in $toAnalyze) {
    Write-Host "Processing $date..." -ForegroundColor White
    
    try {
        # Run analysis
        $result = & $venvPython $scriptPath $chat $date --batch-size $batchSize 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Successfully analyzed $date" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ✗ Failed to analyze $date (Exit code: $LASTEXITCODE)" -ForegroundColor Red
            Write-Host "    Error: $result" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ✗ Exception analyzing $date" -ForegroundColor Red
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Analysis Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Success: $successCount | Failed: $failCount | Duration: $($duration.ToString('mm\:ss'))" -ForegroundColor White

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "Analyzed files are in: $outputPath" -ForegroundColor Green
}

exit $failCount
