# 测试记录（docs/ceshi-jilu.md）

本文件记录**真实执行**的命令与输出，未编造。环境：Windows 11 / Python 3.13.12 /
numpy 2.5.3 / pypdf 6.19.0 / pytest 9.1.1。

---

## 1. 单元测试命令

```powershell
.\scripts\ceshi.ps1
# 等价于：.\.venv\Scripts\python.exe -m pytest -q
```

### 真实输出（最终，全部通过）
```
.....................
21 passed in 6.03s
```

### 测试分布（满足硬要求）
- 解析测试 6：`test_jiexi.py`（TXT / MD / PDF / 空页 / 重复 SHA256 去重 / 编码 GBK+BOM）
- 索引测试 5：`test_suoyin.py`（向量数一致 / 保存加载 / 模型 ID 校验 / 块数不一致报错 / add+search）
- 检索评价：跑 20 题，断言 Recall@5 ≥ 0.8（实际 1.0）
- 证据审查 10 题：`test_zhengju.py` 校验 `renshen_shencha.json` 结构 + 引用校验函数
- 安全/资源 4：`test_anquan.py`（提示注入 / 超长文档 / 空文档 / 离线可用）

---

## 2. 失败用例与修复过程（真实发生过）

第一次运行：`2 failed, 19 passed`。

### 失败 1：`test_jiexi_kongye` —— UnicodeEncodeError
- 原因：PDF 测试夹具用中文文本，但生成 PDF 的内容流按 `latin-1` 编码，中文无法编码。
- 修复：测试夹具改用 ASCII 文本（`["First page has text"], [""]`），断言仍检查“第 2 页为空页”。
- 反思：PDF 内容流（Helvetica 基础 14 字体）只支持 ASCII；中文 PDF 需嵌入字体（本机未做）。

### 失败 2：`test_pingce_xieru_wenjian` —— TypeError
- 原因：`zhuc_jiank_pingce()` 没有 `renshen_lujing` 形参，测试传了它。
- 修复：在 `src/pingce.py` 给函数增加 `renshen_lujing=None` 形参并在内部使用。

修复后重跑：`21 passed in 6.03s`。

---

## 3. 评测运行与真实数字

```powershell
.\scripts\jianku.ps1
.\scripts\pingce.ps1
```

### 真实输出（jianku）
```
建索引完成：7 个块，后端=zihouduan
```

### 真实输出（pingce）
```
[提示] 用后备索引 NumpySuoyin：未安装 faiss-cpu，无法使用 FaissSuoyin：No module named 'faiss'
Recall@1=0.9792 Recall@3=1.0000 Recall@5=1.0000 误命中率=0.0000 平均延迟=0.000360s
```

结果已写入 `pingce/jieguo.json`；`pingce/renshen_shencha.json` 含 10 条人工证据审查。

> 诚实提醒：Recall 高源于评测集与语料均为本人撰写、字面重合度高；不代表真实语义泛化。
> 本机未装 BGE / Qwen，未实测真实模型路径。
