# -*- coding: utf-8 -*-
"""pytest 公共夹具：构造临时配置、建索引、生成测试用 PDF。"""
import os
import sys
import tempfile

import pytest

# 让 tests 能 import 到项目根和 src
_GEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _GEN)

from src.peizhi import huoq_peizhi
from src.liucheng import jianku


def xie_jianyi_pdf(lujing, ye_mian_liebiao):
    """生成一个最小可用的 PDF（用内置 Helvetica 字体，ASCII 文本）。

    仅用于单元测试里验证“PDF 解析/空页/页码”这些能力，不依赖任何第三方 PDF 库。
    """
    objs = {}
    n = len(ye_mian_liebiao)
    font_obj = 3
    page_objs = [4 + i * 2 for i in range(n)]
    content_objs = [5 + i * 2 for i in range(n)]
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join("%d 0 R" % p for p in page_objs)
    objs[2] = ("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, n)).encode("latin-1")
    objs[font_obj] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    for i, lines in enumerate(ye_mian_liebiao):
        content = "BT /F1 12 Tf 50 780 Tm\n"
        for ln in lines:
            ln = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content += "(%s) Tj\n0 -15 Td\n" % ln
        content += "ET"
        cb = content.encode("latin-1")
        objs[content_objs[i]] = b"<< /Length %d >>\nstream\n" % len(cb) + cb + b"\nendstream"
        objs[page_objs[i]] = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
            % (font_obj, content_objs[i])
        ).encode("latin-1")
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for k in sorted(objs):
        offsets.append((k, len(out)))
        out += ("%d 0 obj\n" % k).encode("latin-1") + objs[k] + b"\nendobj\n"
    xref = len(out)
    total = len(objs) + 1
    out += ("xref\n0 %d\n" % total).encode("latin-1")
    out += b"0000000000 65535 f \n"
    for k, off in offsets:
        out += ("%010d 00000 n \n" % off).encode("latin-1")
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (total, xref)).encode("latin-1")
    with open(lujing, "wb") as f:
        f.write(out)


@pytest.fixture
def peizhi_tmp(tmp_path):
    p = huoq_peizhi()
    p.cunchu_mulu = str(tmp_path)
    p.suoyin_lujing = str(tmp_path / "index.npz")
    p.meta_lujing = str(tmp_path / "meta.json")
    p.shuju_mulu = os.path.join(_GEN, "data")
    p.pingce_mulu = os.path.join(_GEN, "pingce")
    return p


@pytest.fixture(scope="session")
def yijing_suoyin():
    """基于项目自带 data/ 建一次索引（会话级，省时间）。"""
    tmp = tempfile.mkdtemp(prefix="rag_test_")
    p = huoq_peizhi()
    p.cunchu_mulu = tmp
    p.suoyin_lujing = os.path.join(tmp, "index.npz")
    p.meta_lujing = os.path.join(tmp, "meta.json")
    p.shuju_mulu = os.path.join(_GEN, "data")
    p.pingce_mulu = os.path.join(_GEN, "pingce")
    suoyin, houduan, parsed = jianku(p)
    return suoyin, houduan, parsed


@pytest.fixture
def pdf_writer():
    return xie_jianyi_pdf
