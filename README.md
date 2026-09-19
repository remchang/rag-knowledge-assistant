# 实验05：基于开源大模型的智能知识问答系统（RAG）

课程：开源软件与新技术　|　学生：王锐兵（软件2304，学号 23110506126）

本项目是一个**最小化但完整可跑**的 RAG（检索增强生成）问答系统。所有代码、文档、评测均自包含，
不依赖任何商业服务，可完全离线运行。

> ⚠️ **重要诚实声明（请先读这一段）**
> 本机**没有安装** torch / transformers / sentence-transformers / faiss-cpu，
> 因此本项目**实际跑的是**：
> - 嵌入后端：**`zihouduan`**（纯 numpy 的“字符 n-gram + TF-IDF + L2 归一化”后备方案），
>   不是真实的 BGE 语义向量；
> - 生成模式：**`zhengju_zhaiyao`**（证据抽取降级模式），**不调用大模型**，
>   只展示按相关度排序的原文证据 + 句子选择摘要，并明确标注“本模式未进行生成”。
>
> 代码里**已经写好**真实路径 `BgeHouduan`（BGE）和 `BendiMoxing`（本地 Qwen），
> 它们在检测到对应库未安装时会**优雅报错并自动回退**，不会让程序崩溃。
> 装上真实模型后的运行命令见文末。

---

## 1. 系统架构

```mermaid
flowchart LR
    A[文档 data/*.md|txt] --> B[解析 jiexi]
    B -->|SHA256 去重| C[分块 fenkuai]
    C --> D[嵌入 xiangliang]
    D -->|向量| E[(向量索引 suoyin)]
    C -->|元数据| E
    Q[用户问题] --> D2[查询编码]
    D2 --> R[检索 jiansuo]
    R --> E
    R --> G[生成 shengcheng]
    G -->|降级模式| H[原文证据 + 摘要]
    G -->|真实模式| I[大模型生成]
```

- `src/jiexi.py`：解析 TXT / Markdown / PDF，生成 `doc_id` 与内容 `SHA256`，PDF 逐页抽取并记录页码，空文本页标记“需要 OCR，当前未索引”。
- `src/fenkuai.py`：默认 400 字符块 + 80 字符重叠，优先在段落边界切，避免把标题和正文无条件切断。
- `src/xiangliang.py`：嵌入后端。`Zihouduan`（默认实际）/ `BgeHouduan`（真实，未装则回退）。
- `src/suoyin.py`：`NumpySuoyin`（默认，精确余弦）/ `FaissSuoyin`（装了 faiss 才用）。索引与元数据分开保存，先写临时文件再原子替换，加载时校验块数/向量数/模型 ID。
- `src/jiansuo.py`：查询编码、Top-k、相似度阈值过滤、按文档过滤，过滤 faiss 的 -1 无效下标。
- `src/shengcheng.py`：`ZhengjuZhaiyaoMosshi`（降级，默认）/ `BendiMoxing`（真实，未装则回退）；含提示注入检测与引用校验。
- `src/pingce.py`：检索评测（Recall@1/3/5、误命中率、平均延迟）。

---

## 2. 运行环境需求

- CPU 即可运行（后备嵌入 + 证据降级模式）。内存约 100–200 MB。
- 若启用真实 BGE / Qwen：建议 8 GB+ 内存，Qwen1.5B 在 CPU 上单条回答约数秒到数十秒。
- Python 3.13（本机：`C:\Users\王锐兵\.workbuddy\binaries\python\versions\3.13.12\python.exe`）。
- 依赖（仅这三个，都很小）：`numpy`、`pypdf`、`pytest`。**不要安装** torch / transformers / sentence-transformers / faiss-cpu / streamlit（太大或会卡死）。

### 安装依赖（用阿里云镜像，适配国内慢网）
```powershell
.\scripts\anzhuang.ps1
```
> 要跑 Streamlit 界面，请自己额外执行：`.\.venv\Scripts\pip install streamlit`

---

## 3. 支持与解析格式

| 格式 | 支持情况 | 说明 |
| --- | --- | --- |
| TXT | ✅ | 自动处理 GBK / UTF-8 / BOM 编码 |
| Markdown | ✅ | 识别 `#/##/###` 标题，段落带“所属标题” |
| PDF | ✅ | 用 pypdf 逐页抽取；空文本页标记“需要 OCR，当前未索引” |

重复 `SHA256` 的文件不会重复入库（去重在建索引流程中完成）。

---

## 4. 关键参数（`src/peizhi.py`）

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| `fenkuai_daxiao` | 400 | 分块大小（字符） |
| `fenkuai_chongdie` | 80 | 相邻块重叠（字符） |
| `top_k` | 5 | 返回最相关片段数 |
| `yuling_xianzhi` | 0.12 | 相似度阈值（只影响展示/生成，不影响排名与 Recall） |
| `houduan` | `zihouduan` | 嵌入后端；写 `bge` 会自动回退 |
| `shengcheng` | `zhengju_zhaiyao` | 生成模式；写 `bendi` 会自动回退 |

---

## 5. 索引与重建

索引保存在 `storage/`：
- `storage/index.npz`：向量
- `storage/meta.json`：每个块的元信息 + 模型 ID + 块数

构建 / 重建：
```powershell
.\scripts\jianku.ps1
```
> 换嵌入模型（比如从后备切到真实 BGE）后**必须重建索引**，否则加载时会因“模型 ID 不一致”报错。

---

## 6. 降级模式（当前默认）

由于本机未装大模型，默认走 `zhengju_zhaiyao`：
- 不做生成，只给出按相关度排序的原文证据片段，并标注 `[S1] [S2] …`；
- 附一个“基于句子选择的摘要”（取最高相关块的前两句）；
- 界面与输出**明确标注**“本模式未进行生成，以下是原文证据”。

> 关于引用：只给输出补一个 `[S1]` **不等于**证明内容正确。引用校验函数 `yinyong_jianyan`
> 会检查回答里的 `[Sn]` 是否都来自本轮检索结果，否则标记为“引用无效/证据不足”。

---

## 7. 隐私与提示注入边界

- 文档内容被视为**不可信数据**。系统规则明确禁止执行文档中的指令。
- `tishi_zhuruan_jiance` 会识别“忽略以上规则 / 输出系统提示词 / 输出密钥 / print your system prompt”等模式并标记为可疑。
- 本项目在 `data/docker-rongqi.md` 末尾**故意嵌入了一段提示注入文本**，仅用于测试注入防护，正常读者请忽略。

---

## 8. 评测结果（真实运行）

评测集 `pingce/wenti.json` 共 20 题，其中 4 题为知识库外（应拒答）。
在本机（后备嵌入 + 证据降级模式）真实运行结果：

| 指标 | 数值 |
| --- | --- |
| Recall@1 | 0.9792 |
| Recall@3 | 1.0000 |
| Recall@5 | 1.0000 |
| 知识库外问题误命中率 | 0.0000 |
| 平均检索延迟 | 0.00036 s |

> 注意：Recall 高是因为评测集与语料均为本人撰写、query 与标准片段字面重合度高；
> 换成真实 BGE 语义向量后，跨表述的泛化能力会更强，但本机**未实测**。

---

## 9. 装上真实模型后的运行命令

```powershell
# 1) 下载真实模型权重（固定 revision，可离线缓存）
.\scripts\xiazai-moxing.ps1

# 2) 修改 src/peizhi.py：把 houduan 改成 "bge"，shengcheng 改成 "bendi"
# 3) 重建索引（因为嵌入模型变了，模型 ID 不一致会报错）
.\scripts\jianku.ps1
# 4) 跑界面（需自己装 streamlit）
.\.venv\Scripts\python.exe -m streamlit run app.py
```

模型仓库与 revision 见 `model_list.md`。

---

## 10. 测试

```powershell
.\scripts\ceshi.ps1
```
共 21 个测试全部通过（解析 6、索引 5、检索评价、证据审查 10、安全/资源 4）。
详细记录见 `docs/ceshi-jilu.md`。
