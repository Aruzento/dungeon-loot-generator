@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Installing build dependency...
python -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 exit /b 1

echo [2/3] Running tests...
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1

echo [3/3] Building standalone GUI executable...
python -m PyInstaller --noconfirm --clean dungeon_loot.spec
if errorlevel 1 exit /b 1

echo Built: dist\DungeonLoot.exe
endlocal
