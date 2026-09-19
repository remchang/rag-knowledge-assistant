# -*- coding: utf-8 -*-
"""检索行为测试：top-k 截断 / 分数降序 / 无 -1 下标 / 文档过滤。"""
import sys
import os

_GEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _GEN)

from src.jiansuo import jiansuo


def test_jiansuo_topk(yijing_suoyin, peizhi_tmp):
    suoyin, houduan, parsed = yijing_suoyin
    res = jiansuo(suoyin, "MIT 许可证对商业使用有什么限制？", houduan, peizhi_tmp)
    assert 1 <= len(res) <= peizhi_tmp.top_k
    scores = [r["score"] for r in res]
    assert scores == sorted(scores, reverse=True)
    # faiss 可能返回 -1 无效下标，这里要确保被过滤掉
    assert all(r["idx"] >= 0 for r in res)


def test_jiansuo_doc_filter(yijing_suoyin, peizhi_tmp):
    suoyin, houduan, parsed = yijing_suoyin
    # 用一个不存在的文档过滤集 -> 结果应为空
    res = jiansuo(suoyin, "MIT 许可证", houduan, peizhi_tmp, doc_filter={"doc_bu_cun_zai"})
    assert res == []
