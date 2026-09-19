# -*- coding: utf-8 -*-
"""检索模块：把用户问题编码成向量，去索引里取最相关的几块。

要点：
- 查询和文档用“同一个后端、同一种归一化”，否则余弦没意义。
- k 不能超过索引里的块数（防御）。
- 过滤掉 faiss 可能返回的 -1 无效下标。
- 相似度阈值（yuling_xianzhi）只用于“展示/生成”，不影响排名本身。
"""

import numpy as np


def jiansuo(suoyin, chaxun, houduan, peizhi, doc_filter=None):
    """默认检索：返回 top_k（且分数 >= 阈值）的片段。"""
    query_vec = houduan.bianma(chaxun, shifou_chaxun=True)
    k = int(peizhi.top_k)
    if k > suoyin.kuai_shu:
        k = suoyin.kuai_shu
    yuliang = getattr(peizhi, "yuling_xianzhi", None)
    jieguo = suoyin.search(query_vec, k, yuliang=yuliang, doc_filter=doc_filter)
    jieguo = [j for j in jieguo if j["idx"] >= 0]
    return jieguo


def jiansuo_candidate(suoyin, chaxun, houduan, k, doc_filter=None):
    """取 top-k 候选（忽略阈值），给评测用——评测看的是排名，不是阈值。"""
    query_vec = houduan.bianma(chaxun, shifou_chaxun=True)
    k = int(k)
    if k > suoyin.kuai_shu:
        k = suoyin.kuai_shu
    jieguo = suoyin.search(query_vec, k, yuliang=None, doc_filter=doc_filter)
    jieguo = [j for j in jieguo if j["idx"] >= 0]
    return jieguo
