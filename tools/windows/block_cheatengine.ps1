param(
    [Parameter(Mandatory=$true)][ValidateSet('add','remove')][string]$Action,
    [Parameter(Mandatory=$true)][string]$ExePath
)

$ruleName = "Block CheatEngine"
if ($Action -eq 'add') {
    Write-Output "Adding firewall rule to block: $ExePath"
    try {
        New-NetFirewallRule -DisplayName $ruleName -Direction Outbound -Action Block -Program $ExePath -Enabled True -ErrorAction Stop
        Write-Output "Rule added."
    } catch {
        Write-Error "Failed to add rule: $_"
        exit 1
    }
} else {
    Write-Output "Removing firewall rule named: $ruleName"
    try {
        Get-NetFirewallRule -DisplayName $ruleName | Remove-NetFirewallRule
        Write-Output "Rule removed."
    } catch {
        Write-Error "Failed to remove rule or rule not present: $_"
        exit 1
    }
}
