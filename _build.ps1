$node="C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Microsoft\VisualStudio\NodeJs\node.exe"
$env:NODE_OPTIONS="--max-old-space-size=4096"
Set-Location "F:\tiroltourismus"
& $node "node_modules\astro\astro.js" "build"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
