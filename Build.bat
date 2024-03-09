@echo off
echo Deleting exsiting dist folders...
rmdir /s /q dist

echo Running PyInstaller for main.py...
pyinstaller --onefile --add-data "templates;templates" --icon icon.ico main.py

echo Running PyInstaller for background.py...
pyinstaller --onefile background.py

echo Deleting build folders...
rmdir /s /q build

echo Deleting spec files...
del main.spec
del background.spec

echo Process completed successfully.
