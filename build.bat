@echo off
set TCL_LIBRARY=C:\Users\amir\AppData\Local\Programs\Python\Python311\tcl\tcl8.6
set TK_LIBRARY=C:\Users\amir\AppData\Local\Programs\Python\Python311\tcl\tk8.6

echo ========================================
echo   Building JARVIS .exe (Safe Mode)
echo ========================================

pip install -r requirements.txt

pyinstaller --onefile --noconsole --name "jarvis" ^
  --clean ^
  --collect-all vosk ^
  --exclude-module torch ^
  --exclude-module tensorflow ^
  main.py

echo.
echo ✅ Done! Your .exe is in: dist\jarvis.exe
pause
