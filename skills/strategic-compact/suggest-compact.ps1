# Strategic Compact Suggester (Windows PowerShell Version)
# Runs on PreToolUse or periodically to suggest manual compaction at logical intervals
#
# Why manual over auto-compact:
# - Auto-compact happens at arbitrary points, often mid-task
# - Strategic compacting preserves context through logical phases
# - Compact after exploration, before execution
# - Compact after completing a milestone, before starting next
#
# Hook config (in ~/.claude/settings.json):
# {
#   "hooks": {
#     "PreToolUse": [{
#       "matcher": "tool == \"Edit\" || tool == \"Write\"",
#       "hooks": [{
#         "type": "command",
#         "command": "powershell -ExecutionPolicy Bypass -File \"$env:USERPROFILE\\.claude\\skills\\strategic-compact\\suggest-compact.ps1\""
#       }]
#     }]
#   }
# }
#
# Criteria for suggesting compact:
# - Session has been running for extended period
# - Large number of tool calls made
# - Transitioning from research/exploration to implementation
# - Plan has been finalized

# Configuration
$Threshold = if ($env:COMPACT_THRESHOLD) { [int]$env:COMPACT_THRESHOLD } else { 50 }
$ReminderInterval = if ($env:COMPACT_REMINDER_INTERVAL) { [int]$env:COMPACT_REMINDER_INTERVAL } else { 25 }

# Track tool call count (fixed filename so it persists across hook invocations)
# Uses date-based reset - counter resets each day for fresh sessions
$Today = Get-Date -Format "yyyyMMdd"
$CounterFile = "$env:TEMP\claude-strategic-compact-$Today.txt"

# Initialize or increment counter
if (Test-Path $CounterFile) {
    $count = [int](Get-Content $CounterFile -Raw)
    $count++
} else {
    $count = 1
}
Set-Content -Path $CounterFile -Value $count -NoNewline

# Suggest compact after threshold tool calls
if ($count -eq $Threshold) {
    Write-Host "[StrategicCompact] $Threshold tool calls reached - consider /compact if transitioning phases" -ForegroundColor Yellow
}

# Suggest at regular intervals after threshold
if ($count -gt $Threshold -and ($count % $ReminderInterval) -eq 0) {
    Write-Host "[StrategicCompact] $count tool calls - good checkpoint for /compact if context is stale" -ForegroundColor Yellow
}
