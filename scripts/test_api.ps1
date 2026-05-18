$key = $env:OPENCODE_GO_API_KEY
Write-Output "Key available: $($key.Length -gt 0)"
Write-Output "Key length: $($key.Length)"

$body = @{
    model = 'deepseek-v4-flash'
    messages = @(
        @{role='system'; content='Say hello'}
        @{role='user'; content='Say hello world'}
    )
    max_tokens = 20
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri 'https://opencode.ai/zen/go/v1/chat/completions' -Method Post -Body $body -ContentType 'application/json' -Headers @{Authorization = "Bearer $key"} -ErrorAction Stop
    Write-Output "API response: $($response.choices[0].message.content)"
} catch {
    Write-Output "API error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $respBody = $reader.ReadToEnd()
        Write-Output "Response body: $respBody"
    }
}
