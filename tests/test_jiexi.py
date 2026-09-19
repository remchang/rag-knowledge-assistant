# -*- coding: utf-8 -*-
"""解析测试：TXT / MD / PDF / 空页 / 重复去重 / 编码问题（>=6 项）"""
import os
import sys

_GEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _GEN)

from src import jiexi


def test_jiexi_txt(tmp_path):
    fp = tmp_path / "a.txt"
    fp.write_text("第一段内容。\n\n第二段内容。\n\n第三段。", encoding="utf-8")
    jg = jiexi.jiexi_wenjian(str(fp))
    assert jg["geshi"] == "txt"
    assert jg["sha256"] and len(jg["sha256"]) == 64
    assert jg["doc_id"].startswith("doc_")
    # 三段 -> 三个段落
    assert len(jg["duanluo"]) == 3
    assert all("paragraph" in d and "text" in d for d in jg["duanluo"])


def test_jiexi_md(tmp_path):
    fp = tmp_path / "b.md"
    fp.write_text("# 标题一\n正文关于标题一。\n\n## 小标题\n正文关于小标题。\n", encoding="utf-8")
    jg = jiexi.jiexi_wenjian(str(fp))
    assert jg["geshi"] == "md"
    # 标题段也应被记录，并带 heading
    headings = [d["heading"] for d in jg["duanluo"]]
    assert "标题一" in headings
    # 某段 heading 应继承自最近标题
    assert any(d["heading"] == "小标题" for d in jg["duanluo"])


def test_jiexi_pdf(pdf_writer, tmp_path):
    fp = tmp_path / "c.pdf"
    pdf_writer(str(fp), [["Hello page one line A", "Hello page one line B"], ["Second page text"]])
    jg = jiexi.jiexi_wenjian(str(fp))
    assert jg["geshi"] == "pdf"
    # 两页都应抽到，且带页码
    pages = [d["page"] for d in jg["duanluo"]]
    assert 1 in pages and 2 in pages
    wenben = jg["quanbu_wenben"]
    assert "Hello page one" in wenben and "Second page" in wenben


def test_jiexi_kongye(pdf_writer, tmp_path):
    # 第 2 页是空页：应当记到 kongye，并明确提示“需要 OCR”
    fp = tmp_path / "d.pdf"
    pdf_writer(str(fp), [["First page has text"], [""]])
    jg = jiexi.jiexi_wenjian(str(fp))
    assert len(jg["kongye"]) == 1
    assert jg["kongye"][0]["page"] == 2
    assert "需要 OCR" in jg["kongye"][0]["beizhu"]
    # 空页不应进入可检索段落
    assert all(d["page"] != 2 for d in jg["duanluo"])


def test_jiexi_chongfu_sha256(tmp_path):
    # 两个文件内容相同 -> sha256 与 doc_id 必须一致（去重依据）
    f1 = tmp_path / "e1.txt"
    f2 = tmp_path / "e2.txt"
    neirong = "这是一份完全一样的文档内容，用于测试去重。"
    f1.write_text(neirong, encoding="utf-8")
    f2.write_text(neirong, encoding="utf-8")
    j1 = jiexi.jiexi_wenjian(str(f1))
    j2 = jiexi.jiexi_wenjian(str(f2))
    assert j1["sha256"] == j2["sha256"]
    assert j1["doc_id"] == j2["doc_id"]


def test_jiexi_bianma(tmp_path):
    # 编码问题：GBK 编码的文件应当能被正确读出（不出现乱码）
    fp = tmp_path / "g.txt"
    with open(str(fp), "wb") as f:
        f.write("开源软件与新技术课程实验".encode("gbk"))
    jg = jiexi.jiexi_wenjian(str(fp))
    assert "开源软件与新技术课程实验" in jg["quanbu_wenben"]
    # BOM 的 utf-8 也应被正确去掉
    fb = tmp_path / "bom.txt"
    with open(str(fb), "wb") as f:
        f.write("带 BOM 的文档".encode("utf-8-sig"))
    jg2 = jiexi.jiexi_wenjian(str(fb))
    assert jg2["quanbu_wenben"] == "带 BOM 的文档"
