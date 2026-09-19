# 建索引：解析 data/ 下文档 -> 去重 -> 分块 -> 编码 -> 保存索引到 storage/。
# 用法：.\scripts\jianku.ps1
# 注意：当前用的是后备嵌入后端（zihouduan）；索引与元数据分开保存在 storage/。

$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Output "错误：未找到 .venv，请先运行 .\scripts\anzhuang.ps1"
    exit 1
}

& $py -c "import sys; sys.path.insert(0, sys.argv[1]); from src.liucheng import jianku; suoyin, houduan, parsed = jianku(); print('建索引完成：%d 个块，后端=%s' % (suoyin.kuai_shu, houduan.mingzi))" $root

