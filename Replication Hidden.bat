@echo off

cd /d C:\ReplicationBot

if not exist logs mkdir logs

set LOGFILE=logs\run.log

python replication.py > "%LOGFILE%" 2>&1

if %ERRORLEVEL% EQU 0 (
    powershell -Command "[System.Windows.MessageBox]::Show('Replication Export berhasil selesai.','Replication Export')"
) else (
    powershell -Command "[System.Windows.MessageBox]::Show('Replication Export gagal. Cek logs\run.log','Replication Export')"
)