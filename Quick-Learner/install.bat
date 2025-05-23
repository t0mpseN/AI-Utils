@echo
title Install Dependencies
echo Installing dependencies...
cmd /c "winget install 7zip"
cmd /c "pip install -r requirements.txt"
pause