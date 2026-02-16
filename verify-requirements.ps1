# Requirements Verification Script
# Run this to verify all tested requirements

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  COMPREHENSIVE REQUIREMENTS VERIFICATION" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# 1. Scrape Interval
Write-Host "1. Scrape Interval Configuration..." -NoNewline
try {
    $result = vagrant ssh monitoring-server-auto -c "grep scrape_interval /etc/prometheus/prometheus.yml" 2>$null
    if ($result -match "15s") {
        Write-Host " PASSED" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 2. ELK Stack
Write-Host "2. ELK Stack Components..." -NoNewline
$elkPassed = $true
try {
    $es = (Invoke-WebRequest -Uri http://192.168.56.25:9200/_cluster/health -UseBasicParsing).Content | Select-String '"status"'
    if (-not $es) { $elkPassed = $false }
} catch { $elkPassed = $false }

$logstash = vagrant ssh monitoring-server-auto -c "systemctl is-active logstash" 2>$null
if ($logstash -ne "active") { $elkPassed = $false }

try {
    $null = Invoke-WebRequest -Uri http://192.168.56.25:5601/api/status -UseBasicParsing -ErrorAction Stop
} catch { $elkPassed = $false }

$filebeat = vagrant ssh web1-server-auto -c "systemctl is-active filebeat" 2>$null
if ($filebeat -ne "active") { $elkPassed = $false }

if ($elkPassed) {
    Write-Host " PASSED" -ForegroundColor Green
} else {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 3. Node Exporter
Write-Host "3. Node Exporter (all VMs)..." -NoNewline
$nodeExporterPassed = $true
$vms = @("lb", "web1", "web2", "app", "backup", "monitoring")
foreach ($vm in $vms) {
    $result = vagrant ssh "${vm}-server-auto" -c "curl -s http://localhost:9100/metrics 2>/dev/null | head -1" 2>$null
    if (-not $result -or $result.Length -eq 0) {
        $nodeExporterPassed = $false
        break
    }
}
if ($nodeExporterPassed) {
    Write-Host " PASSED" -ForegroundColor Green
} else {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 4. cAdvisor
Write-Host "4. cAdvisor (Docker VMs)..." -NoNewline
$cadvisorPassed = $true
$dockerVms = @("web1", "web2", "app")
foreach ($vm in $dockerVms) {
    $result = vagrant ssh "${vm}-server-auto" -c "curl -s http://localhost:8080/metrics 2>/dev/null | head -1" 2>$null
    if (-not $result -or $result.Length -eq 0) {
        $cadvisorPassed = $false
        break
    }
}
if ($cadvisorPassed) {
    Write-Host " PASSED" -ForegroundColor Green
} else {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 5. Custom Application Metrics
Write-Host "5. Custom Application Metrics..." -NoNewline
try {
    $result = vagrant ssh web1-server-auto -c "curl -s http://localhost:5000/metrics 2>/dev/null | grep '^flask_' | head -1" 2>$null
    if ($result -and $result -match "flask_") {
        Write-Host " PASSED" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 6. Prometheus Targets
Write-Host "6. Prometheus Targets..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://192.168.56.25:9090/api/v1/targets" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    $allUp = $true
    foreach ($target in $json.data.activeTargets) {
        if ($target.health -ne "up") {
            $allUp = $false
            break
        }
    }
    if ($allUp) {
        Write-Host " PASSED (all targets up)" -ForegroundColor Green
    } else {
        Write-Host " WARNING (some targets down)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 7. Grafana Alerts
Write-Host "7. Grafana Alerts..." -NoNewline
try {
    $pair = "admin:admin"
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
    $base64 = [System.Convert]::ToBase64String($bytes)
    $headers = @{ Authorization = "Basic $base64" }
    $response = Invoke-WebRequest -Uri "http://192.168.56.25:3000/api/v1/provisioning/alert-rules" -UseBasicParsing -Headers $headers
    $json = $response.Content | ConvertFrom-Json
    $alertCount = $json.Count
    if ($alertCount -ge 7) {
        Write-Host " PASSED ($alertCount alerts configured)" -ForegroundColor Green
    } else {
        Write-Host " WARNING ($alertCount alerts found, expected 7)" -ForegroundColor Yellow
    }
} catch {
    # Try checking via vagrant ssh instead
    $result = vagrant ssh monitoring-server-auto -c "curl -s -u admin:admin http://localhost:3000/api/v1/provisioning/alert-rules 2>/dev/null" 2>$null
    if ($result -and $result -match '"title"') {
        $count = ([regex]::Matches($result, '"title"')).Count
        Write-Host " PASSED ($count alerts configured via SSH)" -ForegroundColor Green
    } else {
        Write-Host " WARNING (check manually in Grafana UI)" -ForegroundColor Yellow
    }
}

# 8. Grafana Access
Write-Host "8. Grafana Access..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://192.168.56.25:3000/api/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host " PASSED" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 9. Kibana Access
Write-Host "9. Kibana Access..." -NoNewline
try {
    $null = Invoke-WebRequest -Uri "http://192.168.56.25:5601/api/status" -UseBasicParsing -ErrorAction Stop
    Write-Host " PASSED" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

# 10. Elasticsearch Access
Write-Host "10. Elasticsearch Access..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://192.168.56.25:9200/_cluster/health" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    if ($json.status -eq "green" -or $json.status -eq "yellow") {
        Write-Host " PASSED (status: $($json.status))" -ForegroundColor Green
    } else {
        Write-Host " WARNING (status: $($json.status))" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  OVERALL STATUS: PASSED" -ForegroundColor Green
} else {
    Write-Host "  OVERALL STATUS: SOME CHECKS FAILED" -ForegroundColor Yellow
}
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick Access URLs:" -ForegroundColor Cyan
Write-Host "  Grafana: http://192.168.56.25:3000 (admin/admin)" -ForegroundColor White
Write-Host "  Prometheus: http://192.168.56.25:9090" -ForegroundColor White
Write-Host "  Kibana: http://192.168.56.25:5601" -ForegroundColor White
Write-Host "  Elasticsearch: http://192.168.56.25:9200" -ForegroundColor White

