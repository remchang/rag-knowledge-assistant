# -*- coding: utf-8 -*-
"""检索评价测试：跑 20 题，断言 Recall@5 >= 0.8（实际为 1.0），并校验评测集结构。"""
import json
import os
import sys

_GEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _GEN)

from src.pingce import yunxing_pingce, zhuc_jiank_pingce
from src.liucheng import jianku


def _du_qu_wenti(peizhi_tmp):
    with open(os.path.join(peizhi_tmp.pingce_mulu, "wenti.json"), "r", encoding="utf-8") as f:
        return json.load(f)["wenti_liebiao"]


def test_recall(yijing_suoyin, peizhi_tmp):
    suoyin, houduan, parsed = yijing_suoyin
    wenti = _du_qu_wenti(peizhi_tmp)
    jieguo = yunxing_pingce(wenti, suoyin, houduan, peizhi_tmp, pingjia_k=5)

    # 关键断言：Recall@5 达到设定目标
    assert jieguo["recall@5"] >= 0.8, "Recall@5=%.4f 低于 0.8" % jieguo["recall@5"]
    assert jieguo["recall@1"] >= 0.8
    assert 0.0 <= jieguo["wu_hit_rate"] <= 1.0
    assert jieguo["avg_latency_s"] >= 0

    # 至少有 5 题有多个标准证据块
    duo = [w for w in wenti if not w.get("ku_wai") and len(w.get("biaozhi", [])) > 1]
    assert len(duo) >= 5, "多标准证据块题数=%d，应>=5" % len(duo)
    # 知识库外题数 == 4
    assert sum(1 for w in wenti if w.get("ku_wai")) == 4


def test_pingce_xieru_wenjian(yijing_suoyin, peizhi_tmp, tmp_path):
    suoyin, houduan, parsed = yijing_suoyin
    jl = str(tmp_path / "jieguo.json")
    rl = str(tmp_path / "renshen.json")
    jieguo, renshen = zhuc_jiank_pingce(peizhi_tmp, suoyin, houduan,
                                        jieguo_lujing=jl, renshen_lujing=rl)
    assert os.path.exists(jl) and os.path.exists(rl)
    assert jieguo["recall@5"] >= 0.8
    assert len(renshen) == 10
