# -*- coding: utf-8 -*-
"""向量化（Embedding）后端。

本机没装 torch / sentence-transformers，所以默认实际跑的是 Zihouduan（后备后端）：
纯 numpy 实现的“字符 n-gram（1~3）+ TF-IDF + L2 归一化”。它能跑中文，但和真正的
BGE 语义向量差别很大——BGE 是语义相似，n-gram 是字面/词面相似。这点必须在文档里写清楚，
不能假装跑了 BGE。

同时这里也写好了 BgeHouduan（真实路径）：用 sentence-transformers 加载 BGE，
查询前加 "为这个句子生成表示以用于检索相关文章："，文档不加，向量 L2 归一化。
没装库时它会优雅报错并回退，不会让整个程序崩。
"""

import hashlib
import math
from collections import Counter

import numpy as np


class Zihouduan:
    """后备嵌入后端：字符 n-gram + TF-IDF + L2 归一化。"""

    mingzi = "zihouduan"
    moxing_id = "zihouduan-ngram-tfidf-v1"

    def __init__(self, weidu=20000):
        self.weidu = weidu
        self.idf = {}
        self.N = 0

    def shiying(self, wenben_liebiao):
        """在建立索引前，先用全部文档算一遍 IDF（逆文档频率）。"""
        df = {}
        for t in wenben_liebiao:
            for g in set(self._ti_qu_grams(t)):
                df[g] = df.get(g, 0) + 1
        self.N = len(wenben_liebiao) or 1
        # 平滑的 IDF：log((N+1)/(df+1)) + 1，避免除零也避免 idf 为负
        self.idf = {g: math.log((self.N + 1) / (c + 1)) + 1.0 for g, c in df.items()}

    def _ti_qu_grams(self, wenben):
        """抽字符 n-gram（1~3）。只保留中文、字母、数字，标点空格都丢，
        这样“开源许可证”和“许可证开源”会有不同表示，符合中文字面检索直觉。"""
        chars = [c for c in wenben if self._you_xiao(c)]
        grams = []
        n = len(chars)
        for i in range(n):
            for L in (1, 2, 3):
                if i + L <= n:
                    grams.append("".join(chars[i:i + L]))
        return grams

    @staticmethod
    def _you_xiao(c):
        if '一' <= c <= '鿿':
            return True
        return c.isalnum()

    def _vec(self, wenben):
        grams = self._ti_qu_grams(wenben)
        tf = Counter(grams)
        vec = np.zeros(self.weidu, dtype=np.float32)
        for g, c in tf.items():
            # 稳定哈希：用 md5 把 n-gram 映射到固定桶，避免不同进程哈希值不一致
            h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16) % self.weidu
            w = c * self.idf.get(g, 1.0)
            vec[h] += w
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec

    def bianma(self, wenben, shifou_chaxun=False):
        # 后备后端查询和文档用同一套表示（不像 BGE 那样给查询加前缀）
        return self._vec(wenben)


class BgeHouduan:
    """真实路径：BGE 语义向量。没装 sentence-transformers 时优雅报错。"""

    mingzi = "bge"
    moxing_id = "bge-small-zh-v1.5"

    def __init__(self, lujing=None):
        self.ke_yong = False
        self.cuowu = ""
        self._query_prefix = "为这个句子生成表示以用于检索相关文章："
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:  # 没装库就别崩，记下来
            self.cuowu = "未安装 sentence-transformers：%s" % e
            return
        self.ke_yong = True
        try:
            self.moxing = SentenceTransformer(lujing or "BAAI/bge-small-zh-v1.5")
        except Exception as e:
            self.ke_yong = False
            self.cuowu = "加载 BGE 模型失败：%s" % e

    def shiying(self, wenben_liebiao):
        # BGE 自带语料自适应，不必手动算 IDF
        pass

    def bianma(self, wenben, shifou_chaxun=False):
        if not self.ke_yong:
            raise RuntimeError("BGE 后端当前不可用：" + self.cuowu)
        t = wenben
        if shifou_chaxun:
            # 官方建议：检索查询前要加这段前缀，文档不加
            t = self._query_prefix + wenben
        v = self.moxing.encode([t], normalize_embeddings=True)[0]
        return np.asarray(v, dtype=np.float32)


def xuanze_houduan(peizhi):
    """按优先级选择后端：先试配置里的（默认 bge 会回退），不行就用后备 zihouduan。"""
    ming = getattr(peizhi, "houduan", "zihouduan")
    if ming == "bge":
        b = BgeHouduan(getattr(peizhi, "moxing_lujing", {}).get("bge"))
        if b.ke_yong:
            return b
        print("[提示] BGE 后端不可用，回退到后备嵌入（zihouduan）。原因：%s" % b.cuowu)
    return Zihouduan(getattr(peizhi, "zihouduan_weidu", 20000))


def huoq_houduan_mingzi(houduan):
    """暴露“当前用的是哪个后端”，方便界面/日志显示。"""
    return getattr(houduan, "mingzi", "unknown")
