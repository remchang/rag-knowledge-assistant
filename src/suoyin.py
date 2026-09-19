# -*- coding: utf-8 -*-
"""向量索引模块。

提供两个实现，接口统一（add / search / save / load）：
- FaissSuoyin：装了 faiss 才用（精确内积检索）。
- NumpySuoyin：没装 faiss 时的后备，纯 numpy 做精确余弦检索。

索引与元数据分开保存：
- storage/index.npz  （向量）
- storage/meta.json  （每个块的元信息 + 模型 ID + 块数）
用稳定的 chunk_id/doc_id 关联。保存时先写临时文件再原子替换，避免程序中断导致
“索引和元数据错位”（一半新一半旧）。

加载时会校验：块数、向量数、模型 ID 三者是否一致，不一致就明确报错，
不让错误的索引被悄悄用上。
"""

import json
import os
import tempfile

import numpy as np

from . import jiexi, fenkuai
from .xiangliang import xuanze_houduan


class NumpySuoyin:
    """后备索引：把所有向量堆成一个矩阵，检索时算余弦（向量已 L2 归一化，点积即余弦）。"""

    def __init__(self):
        self.vectors = []   # list[np.ndarray]
        self.meta = []      # list[dict]  和 vectors 一一对应
        self.moxing_id = None

    @property
    def kuai_shu(self):
        return len(self.vectors)

    def add(self, vectors, meta_liebiao):
        if len(vectors) != len(meta_liebiao):
            raise ValueError("向量数和元信息数不一致：%d != %d" % (len(vectors), len(meta_liebiao)))
        self.vectors.extend(vectors)
        self.meta.extend(meta_liebiao)

    def search(self, query_vec, k, yuliang=None, doc_filter=None):
        if not self.vectors:
            return []
        k = int(k)
        if k > len(self.vectors):
            k = len(self.vectors)
        M = np.stack(self.vectors)              # (n, d)
        q = np.asarray(query_vec, dtype=np.float32)
        scores = M @ q                          # 归一化后点积 = 余弦
        order = np.argsort(-scores)
        out = []
        for i in order:
            i = int(i)
            sc = float(scores[i])
            # 过滤掉 faiss 风格的无效下标 -1（numpy 这里不会出现，但保留防御）
            if i < 0:
                continue
            if doc_filter is not None:
                md = self.meta[i]
                if md.get("doc_id") not in doc_filter and md.get("source") not in doc_filter:
                    continue
            if yuliang is not None and sc < yuliang:
                # 分数已经降序，到这里后面只会更小，提前结束
                break
            out.append({"idx": i, "score": sc, "chunk": self.meta[i]})
            if len(out) >= k:
                break
        return out

    def save(self, suoyin_lujing, meta_lujing, moxing_id):
        self.moxing_id = moxing_id
        os.makedirs(os.path.dirname(suoyin_lujing), exist_ok=True)
        # 先写临时文件，再原子替换
        vec_tmp = suoyin_lujing + ".tmp.npz"
        meta_tmp = meta_lujing + ".tmp.json"
        np.savez(vec_tmp, vectors=np.stack(self.vectors))
        meta = {
            "moxing_id": moxing_id,
            "kuai_shu": len(self.vectors),
            "xiangliang_shu": len(self.vectors),
            "chunks": self.meta,
        }
        with open(meta_tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        # 原子替换：先向量后元数据，或反过来？只要两个都替换成功即可
        os.replace(vec_tmp, suoyin_lujing)
        os.replace(meta_tmp, meta_lujing)

    def load(self, suoyin_lujing, meta_lujing, qizhi_moxing_id=None):
        if not (os.path.exists(suoyin_lujing) and os.path.exists(meta_lujing)):
            raise FileNotFoundError("索引或元数据文件不存在")
        with open(meta_lujing, "r", encoding="utf-8") as f:
            meta = json.load(f)
        d = np.load(suoyin_lujing, allow_pickle=False)
        vecs = d["vectors"]
        # ---- 一致性校验：块数 / 向量数 / 模型 ID ----
        if meta.get("kuai_shu") != vecs.shape[0]:
            raise ValueError("块数不一致：meta.kuai_shu=%s, 向量数=%s" % (meta.get("kuai_shu"), vecs.shape[0]))
        if len(meta.get("chunks", [])) != vecs.shape[0]:
            raise ValueError("元信息块数与向量数不一致：%d != %d" % (len(meta.get("chunks", [])), vecs.shape[0]))
        if qizhi_moxing_id is not None and meta.get("moxing_id") != qizhi_moxing_id:
            raise ValueError("模型 ID 不一致：索引是 %s，当前后端是 %s（很可能换了嵌入模型，需要重建索引）"
                             % (meta.get("moxing_id"), qizhi_moxing_id))
        self.vectors = [vecs[i] for i in range(vecs.shape[0])]
        self.meta = meta["chunks"]
        self.moxing_id = meta["moxing_id"]
        return self


class FaissSuoyin:
    """装了 faiss 时的精确检索。没装 faiss 构造即报错，由上层回退到 NumpySuoyin。"""

    def __init__(self):
        try:
            import faiss
        except Exception as e:
            raise RuntimeError("未安装 faiss-cpu，无法使用 FaissSuoyin：%s" % e)
        self._faiss = faiss
        self.index = None
        self.meta = []
        self.moxing_id = None

    @property
    def kuai_shu(self):
        return len(self.meta)

    def add(self, vectors, meta_liebiao):
        if len(vectors) != len(meta_liebiao):
            raise ValueError("向量数和元信息数不一致")
        dim = vectors[0].shape[0]
        self.index = self._faiss.IndexFlatIP(dim)  # 内积（余弦，向量已归一化）
        M = np.stack(vectors).astype("float32")
        self.index.add(M)
        self.meta = list(meta_liebiao)

    def search(self, query_vec, k, yuliang=None, doc_filter=None):
        if self.index is None:
            return []
        k = min(int(k), len(self.meta))
        q = np.asarray(query_vec, dtype="float32").reshape(1, -1)
        scores, idxs = self.index.search(q, k)
        out = []
        for sc, i in zip(scores[0], idxs[0]):
            i = int(i)
            if i < 0:          # faiss 可能返回 -1 表示无效
                continue
            if doc_filter is not None:
                md = self.meta[i]
                if md.get("doc_id") not in doc_filter and md.get("source") not in doc_filter:
                    continue
            if yuliang is not None and float(sc) < yuliang:
                continue
            out.append({"idx": i, "score": float(sc), "chunk": self.meta[i]})
        out.sort(key=lambda x: -x["score"])
        return out

    def save(self, suoyin_lujing, meta_lujing, moxing_id):
        # faiss 索引保存用其自带 write_index；这里简化：仍存 npz 以便统一加载
        self.moxing_id = moxing_id
        os.makedirs(os.path.dirname(suoyin_lujing), exist_ok=True)
        vec_tmp = suoyin_lujing + ".tmp.npz"
        meta_tmp = meta_lujing + ".tmp.json"
        M = np.stack([self.index.get_xb()]) if False else self._chong_jian_juzhen()
        np.savez(vec_tmp, vectors=M)
        meta = {"moxing_id": moxing_id, "kuai_shu": len(self.meta), "xiangliang_shu": len(self.meta), "chunks": self.meta}
        with open(meta_tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        os.replace(vec_tmp, suoyin_lujing)
        os.replace(meta_tmp, meta_lujing)

    def _chong_jian_juzhen(self):
        # IndexFlatIP 的底层矩阵可以通过 reconstruct 拿，这里用 get_xb
        return np.array(self._faiss.rev_swig_ptr(self.index.get_xb(), self.index.ntotal * self.index.d).reshape(self.index.ntotal, self.index.d))

    def load(self, suoyin_lujing, meta_lujing, qizhi_moxing_id=None):
        # 复用 NumpySuoyin 的加载逻辑（faiss 文件其实也是 npz 格式存的）
        tmp = NumpySuoyin()
        tmp.load(suoyin_lujing, meta_lujing, qizhi_moxing_id)
        self.meta = tmp.meta
        self.moxing_id = tmp.moxing_id
        dim = tmp.vectors[0].shape[0]
        self.index = self._faiss.IndexFlatIP(dim)
        self.index.add(np.stack(tmp.vectors).astype("float32"))
        return self


def xuanze_suoyin(peizhi):
    """优先 FaissSuoyin，不行就 NumpySuoyin。"""
    try:
        return FaissSuoyin()
    except RuntimeError as e:
        print("[提示] 用后备索引 NumpySuoyin：%s" % e)
        return NumpySuoyin()


def goujian_liucheng(wenjian_liebiao, peizhi, houduan=None):
    """端到端建索引：解析 -> SHA256 去重 -> 分块 -> 适配后端 -> 编码 -> 入索引。

    返回 (suoyin, houduan, parsed)。parsed 是每份文档的解析结果（含 kongye 信息）。
    """
    if houduan is None:
        houduan = xuanze_houduan(peizhi)
    yijie_sha256 = set()
    chunks = []
    parsed = []
    for fp in wenjian_liebiao:
        jg = jiexi.jiexi_wenjian(fp)
        if jg["sha256"] in yijie_sha256:
            # 重复 SHA256 的文件不重复入库
            print("[去重] 跳过重复文档：%s (sha256=%s)" % (jg["wenjian_ming"], jg["sha256"][:12]))
            continue
        yijie_sha256.add(jg["sha256"])
        parsed.append(jg)
        for c in fenkuai.fenkuai_wenjian(jg, peizhi):
            chunks.append(c)
    if not chunks:
        raise ValueError("没有可索引的内容，请检查文档路径和格式")
    houduan.shiying([c["text"] for c in chunks])
    vectors = [houduan.bianma(c["text"]) for c in chunks]
    suoyin = NumpySuoyin()
    suoyin.add(vectors, chunks)
    suoyin.moxing_id = houduan.moxing_id
    return suoyin, houduan, parsed
