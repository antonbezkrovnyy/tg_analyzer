# Analyze all ru_python data in batches
# This script processes all available data files from ../python-tg/data/ru_python

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Batch Analysis: ru_python" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if data directory exists
$dataPath = "..\python-tg\data\ru_python"
if (-Not (Test-Path $dataPath)) {
    Write-Host "Error: Data directory not found: $dataPath" -ForegroundColor Red
    exit 1
}

# Get all JSON files
$files = Get-ChildItem -Path $dataPath -Filter "*.json" | Sort-Object Name

if ($files.Count -eq 0) {
    Write-Host "No JSON files found in $dataPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nFound $($files.Count) data files:" -ForegroundColor Green
foreach ($file in $files) {
    Write-Host "  - $($file.Name)" -ForegroundColor Gray
}

# Configuration
$chat = "ru_python"
$batchSize = 100  # Process 100 messages at a time

Write-Host "`nBatch size: $batchSize messages" -ForegroundColor Cyan
Write-Host "Starting analysis...`n" -ForegroundColor Cyan

$totalProcessed = 0
$totalSuccess = 0
$totalFailed = 0

foreach ($file in $files) {
    # Extract date from filename (e.g., "2025-11-05.json" -> "2025-11-05")
    $date = $file.BaseName
    
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Processing: $date" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    
    $totalProcessed++
    
    try {
        # Run analysis script
        python analyze_full_day.py $chat $date --batch-size $batchSize
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✓ Successfully analyzed: $date" -ForegroundColor Green
            $totalSuccess++
        } else {
            Write-Host "`n✗ Failed to analyze: $date (exit code: $LASTEXITCODE)" -ForegroundColor Red
            $totalFailed++
        }
    } catch {
        Write-Host "`n✗ Error analyzing $date : $_" -ForegroundColor Red
        $totalFailed++
    }
    
    # Small delay between files
    Start-Sleep -Seconds 2
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "BATCH ANALYSIS COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total files: $totalProcessed" -ForegroundColor White
Write-Host "Successful: $totalSuccess" -ForegroundColor Green
Write-Host "Failed: $totalFailed" -ForegroundColor Red
Write-Host "`nOutput location: output/ru_python/" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
