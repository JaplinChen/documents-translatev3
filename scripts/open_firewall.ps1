$RuleName = "Allow-Documents-Translate-Docker"
$Ports = @(5194, 5002, 11434)

Write-Host "--- Windows Firewall Configurator ---" -ForegroundColor Cyan

$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run this script as ADMINISTRATOR!"
    exit
}

if (Get-NetFirewallRule -Name $RuleName -ErrorAction SilentlyContinue) {
    Remove-NetFirewallRule -Name $RuleName
    Write-Host "Removed existing rule."
}

New-NetFirewallRule -DisplayName "Documents Translate (Docker Share)" `
    -Name $RuleName `
    -Direction Inbound `
    -LocalPort $Ports `
    -Protocol TCP `
    -Action Allow `
    -Description "Allows LAN access to Documents Translate frontend and backend."

$ip = ([System.Net.Dns]::GetHostEntry([System.Net.Dns]::GetHostName()).AddressList | Where-Object { $_.AddressFamily -eq 'InterNetwork' } | Select-Object -First 1).IPAddressToString
Write-Host "SUCCESS: Ports $($Ports -join ', ') are now open." -ForegroundColor Green
Write-Host "Share URL: http://$($ip):5194" -ForegroundColor Yellow
