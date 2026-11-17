# Copies the Azure PostgreSQL database into local media_db_4.
#   1. Backs up the current local media_db_4 to the Desktop (safety copy)
#   2. Dumps the Azure database to the Desktop
#   3. Drops and recreates local media_db_4 and restores the Azure dump into it
# Passwords are typed at the prompts and never saved.

$ErrorActionPreference = "Stop"
$bin     = "C:\Program Files\PostgreSQL\18\bin"
$desktop = [Environment]::GetFolderPath("Desktop")
$stamp   = Get-Date -Format "yyyy-MM-dd_HHmm"
$localDb = "media_db_4"

function Read-Secret($prompt) {
    $s = Read-Host $prompt -AsSecureString
    [Runtime.InteropServices.Marshal]::PtrToStringAuth(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
}

function Run($exe, [string[]]$argList) {
    & "$bin\$exe" @argList
    if ($LASTEXITCODE -ne 0) { throw "$exe failed with exit code $LASTEXITCODE" }
}

# --- Azure details ---
$azHost = Read-Host "Azure server name (e.g. myserver.postgres.database.azure.com)"
$azDb   = Read-Host "Azure database name"
$azUser = Read-Host "Azure admin username"
$azPass = Read-Secret "Azure password"

# --- Local details ---
$locPass = Read-Secret "Local postgres password"

$azDump    = Join-Path $desktop "azure_$($azDb)_$stamp.dump"
$localDump = Join-Path $desktop "local_$($localDb)_before_restore_$stamp.dump"

try {
    # 1. Safety backup of local media_db_4 (skipped if it doesn't exist)
    $env:PGPASSWORD = $locPass
    $exists = & "$bin\psql.exe" -h localhost -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$localDb'"
    if ($LASTEXITCODE -ne 0) { throw "Could not connect to local Postgres - check the local password." }
    if ($exists -eq "1") {
        Write-Host "`n[1/3] Backing up local $localDb to $localDump ..."
        Run "pg_dump.exe" @("-h", "localhost", "-U", "postgres", "-d", $localDb, "-Fc", "-f", $localDump)
    } else {
        Write-Host "`n[1/3] Local $localDb does not exist yet - no backup needed."
    }

    # 2. Dump Azure database to Desktop
    Write-Host "`n[2/3] Dumping Azure database $azDb to $azDump ..."
    $env:PGPASSWORD = $azPass
    Run "pg_dump.exe" @("host=$azHost port=5432 dbname=$azDb user=$azUser sslmode=require",
                        "-Fc", "--no-owner", "--no-acl", "-f", $azDump)

    # 3. Recreate local media_db_4 and restore
    Write-Host "`n[3/3] Restoring into local $localDb ..."
    $env:PGPASSWORD = $locPass
    Run "dropdb.exe"   @("-h", "localhost", "-U", "postgres", "--if-exists", "--force", $localDb)
    Run "createdb.exe" @("-h", "localhost", "-U", "postgres", $localDb)
    & "$bin\pg_restore.exe" -h localhost -U postgres -d $localDb --no-owner --no-acl $azDump
    if ($LASTEXITCODE -ne 0) {
        Write-Host "pg_restore finished with warnings (often Azure-only extensions/roles). Check the messages above." -ForegroundColor Yellow
    }

    $tables = & "$bin\psql.exe" -h localhost -U postgres -d $localDb -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')"
    Write-Host "`nDone. Local $localDb now has $tables tables/views." -ForegroundColor Green
    Write-Host "Azure dump:   $azDump"
    if (Test-Path $localDump) { Write-Host "Old local backup: $localDump" }
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
