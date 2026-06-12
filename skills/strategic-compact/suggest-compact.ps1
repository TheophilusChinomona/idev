# Strategic Compact Suggester (idev plugin - Windows PowerShell version)
#
# PostToolUse hook (matcher: "Edit|Write"). Reads the hook JSON from stdin,
# keeps a per-session counter in $env:TEMP, and every N Edit/Write calls
# (default 50, override with IDEV_COMPACT_THRESHOLD) emits hookSpecificOutput
# JSON on stdout so Claude sees a reminder to suggest /compact at a logical
# boundary.
#
# This script lives in the installed idev plugin at:
#   <idev-plugin-root>\skills\strategic-compact\suggest-compact.ps1
# See SKILL.md in this folder for the settings.json registration snippet
# (use the absolute plugin path - ${CLAUDE_PLUGIN_ROOT} does not expand in
# user settings).
#
# OFF by default: exits immediately unless the per-project opt-in flag exists.
# Toggle with /idev:hooks enable|disable compact (creates/removes the flag).
# Always exits 0; emits nothing below the threshold.

$ErrorActionPreference = "SilentlyContinue"

# Opt-in guard (mirrors suggest-compact.sh)
$projectDir = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { "." }
$flag = Join-Path $projectDir ".claude/idev/compact-suggestions-enabled"
if (-not (Test-Path $flag)) { exit 0 }

# Read the hook JSON from stdin and extract session_id
$raw = [Console]::In.ReadToEnd()
$sessionId = "default"
try {
    $json = $raw | ConvertFrom-Json
    if ($json.session_id) {
        $clean = [string]$json.session_id -replace '[^A-Za-z0-9._-]', ''
        if ($clean) { $sessionId = $clean }
    }
} catch {}

$threshold = 50
if ($env:IDEV_COMPACT_THRESHOLD -and $env:IDEV_COMPACT_THRESHOLD -match '^\d+$') {
    $parsed = [int]$env:IDEV_COMPACT_THRESHOLD
    if ($parsed -ge 1) { $threshold = $parsed }
}

# Per-session counter (not shared across sessions/projects)
$counterFile = Join-Path $env:TEMP "claude-idev-compact-$sessionId"

$count = 0
if (Test-Path $counterFile) {
    $contents = (Get-Content $counterFile -Raw).Trim()
    # Reset if contents are not numeric (corrupt/tampered file)
    if ($contents -match '^\d+$') { $count = [int]$contents }
}
$count++
Set-Content -Path $counterFile -Value $count -NoNewline

if (($count % $threshold) -eq 0) {
    $msg = "[strategic-compact] $count Edit/Write calls this session. If you are at a logical boundary (plan finalized, milestone complete, bug fixed), consider suggesting /compact to the user before continuing. Do not interrupt mid-implementation."
    $payload = @{
        hookSpecificOutput = @{
            hookEventName     = "PostToolUse"
            additionalContext = $msg
        }
    } | ConvertTo-Json -Compress
    Write-Output $payload
}

exit 0
