# 跑评测：读 pingce/wenti.json，检索 20 题，算 Recall@k 与误命中率，写 jieguo.json。
# 用法：.\scripts\pingce.ps1
# 必须先建好索引（.\scripts\jianku.ps1）。

$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Output "错误：未找到 .venv，请先运行 .\scripts\anzhuang.ps1"
    exit 1
}

& $py -c "import sys; sys.path.insert(0, sys.argv[1]); from src.pingce import zhuc_jiank_pingce; jieguo, rs = zhuc_jiank_pingce(); print('Recall@1=%.4f Recall@3=%.4f Recall@5=%.4f 误命中率=%.4f 平均延迟=%.6fs' % (jieguo['recall@1'], jieguo['recall@3'], jieguo['recall@5'], jieguo['wu_hit_rate'], jieguo['avg_latency_s']))" $root

