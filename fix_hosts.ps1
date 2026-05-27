$hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
$content = Get-Content $hosts -Raw
$content = $content -replace '#\t127\.0\.0\.1\s+localhost', "`t127.0.0.1`tlocalhost"
$content = $content -replace '#\t::1\s+localhost', "`t::1`tlocalhost"
Set-Content $hosts -Value $content -Force
Write-Output 'Done'
