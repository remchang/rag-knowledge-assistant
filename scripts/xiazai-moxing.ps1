# 下载真实模型权重（默认不执行，仅给装好环境后的同学用）。
# 用法：.\scripts\xiazai-moxing.ps1            # 下载全部
#       .\scripts\xiazai-moxing.ps1 bge       # 只下 BGE
# 固定 revision 与 local_dir，保证可离线复现。repo 见 model_list.md。

$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
$pip = Join-Path $root ".venv\Scripts\pip.exe"
$mirror = "https://mirrors.aliyun.com/pypi/simple/"
$turst = "mirrors.aliyun.com"

if (-not (Test-Path $py)) {
    Write-Output "错误：未找到 .venv，请先运行 .\scripts\anzhuang.ps1"
    exit 1
}

Write-Output "安装 huggingface_hub ..."
& $pip install huggingface_hub -i $mirror --trusted-host $turst

$ming = $args[0]
& $py -c "import sys; sys.path.insert(0, sys.argv[1]); from src.xiazai_moxing import zhuxia; zhuxia(ming=sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None)" $root $ming

