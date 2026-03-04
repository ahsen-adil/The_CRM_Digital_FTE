$urls = @(
    'http://localhost:3000/',
    'http://localhost:3000/dashboard',
    'http://localhost:3000/tickets',
    'http://localhost:3000/customers',
    'http://localhost:3000/reports',
    'http://localhost:3000/webform',
    'http://localhost:3000/settings'
)

foreach($url in $urls) {
    try {
        $r = Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing -TimeoutSec 10
        Write-Host "$url : $($r.StatusCode) - OK"
    } catch {
        Write-Host "$url : FAILED - $($_.Exception.Message)"
    }
}
