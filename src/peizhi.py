# -*- coding: utf-8 -*-
"""实验05 的全局配置模块。

这里把所有“会经常改来改去”的参数集中放一起，免得改个分块大小还要满项目找。
代码里一律用拼音命名（fenkuai_daxiao = 分块大小），注释用中文，像普通本科生写的那样。

说明：本机没有装 torch / transformers / sentence-transformers / faiss-cpu，
所以默认后端是“zihouduan”（纯 numpy 的字符 n-gram + TF-IDF 后备嵌入），
生成端默认是“zhengju_zhaiyao”（证据抽取降级模式，不调用大模型）。
等以后装了真实模型，把 houduan / shengcheng 改成对应值即可（见 README）。
"""

import os


# ---- 分块相关 ----
# 默认一块 400 个中文字符，重叠 80 个字符。
# 为什么是 400：太小会切断语义，太大检索不精准；400 对中文教材段落比较合适。
FENKUAI_DAXIAO = 400
FENKUAI_CHONGDIE = 80

# ---- 检索相关 ----
# 默认返回前 5 个最相关片段。
TOP_K = 5
# 相似度阈值：低于这个数的片段不展示、不参与生成。
# 注意：这个阈值只影响“展示/生成”，不影响评测里的 Recall@k（评测看 top-k 排名）。
YULING_XIANZHI = 0.12

# ---- 嵌入后端选择 ----
# "bge" 想用真实 BGE 模型；"zihouduan" 是后备方案。
# 本机没装 sentence-transformers，所以写 "bge" 也会自动回退到 zihouduan。
HOUDUAN = "zihouduan"

# ---- 生成后端选择 ----
# "bendi" 想用本地 Qwen 模型；"zhengju_zhaiyao" 是降级模式（只给证据不给生成）。
SHENGCHENG = "zhengju_zhaiyao"

# ---- 模型和缓存路径 ----
# 真实模型权重默认缓存到项目下的 storage/moxing 目录（离线可用）。
MOXING_LUJING = {
    "bge": "BAAI/bge-small-zh-v1.5",
    "qwen_1_5b": "Qwen/Qwen2.5-1.5B-Instruct",
    "qwen_0_5b": "Qwen/Qwen2.5-0.5B-Instruct",
}

# 后备嵌入后端用的哈希维度（字符 n-gram 哈希到这个桶数）。
# 选 20000 是为了在内存和区分度之间折中；太大占内存，太小容易哈希冲突。
ZIHOUDUAN_WEIDU = 20000

# ---- 存储路径 ----
# 索引与元数据分开保存：storage/index.* 和 storage/meta.json
CUNCHU_MULU = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
SUOYIN_LUJING = os.path.join(CUNCHU_MULU, "index.npz")
META_LUJING = os.path.join(CUNCHU_MULU, "meta.json")

# 数据目录（放课程文档）和评测集目录
SHUJU_MULU = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PINGCE_MULU = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pingce")


class Peizhi:
    """把上面的配置打包成一个对象，方便在模块之间传递。"""

    def __init__(self, qijian=None):
        # qijian 是一个可选字典，用来在测试或脚本里临时覆盖某些参数
        self.fenkuai_daxiao = FENKUAI_DAXIAO
        self.fenkuai_chongdie = FENKUAI_CHONGDIE
        self.top_k = TOP_K
        self.yuling_xianzhi = YULING_XIANZHI
        self.houduan = HOUDUAN
        self.shengcheng = SHENGCHENG
        self.moxing_lujing = dict(MOXING_LUJING)
        self.zihouduan_weidu = ZIHOUDUAN_WEIDU
        self.cunchu_mulu = CUNCHU_MULU
        self.suoyin_lujing = SUOYIN_LUJING
        self.meta_lujing = META_LUJING
        self.shuju_mulu = SHUJU_MULU
        self.pingce_mulu = PINGCE_MULU
        if qijian:
            for k, v in qijian.items():
                if hasattr(self, k):
                    setattr(self, k, v)

    def __repr__(self):
        return ("Peizhi(fenkuai_daxiao=%d, fenkuai_chongdie=%d, top_k=%d, "
                "yuling_xianzhi=%.3f, houduan=%s, shengcheng=%s)" % (
                    self.fenkuai_daxiao, self.fenkuai_chongdie, self.top_k,
                    self.yuling_xianzhi, self.houduan, self.shengcheng))


def huoq_peizhi(qijian=None):
    """拿到一份默认配置。测试里可以传 qijian 覆盖个别参数。"""
    return Peizhi(qijian)
