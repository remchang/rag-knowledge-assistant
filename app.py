# -*- coding: utf-8 -*-
"""Streamlit 界面（可选运行）。

注意：本文件顶部 import streamlit，但项目默认不需要安装 streamlit。
要跑界面，请先自己装：pip install streamlit（见 scripts/anzhuang.ps1 里已含）。
所有核心逻辑都在 src/ 里，本文件只做薄封装，不绑定 UI。

运行：streamlit run app.py
"""

import os
import sys

import streamlit as st

# 让 src 可被 import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.peizhi import huoq_peizhi
from src.liucheng import jianku, jiazai_suoyin, wenda
from src.jiexi import liebie_wenjian

st.set_page_config(page_title="智能知识问答（RAG）", layout="wide")
st.title("基于开源大模型的智能知识问答系统（RAG）")

peizhi = huoq_peizhi()

# 侧栏：索引状态与重建
with st.sidebar:
    st.header("索引状态")
    if os.path.exists(peizhi.suoyin_lujing) and os.path.exists(peizhi.meta_lujing):
        try:
            suoyin, houduan = jiazai_suoyin(peizhi)
            st.success("索引已加载：%d 个块" % suoyin.kuai_shu)
            st.write("嵌入后端：", houduan.mingzi)
            st.write("模型 ID：", suoyin.moxing_id)
        except Exception as e:
            st.error("索引加载失败：%s" % e)
            suoyin, houduan = None, None
    else:
        st.warning("尚未建索引")
        suoyin, houduan = None, None

    if st.button("重新建索引（解析 data/ 下文档）"):
        with st.spinner("正在解析、分块、编码、建索引…"):
            suoyin, houduan, parsed = jianku(peizhi)
        st.success("建索引完成：%d 个块" % suoyin.kuai_shu)

# 文档管理
st.header("文档管理（data/）")
wenjian = liebie_wenjian(peizhi.shuju_mulu)
st.write("当前索引来源文档：", [os.path.basename(w) for w in wenjian])

# 提问
st.header("提问")
chaxun = st.text_area("输入你的问题：", height=80)
if st.button("提问") and chaxun.strip():
    if suoyin is None:
        suoyin, houduan = jiazai_suoyin(peizhi)
    with st.spinner("检索中…"):
        hd = wenda(chaxun, peizhi, suoyin, houduan)
    st.subheader("运行模式")
    st.write("嵌入后端：%s ｜ 生成模式：%s" % (hd.get("houduan"), hd.get("shengcheng_moshi")))
    st.info(hd.get("tishi", ""))
    if hd.get("zhaiyao"):
        st.subheader("摘要（基于句子选择）")
        st.write(hd["zhaiyao"])
    st.subheader("来源片段 / 证据")
    for z in hd.get("zhengju", []):
        with st.expander("[{S%d}] %s  分数=%.4f" % (z["bianhao"], z.get("source"), z["score"])):
            if z.get("page"):
                st.caption("页码：%s" % z["page"])
            if z.get("heading"):
                st.caption("标题：%s" % z["heading"])
            st.write(z["text"])
    if not hd.get("shifou_shengcheng"):
        st.caption("说明：当前为降级模式，未进行大模型生成，以上为原文证据。")
