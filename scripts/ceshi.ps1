# 跑测试：执行 pytest -q。
# 用法：.\scripts\ceshi.ps1
# 说明：测试会重建索引到临时目录，不依赖已保存的 storage/。

$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Output "错误：未找到 .venv，请先运行 .\scripts\anzhuang.ps1"
    exit 1
}

Set-Location $root
& $py -m pytest -q

