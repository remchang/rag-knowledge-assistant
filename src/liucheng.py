# -*- coding: utf-8 -*-
"""流程编排：建索引 / 加载索引 / 问答。把核心逻辑都放在 src 里，UI 只做薄封装。"""

import os

from .peizhi import huoq_peizhi
from .jiexi import liebie_wenjian
from .suoyin import goujian_liucheng, xuanze_suoyin
from .jiansuo import jiansuo
from .xiangliang import xuanze_houduan, huoq_houduan_mingzi
from .shengcheng import xuanze_shengcheng


def jianku(peizhi=None, wenjian_liebiao=None):
    """解析数据目录 -> 去重 -> 分块 -> 编码 -> 建索引 -> 保存。返回 (suoyin, houduan, parsed)。"""
    if peizhi is None:
        peizhi = huoq_peizhi()
    if wenjian_liebiao is None:
        wenjian_liebiao = liebie_wenjian(peizhi.shuju_mulu)
    suoyin, houduan, parsed = goujian_liucheng(wenjian_liebiao, peizhi)
    suoyin.save(peizhi.suoyin_lujing, peizhi.meta_lujing, houduan.moxing_id)
    return suoyin, houduan, parsed


def jiazai_suoyin(peizhi=None):
    """加载已保存的索引，并做一致性校验。"""
    if peizhi is None:
        peizhi = huoq_peizhi()
    houduan = xuanze_houduan(peizhi)
    suoyin = xuanze_suoyin(peizhi)
    suoyin.load(peizhi.suoyin_lujing, peizhi.meta_lujing, houduan.moxing_id)
    return suoyin, houduan


def wenda(chaxun, peizhi=None, suoyin=None, houduan=None):
    """给定问题，返回检索+生成结果（字典）。核心逻辑不依赖 UI。"""
    if peizhi is None:
        peizhi = huoq_peizhi()
    if suoyin is None or houduan is None:
        suoyin, houduan = jiazai_suoyin(peizhi)
    jieguo = jiansuo(suoyin, chaxun, houduan, peizhi)
    shengcheng_qi = xuanze_shengcheng(peizhi)
    hd = shengcheng_qi.shengcheng(chaxun, jieguo, peizhi)
    hd["houduan"] = huoq_houduan_mingzi(houduan)
    hd["shengcheng_moshi"] = shengcheng_qi.mingzi
    return hd
