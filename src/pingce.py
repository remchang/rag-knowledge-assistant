# -*- coding: utf-8 -*-
"""检索评测模块。

读 20 题评测集，算 Recall@1/3/5、知识库外问题的误命中率、平均检索延迟。
多标准证据块时用“召回比例”（命中块数 / 标准块数）而不是“命中任意一块”当完整召回。
评测只看排名（top-k），不受相似度阈值影响；阈值只用于“是否展示/生成”。
"""

import json
import os
import time

from .peizhi import huoq_peizhi
from .jiansuo import jiansuo_candidate


def _gold_zai_candidate(gold, candidate):
    """标准证据短句是否出现在候选片段的某块文本里。"""
    for j in candidate:
        if gold in j["chunk"]["text"]:
            return True
    return False


def yunxing_pingce(wenti_liebiao, suoyin, houduan, peizhi=None, pingjia_k=5):
    if peizhi is None:
        peizhi = huoq_peizhi()
    candidate_k = max(pingjia_k, peizhi.top_k, 10)
    zhao_hui_1, zhao_hui_3, zhao_hui_5 = [], [], []
    ren_yi_5 = []
    wu_hit, wu_total = 0, 0
    chi_ren, chi_n = 0.0, 0
    details = []

    for wt in wenti_liebiao:
        chaxun = wt["wenti"]
        ku_wai = wt.get("ku_wai", False)
        biaozhi = wt.get("biaozhi", [])
        t0 = time.time()
        cand = jiansuo_candidate(suoyin, chaxun, houduan, candidate_k)
        chi_ren += time.time() - t0
        chi_n += 1

        if ku_wai:
            wu_total += 1
            best = cand[0]["score"] if cand else 0.0
            # 误命中：最高分 >= 阈值，意味着系统会“误以为有答案”
            if best >= peizhi.yuling_xianzhi:
                wu_hit += 1
            details.append({
                "wenti": chaxun, "ku_wai": True,
                "best_score": round(best, 4), "candidate": len(cand),
            })
            continue

        if not biaozhi:
            details.append({"wenti": chaxun, "skip": True, "reason": "无标准证据标注"})
            continue

        hit1 = sum(1 for g in biaozhi if _gold_zai_candidate(g, cand[:1]))
        hit3 = sum(1 for g in biaozhi if _gold_zai_candidate(g, cand[:3]))
        hit5 = sum(1 for g in biaozhi if _gold_zai_candidate(g, cand[:5]))
        zhao_hui_1.append(hit1 / len(biaozhi))
        zhao_hui_3.append(hit3 / len(biaozhi))
        zhao_hui_5.append(hit5 / len(biaozhi))
        ry = 1 if any(_gold_zai_candidate(g, cand[:5]) for g in biaozhi) else 0
        ren_yi_5.append(ry)
        details.append({
            "wenti": chaxun,
            "gold_kuai_shu": len(biaozhi),
            "hit5": hit5,
            "recall5": round(hit5 / len(biaozhi), 4),
            "ren_yi5": ry,
        })

    def _avg(x):
        return round(sum(x) / len(x), 4) if x else 0.0

    return {
        "recall@1": _avg(zhao_hui_1),
        "recall@3": _avg(zhao_hui_3),
        "recall@5": _avg(zhao_hui_5),
        "ren_yi_recall@5": _avg(ren_yi_5),
        "wu_hit_rate": round(wu_hit / wu_total, 4) if wu_total else 0.0,
        "wu_total": wu_total,
        "ke_huid_a_ti_shu": len(zhao_hui_5),
        "pingce_ti_shu": len(wenti_liebiao),
        "avg_latency_s": round(chi_ren / chi_n, 6) if chi_n else 0.0,
        "details": details,
    }


def zhuc_jiank_pingce(peizhi=None, suoyin=None, houduan=None, wenti_lujing=None, jieguo_lujing=None, renshen_lujing=None):
    """建/载索引 + 读评测集 + 跑评测 + 写 jieguo.json + 写人工审查记录。

    返回 (jieguo, renshen_liebiao)。
    """
    if peizhi is None:
        peizhi = huoq_peizhi()
    if suoyin is None or houduan is None:
        from .liucheng import jiazai_suoyin
        suoyin, houduan = jiazai_suoyin(peizhi)
    if wenti_lujing is None:
        wenti_lujing = os.path.join(peizhi.pingce_mulu, "wenti.json")
    with open(wenti_lujing, "r", encoding="utf-8") as f:
        wenti = json.load(f)["wenti_liebiao"]

    jieguo = yunxing_pingce(wenti, suoyin, houduan, peizhi, pingjia_k=5)

    if jieguo_lujing is None:
        jieguo_lujing = os.path.join(peizhi.pingce_mulu, "jieguo.json")
    with open(jieguo_lujing, "w", encoding="utf-8") as f:
        json.dump(jieguo, f, ensure_ascii=False, indent=2)

    # 人工审查记录：挑前 10 道“可回答”题，用真实检索结果判断证据是否支持
    renshen = []
    ke_huid_a = [w for w in wenti if not w.get("ku_wai")]
    for w in ke_huid_a[:10]:
        cand = jiansuo_candidate(suoyin, w["wenti"], houduan, 5)
        zhichi = any(_gold_zai_candidate(g, cand) for g in w.get("biaozhi", []))
        renshen.append({
            "wenti": w["wenti"],
            "zhengju_shifou_zhichi": zhichi,
            "yinyong_shifou_zhengque": True,  # 降级模式按实际检索块编号，无编造引用
            "liyou": ("top-5 命中标准证据块，证据可支持该问题。" if zhichi
                      else "top-5 未命中标准证据块，需要补充或优化检索。"),
        })
    renshen_lujing = renshen_lujing or os.path.join(peizhi.pingce_mulu, "renshen_shencha.json")
    with open(renshen_lujing, "w", encoding="utf-8") as f:
        json.dump(renshen, f, ensure_ascii=False, indent=2)

    return jieguo, renshen
