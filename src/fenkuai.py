# -*- coding: utf-8 -*-
"""分块模块：把解析出来的段落切成固定大小的块。

默认 400 字符一块、相邻块重叠 80 字符（滑动窗口）。

为什么不在标题和正文之间硬切：
中文教材里“## 某个小标题”往往紧跟着它的解释。如果我们按固定字数一刀切，
很可能把“小标题”切在上一块末尾、“解释”切在下一块开头，检索时两块都不完整。
所以这里优先在“段落边界”切断——只有当前块已经足够长、再加一段会超时才切，
标题段本身会作为新块的起点，从而避免标题孤零零被切断。
"""

import re


def _hebing_changdu(liebiao):
    return sum(len(x) for x in liebiao)


def fenkuai_wenben(wenben, peizhi, doc_id, source, page=None, heading=""):
    """对一个纯文本字符串直接分块（测试或单段场景用）。"""
    # 先把文本按换行切成小段，再按窗口拼块
    xiaoduan = [x for x in re.split(r"\n+", wenben) if x.strip()]
    if not xiaoduan:
        xiaoduan = [wenben]
    return _pinjie_kuai(xiaoduan, [page] * len(xiaoduan), [heading] * len(xiaoduan),
                       peizhi, doc_id, source)


def _pinjie_kuai(paras, pages, headings, peizhi, doc_id, source):
    """paras/pages/headings 是等长的三段信息，按窗口拼成块。"""
    da = peizhi.fenkuai_daxiao
    chong = peizhi.fenkuai_chongdie
    kuai = []
    cur = []          # 当前块累积的小段
    cur_page = None
    cur_heading = ""
    ci = 0
    last_tail = ""

    def qiepian():
        nonlocal cur, cur_page, cur_heading, ci, last_tail
        txt = "\n".join(cur).strip()
        if txt:
            kuai.append({
                "chunk_id": "%s_c%d" % (doc_id, ci),
                "doc_id": doc_id,
                "source": source,
                "page": cur_page,
                "heading": cur_heading,
                "text": txt,
            })
            ci += 1
        # 记录刚切出这块的文本尾部，作为下一块的重叠开头
        whole = "\n".join(cur)
        last_tail = whole[-chong:] if len(whole) > chong else whole
        cur = []

    for i, ptxt in enumerate(paras):
        page = pages[i]
        heading = headings[i] if i < len(headings) else ""
        # 当前块已有内容，再加这一段会超尺寸 -> 先切断
        if cur and (_hebing_changdu(cur) + len(ptxt) > da):
            qiepian()
            if last_tail:
                cur = [last_tail]
        cur.append(ptxt)
        cur_page = page if page is not None else cur_page
        if heading:
            cur_heading = heading
        # 满了也切（保证单块不超过 da 太多）
        if _hebing_changdu(cur) >= da:
            qiepian()
            if last_tail:
                cur = [last_tail]
    qiepian()
    return kuai


def fenkuai_wenjian(jiexi_jieguo, peizhi):
    """对一个 jiexi.jiexi_wenjian 的返回结果做分块。"""
    doc_id = jiexi_jieguo["doc_id"]
    source = jiexi_jieguo["wenjian_ming"]
    paras = [(d["text"], d.get("page"), d.get("heading", "")) for d in jiexi_jieguo["duanluo"]]
    if not paras:
        return []
    xs = [p[0] for p in paras]
    ps = [p[1] for p in paras]
    hs = [p[2] for p in paras]
    return _pinjie_kuai(xs, ps, hs, peizhi, doc_id, source)
