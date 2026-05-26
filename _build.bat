@echo off
set NODE_OPTIONS=--max-old-space-size=4096
"C:\Program Files\nodejs\node.exe" "C:\Users\logga\AppData\Roaming\npm\node_modules\npm\bin\npx-cli.js" astro build
exit /b %ERRORLEVEL%
