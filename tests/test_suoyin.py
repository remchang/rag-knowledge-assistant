# -*- coding: utf-8 -*-
"""索引测试：向量数 / 保存加载 / 模型ID校验 / 块数不一致报错 / 检索（>=5 项）"""
import json
import os
import sys

import numpy as np

_GEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _GEN)

from src.liucheng import jianku
from src.suoyin import NumpySuoyin, xuanze_suoyin
from src.xiangliang import xuanze_houduan


def test_xianliang_shu(yijing_suoyin):
    suoyin, houduan, parsed = yijing_suoyin
    # 向量数、元信息数、块数三者必须一致
    assert suoyin.kuai_shu == len(suoyin.meta)
    assert suoyin.kuai_shu == len(suoyin.vectors)
    assert suoyin.kuai_shu > 0
    # 每个向量维度一致
    dim = suoyin.vectors[0].shape[0]
    assert all(v.shape[0] == dim for v in suoyin.vectors)


def test_baocun_jiazai(peizhi_tmp):
    suoyin, houduan, parsed = jianku(peizhi_tmp)
    n = suoyin.kuai_shu
    # 重新加载
    s2 = xuanze_suoyin(peizhi_tmp)
    s2.load(peizhi_tmp.suoyin_lujing, peizhi_tmp.meta_lujing, houduan.moxing_id)
    assert s2.kuai_shu == n
    # 某个块的文本应当能原样找回
    assert s2.meta[0]["text"] == suoyin.meta[0]["text"]
    assert s2.moxing_id == houduan.moxing_id


def test_moxing_id_jiaoyan(peizhi_tmp):
    suoyin, houduan, parsed = jianku(peizhi_tmp)
    s2 = xuanze_suoyin(peizhi_tmp)
    # 用错误的模型 ID 去加载 -> 必须报错，不能悄悄用上
    try:
        s2.load(peizhi_tmp.suoyin_lujing, peizhi_tmp.meta_lujing, "cuowu-moxing-id")
        raise AssertionError("应当因模型 ID 不一致而报错")
    except ValueError as e:
        assert "模型 ID" in str(e)


def test_kuai_shu_buyizhi(peizhi_tmp):
    suoyin, houduan, parsed = jianku(peizhi_tmp)
    n = suoyin.kuai_shu
    # 故意把 meta.json 里的 kuai_shu 改错
    with open(peizhi_tmp.meta_lujing, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta["kuai_shu"] = n + 5
    with open(peizhi_tmp.meta_lujing, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    s2 = xuanze_suoyin(peizhi_tmp)
    try:
        s2.load(peizhi_tmp.suoyin_lujing, peizhi_tmp.meta_lujing, houduan.moxing_id)
        raise AssertionError("块数不一致时必须报错")
    except ValueError as e:
        assert "块数" in str(e) or "不一致" in str(e)


def test_add_search():
    s = NumpySuoyin()
    v0 = np.array([1.0, 0.0, 0.0], dtype="float32")
    v1 = np.array([0.0, 1.0, 0.0], dtype="float32")
    s.add([v0, v1], [{"text": "甲", "doc_id": "d", "source": "s", "page": 1, "heading": ""},
                     {"text": "乙", "doc_id": "d", "source": "s", "page": 2, "heading": ""}])
    # 归一化后检索
    q = np.array([1.0, 0.0, 0.0], dtype="float32")
    q = q / np.linalg.norm(q)
    res = s.search(q, k=2)
    assert res[0]["idx"] == 0
    assert all(r["idx"] >= 0 for r in res)  # 没有 -1 无效下标
    # doc_filter 过滤
    res2 = s.search(q, k=2, doc_filter={"bu_cun_zai"})
    assert res2 == []
