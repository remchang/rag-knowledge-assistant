# 安装依赖：创建虚拟环境并安装 numpy / pypdf / pytest（用阿里云镜像，适配国内慢网）。
# 用法：在 PowerShell 里执行  .\scripts\anzhuang.ps1
# 说明：本机默认不装 torch / transformers / sentence-transformers / faiss-cpu / streamlit。
#       若要跑 Streamlit 界面，请自己额外执行：.\.venv\Scripts\pip install streamlit

$py_exe = Join-Path $env:USERPROFILE ".workbuddy\binaries\python\versions\3.13.12\python.exe"
$root = Split-Path -Parent $PSScriptRoot
$mirror = "https://mirrors.aliyun.com/pypi/simple/"
$turst = "mirrors.aliyun.com"

if (-not (Test-Path $py_exe)) {
    Write-Output "错误：未找到 Python 解释器：$py_exe"
    exit 1
}

Write-Output "正在创建虚拟环境 .venv ..."
& $py_exe -m venv (Join-Path $root ".venv")

$pip = Join-Path $root ".venv\Scripts\pip.exe"
Write-Output "正在升级 pip ..."
& $pip install --upgrade pip -i $mirror --trusted-host $turst

Write-Output "正在安装 numpy pypdf pytest ..."
& $pip install numpy pypdf pytest -i $mirror --trusted-host $turst

Write-Output "依赖安装完成（numpy / pypdf / pytest）。"

