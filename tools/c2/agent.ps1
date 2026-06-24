param(
    [Parameter(Mandatory=$true)][string]$StorageAccount,
    [Parameter(Mandatory=$true)][string]$Container,
    [Parameter(Mandatory=$true)][string]$SasToken
)

$base = "https://$StorageAccount.blob.core.windows.net/$Container"

function Get-Blob($name) {
    try {
        $r = Invoke-WebRequest -Uri "$base/${name}?${SasToken}" -UseBasicParsing
        return $r.Content
    } catch {
        if ($_.Exception.Response.StatusCode -eq 404) { return $null }
        throw
    }
}

function Set-Blob($name, $body) {
    $h = @{ "x-ms-blob-type" = "BlockBlob"; "Content-Type" = "text/plain" }
    Invoke-WebRequest -Uri "$base/${name}?${SasToken}" -Method PUT -Headers $h `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -UseBasicParsing | Out-Null
}

function Remove-Blob($name) {
    Invoke-WebRequest -Uri "$base/${name}?${SasToken}" -Method DELETE -UseBasicParsing | Out-Null
}

Write-Host "[agent] polling $base ..."

while ($true) {
    try {
        $cmd = Get-Blob "cmd.txt"
        if ($cmd) {
            Remove-Blob "cmd.txt"
            if ($cmd.Trim() -eq "EXIT") {
                Set-Blob "output.txt" "[agent exited]"
                Write-Host "[agent] EXIT received"
                break
            }
            Write-Host "[agent] exec: $cmd"
            try { $out = cmd.exe /c $cmd 2>&1 | Out-String }
            catch { $out = "ERROR: $_" }
            Set-Blob "output.txt" $out
        }
    } catch {
        Write-Host "[agent] error: $_"
    }
    Start-Sleep -Seconds 3
}
