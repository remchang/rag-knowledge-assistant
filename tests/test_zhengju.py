# -*- coding: utf-8 -*-
"""回答证据审查：校验人工审查记录文件结构 + 引用校验函数。"""
import json
import os
import sys

_GEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _GEN)

from src.shengcheng import yinyong_jianyan


def test_renshen_jiegou():
    p = os.path.join(_GEN, "pingce", "renshen_shencha.json")
    assert os.path.exists(p), "人工审查记录文件不存在"
    data = json.load(open(p, "r", encoding="utf-8"))
    assert len(data) == 10, "应记录 10 条审查，实际 %d" % len(data)
    for d in data:
        for key in ("wenti", "zhengju_shifou_zhichi", "yinyong_shifou_zhengque", "liyou"):
            assert key in d, "缺少字段 %s" % key
        assert isinstance(d["zhengju_shifou_zhichi"], bool)
        assert isinstance(d["yinyong_shifou_zhengque"], bool)


def test_yinyong_jianyan():
    # 合法引用：编号都在本轮检索结果里
    ok, buliang = yinyong_jianyan("根据[S1]可知答案是甲，详见[S2]。", {1, 2, 3})
    assert ok and buliang == []
    # 非法引用：出现了不在结果里的 [S9]
    ok2, buliang2 = yinyong_jianyan("见[S1]和[S9]。", {1, 2, 3})
    assert (not ok2) and 9 in buliang2
    # 空回答视为无引用问题
    assert yinyong_jianyan("", {1, 2}) == (True, [])
