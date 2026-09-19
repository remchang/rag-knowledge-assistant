# 模型清单（model_list.md）

> 本机未实际下载这些模型（硬约束：不装 torch / transformers 等大模型依赖）。
> 因此下方 **SHA256 均为“待下载后填写”**，绝不编造。下载脚本见 `scripts/xiazai-moxing.ps1`，
> 固定 revision 以保证可复现。

## 嵌入模型

| 名称 | 仓库 ID | Revision | 许可证 | 大小 | 来源 | SHA256 |
| --- | --- | --- | --- | --- | --- | --- |
| BGE small zh v1.5 | `BAAI/bge-small-zh-v1.5` | `7999e1d3359715c523056ef9478215996d62a620` | MIT | 约 130 MB（fp32） | Hugging Face Hub | 待下载后填写 |

说明：官方建议检索查询前加前缀 `为这个句子生成表示以用于检索相关文章：`，文档不加；
向量需 L2 归一化。`src/xiangliang.py` 的 `BgeHouduan` 已实现该逻辑（本机因未装库而回退）。

## 生成模型（本地推理）

| 名称 | 仓库 ID | Revision | 许可证 | 大小 | 来源 | SHA256 |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen2.5-1.5B-Instruct | `Qwen/Qwen2.5-1.5B-Instruct` | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` | Apache-2.0 | 约 3 GB | Hugging Face Hub | 待下载后填写 |
| Qwen2.5-0.5B-Instruct | `Qwen/Qwen2.5-0.5B-Instruct` | `7ae557604adf67be50417f59c2c2f167def9a775` | Apache-2.0 | 约 1 GB | Hugging Face Hub | 待下载后填写 |

说明：本地生成用 `transformers` 加载，CPU / float32，`apply_chat_template(add_generation_prompt=True)`，
`max_new_tokens=128`，`do_sample=False`，只解码新 token。`src/shengcheng.py` 的 `BendiMoxing` 已实现
（本机因未装库而回退到证据降级模式）。

## 第三方库许可证（另行列出）

- Transformers / Sentence-Transformers / FAISS / Hugging Face Hub：均为 Apache-2.0 或 MIT。
- 模型**权重**许可证单独以上表“许可证”列为准（与代码库许可证不同）。
- 详见 `NOTICE.md`。
