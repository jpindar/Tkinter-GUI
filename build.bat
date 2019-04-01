rmdir dist /s
rmdir build /s
pyinstaller onefile.spec
copy dist\*.* .
