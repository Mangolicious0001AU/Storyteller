
@echo off
cd /d "%~dp0"
echo === PUSHING CHANGES ===
git add .
set /p msg=Commit message: 
if "%msg%"=="" set msg=Update on %DATE% %TIME%
git commit -m "%msg%"
git push origin main
pause
