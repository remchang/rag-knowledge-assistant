# NOTICE（第三方来源与许可证）

本项目本身以 MIT 许可证发布（版权人：王锐兵，软件2304，学号 23110506126）。
以下列出项目中**引用/依赖**的第三方组件及其许可证。本项目在本机**未实际安装**下列大模型相关库，
仅保留接口与说明；它们的许可证信息如下：

| 组件 | 用途 | 许可证 |
| --- | --- | --- |
| Transformers | 本地大模型加载与生成（真实路径，未装则回退） | Apache-2.0 |
| Sentence-Transformers | BGE 等句向量模型加载（真实路径，未装则回退） | Apache-2.0 |
| FAISS (faiss-cpu) | 向量索引加速（真实路径，未装则回退到 numpy） | MIT |
| Hugging Face Hub | 模型权重下载（脚本 `xiazai-moxing.ps1` 使用） | Apache-2.0 |
| Ollama | （可选）本地模型服务替代方案，本项目未使用 | MIT |
| pypdf | PDF 文本抽取（实际安装并使用） | BSD-3-Clause |
| numpy | 数值计算 / 后备嵌入（实际安装并使用） | BSD-3-Clause |
| pytest | 单元测试（实际安装并使用） | MIT |
| Streamlit | Web 界面（可选，需自己安装） | Apache-2.0 |

## 模型权重许可证（单独说明）

模型权重许可证与代码许可证不同，请以上述 `model_list.md` 中“许可证”列为准：
- `BAAI/bge-small-zh-v1.5`：MIT
- `Qwen/Qwen2.5-1.5B-Instruct`：Apache-2.0
- `Qwen/Qwen2.5-0.5B-Instruct`：Apache-2.0

## 课程语料许可证

`data/` 下文档均为作者本人原创，采用 **CC BY 4.0** 发布（见 `data/README.md`）。
