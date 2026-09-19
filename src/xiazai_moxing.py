# -*- coding: utf-8 -*-
"""下载真实模型权重（默认不执行，仅给装好环境后的同学用）。

用 huggingface_hub 的 snapshot_download，固定 revision 和 local_dir，
保证可离线复现、可缓存。模型清单见 model_list.md（SHA256 待下载后填写）。
"""

import os

from .peizhi import huoq_peizhi

# 固定 revision，保证“下载的就是评测用的那版”
MOXING_PEIZHI = [
    {
        "ming": "bge-small-zh-v1.5",
        "repo": "BAAI/bge-small-zh-v1.5",
        "revision": "7999e1d3359715c523056ef9478215996d62a620",
    },
    {
        "ming": "Qwen2.5-1.5B-Instruct",
        "repo": "Qwen/Qwen2.5-1.5B-Instruct",
        "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
    },
    {
        "ming": "Qwen2.5-0.5B-Instruct",
        "repo": "Qwen/Qwen2.5-0.5B-Instruct",
        "revision": "7ae557604adf67be50417f59c2c2f167def9a775",
    },
]


def zhuxia(ming=None):
    """下载模型。ming 为 None 时下载全部。需要先 pip install huggingface_hub。"""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise RuntimeError("请先安装 huggingface_hub：pip install huggingface_hub")
    p = huoq_peizhi()
    moxing_mulu = os.path.join(p.cunchu_mulu, "moxing")
    os.makedirs(moxing_mulu, exist_ok=True)
    for cfg in MOXING_PEIZHI:
        if ming and cfg["ming"] != ming:
            continue
        local_dir = os.path.join(moxing_mulu, cfg["ming"])
        print("开始下载：%s (revision=%s) -> %s" % (cfg["repo"], cfg["revision"], local_dir))
        snapshot_download(repo_id=cfg["repo"], revision=cfg["revision"], local_dir=local_dir)
        print("完成：%s" % cfg["ming"])
