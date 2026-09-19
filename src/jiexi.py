# -*- coding: utf-8 -*-
"""文档解析模块：把 TXT / Markdown / PDF 读进来，整理成统一的“段落/页”结构。

每个文档会生成一个 doc_id 和内容 SHA256；重复 SHA256 的文件不重复入库
（去重在 jianku 流程里做，这里只把 sha256 算好交出去）。

踩过的坑：
1. Windows 上有些 TXT 是 GBK 编码，直接 utf-8 读会报 UnicodeDecodeError。
   所以这里做了“先试 utf-8，再试 gbk，最后 latin-1”的兜底。
2. PDF 里经常有“扫描页”——文字抽不出来（空字符串）。这种页不能假装索引了，
   要明确标成“需要 OCR，当前未索引”，否则检索时会凭空多出一坨空块。
"""

import hashlib
import os
import re


def jisuan_sha256(neirong):
    """算一段文本的 SHA256（用于文档去重和内容指纹）。"""
    if isinstance(neirong, str):
        neirong = neirong.encode("utf-8")
    return hashlib.sha256(neirong).hexdigest()


def duqu_wenben(wenjian_lujing):
    """读文本文件，自动处理常见编码（utf-8 / utf-8-sig / gbk / latin-1）。

    返回解码后的字符串。这里专门做编码兜底，是为了让“编码问题”测试能过，
    也避免真实场景里遇到老文档就崩。
    """
    with open(wenjian_lujing, "rb") as f:
        raw = f.read()
    # 先把带 BOM 的 utf-8 处理掉
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("gbk")
    except UnicodeDecodeError:
        pass
    # latin-1 一定能解码（不会报错），但中文会是乱码——这是最后兜底
    return raw.decode("latin-1")


def _chaifen_duanluo(wenben):
    """按空行把文本切成段落，去掉纯空白段。返回段落字符串列表。"""
    out = []
    for blk in re.split(r"\n\s*\n", wenben):
        blk = blk.strip()
        if blk:
            out.append(blk)
    return out


def _jiexi_txt(wenjian_ming, neirong):
    duanluo = []
    for i, p in enumerate(_chaifen_duanluo(neirong)):
        duanluo.append({
            "text": p,
            "page": None,
            "paragraph": i,
            "heading": "",
        })
    return duanluo


def _jiexi_md(wenjian_ming, neirong):
    """Markdown：识别 #/##/### 标题，让每个段落带上“它属于哪个标题下”的信息。"""
    duanluo = []
    dangqian_biaoti = ""
    p_idx = 0
    # 按行扫描，遇到标题更新当前标题；遇到连续非空行聚成一个段落
    huancun = []
    for line in neirong.split("\n"):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            # 先把缓存里的段落结算
            if huancun:
                txt = "\n".join(huancun).strip()
                if txt:
                    duanluo.append({"text": txt, "page": None, "paragraph": p_idx, "heading": dangqian_biaoti})
                    p_idx += 1
                huancun = []
            dangqian_biaoti = m.group(2).strip()
            # 标题本身也作为一段，方便检索“标题即答案”的情况
            duanluo.append({"text": dangqian_biaoti, "page": None, "paragraph": p_idx, "heading": dangqian_biaoti})
            p_idx += 1
        elif line.strip():
            huancun.append(line)
        else:
            if huancun:
                txt = "\n".join(huancun).strip()
                if txt:
                    duanluo.append({"text": txt, "page": None, "paragraph": p_idx, "heading": dangqian_biaoti})
                    p_idx += 1
                huancun = []
    if huancun:
        txt = "\n".join(huancun).strip()
        if txt:
            duanluo.append({"text": txt, "page": None, "paragraph": p_idx, "heading": dangqian_biaoti})
    return duanluo


def _jiexi_pdf(wenjian_ming, neirong):
    """PDF：用 pypdf 逐页抽取；空文本页记到 kongye，明确提示需要 OCR。"""
    from pypdf import PdfReader
    reader = PdfReader(neirong)
    duanluo = []
    kongye = []
    for page_no, page in enumerate(reader.pages, start=1):
        try:
            ye_text = page.extract_text() or ""
        except Exception:
            ye_text = ""
        ye_text = ye_text.strip()
        if not ye_text:
            # 关键：空文本页不进索引，但要把“它存在、且需要 OCR”记下来
            kongye.append({"page": page_no, "beizhu": "需要 OCR，当前未索引"})
            continue
        # 一页可能包含多段，按空行继续切；每段都带上页码
        for i, p in enumerate(_chaifen_duanluo(ye_text)):
            duanluo.append({
                "text": p,
                "page": page_no,
                "paragraph": i,
                "heading": "",
            })
    return duanluo, kongye


def jiexi_wenjian(wenjian_lujing):
    """解析一个文档，返回统一结构。

    返回字典：
    {
      "doc_id": str,
      "wenjian_ming": str,
      "sha256": str,
      "geshi": "txt"/"md"/"pdf",
      "quanbu_wenben": str,
      "duanluo": [ {text, page, paragraph, heading}, ... ],
      "kongye": [ {page, beizhu}, ... ]   # 仅 PDF 可能有
    }
    """
    ext = os.path.splitext(wenjian_lujing)[1].lower()
    wenjian_ming = os.path.basename(wenjian_lujing)

    if ext == ".pdf":
        with open(wenjian_lujing, "rb") as f:
            raw = f.read()
        sha256 = jisuan_sha256(raw)
        duanluo, kongye = _jiexi_pdf(wenjian_ming, wenjian_lujing)
        quanbu = "\n".join(d["text"] for d in duanluo)
        geshi = "pdf"
    else:
        neirong = duqu_wenben(wenjian_lujing)
        sha256 = jisuan_sha256(neirong)
        if ext == ".md":
            duanluo = _jiexi_md(wenjian_ming, neirong)
            geshi = "md"
        else:
            duanluo = _jiexi_txt(wenjian_ming, neirong)
            geshi = "txt"
        kongye = []
        quanbu = neirong

    # doc_id 用内容 sha256 前 16 位，保证内容相同则 doc_id 相同（去重用）
    doc_id = "doc_" + sha256[:16]
    return {
        "doc_id": doc_id,
        "wenjian_ming": wenjian_ming,
        "sha256": sha256,
        "geshi": geshi,
        "quanbu_wenben": quanbu,
        "duanluo": duanluo,
        "kongye": kongye,
    }


def liebie_wenjian(mulu):
    """列出目录下所有 .txt/.md/.pdf 文件（不含子目录）。

    注意：排除 README.md 这类“说明文档”，只索引真正的课程正文，
    否则 README 这种元信息会被当成知识库内容。
    """
    out = []
    for ming in sorted(os.listdir(mulu)):
        if ming.lower().endswith((".txt", ".md", ".pdf")):
            if ming.lower().startswith("readme"):
                continue
            out.append(os.path.join(mulu, ming))
    return out
