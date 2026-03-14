---
name: email-digest
description: "Parse raw email content (MIME/headers/body/attachments), organize into Markdown and Word files, generate summary, and translate English emails to Chinese. Trigger: /email-digest, 解析邮件, 邮件整理, 邮件摘要, parse email, email digest, 整理邮件"
---

# Email Digest Skill

将原始邮件内容解析、整理为结构化的 Markdown 和 Word 文件，并生成概要。英文邮件自动提供中文翻译。

## Workflow

### Step 1: Receive Email Content

When the user pastes raw email content or provides an `.eml` file path:

**Base directory**: `D:/pythonPycharms/工具开发/057邮件处理/`

**命名规则**：每封邮件使用 `YYYYMMDD_主题关键词` 格式创建对应的子文件夹，input 和 output 一一对应。例如：

```
D:/pythonPycharms/工具开发/057邮件处理/
├── input/
│   ├── 20260314_Q1_Review/          ← 第一封邮件原始文件
│   │   └── raw.eml
│   └── 20260315_Conference_Invite/  ← 第二封邮件原始文件
│       └── raw.eml
└── output/
    ├── 20260314_Q1_Review/          ← 第一封邮件输出
    │   ├── Q1_Review.md
    │   ├── Q1_Review.docx
    │   └── data.json
    └── 20260315_Conference_Invite/  ← 第二封邮件输出
        ├── Conference_Invite.md
        ├── Conference_Invite.docx
        └── data.json
```

**步骤**：
1. 从邮件内容中提取日期和主题，生成子文件夹名 `YYYYMMDD_主题关键词`（主题取前30字符，特殊字符替换为下划线）
2. 创建 `input/{folder_name}/` 和 `output/{folder_name}/`
3. 如果用户粘贴了原始文本，保存为 `input/{folder_name}/raw.eml`
4. 如果用户提供了文件路径，直接使用
5. 如果用户已将文件放在 `input/` 目录下（未分子文件夹），先创建子文件夹再移入；同目录下的附件文件（PDF 等）一并移入

### Step 2: Parse Email

根据输入内容的格式，选择不同的解析方式：

**情况 A：标准 MIME 格式（.eml 文件）**

如果文件包含标准 MIME 头（`From:`, `To:`, `Content-Type:`, `MIME-Version:` 等），使用解析脚本：

```bash
python "C:/Users/ASUS/.claude/skills/email-digest/scripts/parse_email.py" "{eml_file_path}"
```

This outputs structured JSON to stdout with: from, to, cc, date, subject, body, attachments list, and language detection.

**情况 B：非标准格式（纯文本、转发邮件、复制粘贴内容）**

常见场景：
- 从邮件客户端复制粘贴的转发邮件（含"以下是转发的邮件"、"---------- Forwarded message ----------"等标记）
- 纯文本形式的邮件内容（含中文/英文头部字段如"发件人:"/"From:"）
- 用户直接粘贴到对话中的邮件文本
- `.txt` 文件而非 `.eml` 文件

此时 **不使用** `parse_email.py`，而是由 Claude 直接阅读文本内容，手动提取：
- 发件人、收件人、抄送、日期、主题等字段
- 正文内容
- 如有转发人备注，单独提取
- 如有附件（同目录下的 PDF 等文件），一并读取处理

同样保存为 `input/{folder_name}/raw.eml`（即使不是标准 MIME 格式，也统一用此文件名归档原始内容）。

### Step 3: Generate Markdown File

输出的 Markdown 文件采用**三段式结构**：先给完整原文（一字不漏），再给概要整理，最后给翻译。

```markdown
# {Subject}

## 邮件信息

| 字段 | 内容 |
|------|------|
| **发件人** / **转发人** | {from_name} <{from_email}> |
| **收件人** | {to_list} |
| **抄送** | {cc_list} |
| **日期** | {date_formatted} |
| **主题** | {subject} |
| ... | （根据邮件类型补充字段，如论文标题、决定结果等） |

## 附件列表

| 文件名 | 类型 | 大小 | 说明 |
|--------|------|------|------|
| {filename} | {type} | {size} | {brief description} |

---

# Part 1: 完整原文

> **原则：完整保留邮件中的所有内容，一字不删。** 包括：
> - 转发人备注（如有）
> - 编辑/发件人正文
> - 所有审稿人/回复人的意见原文
> - 附件的完整文本内容（读取后嵌入）
> - 签名、免责声明等
>
> **附件处理规则：** 附件分两种情况，需根据内容性质区分处理：
> - **内容型附件**（属于正文的一部分）：如审稿人意见 PDF、回复函 PDF 等——读取后**嵌入到正文对应位置**，而非单独放在末尾。例如邮件正文中 Reviewer #2 写"See attached"，则将 PDF 全文插入到 Reviewer #2 意见的位置。
> - **独立型附件**（与正文平行的文件）：如合同、报告、数据文件等——在正文之后单独列出附件原文章节。

## 转发人备注
{forwarding notes, if any}

## 正文原文
{complete original body text, with 内容型附件 inlined at the correct position}

## 独立附件原文（如有）
{complete text content of standalone attachments, read via PDF/Read tool}

---

# Part 2: 概要整理

> **在完整原文之后**，对邮件内容进行结构化概要。
> 如果邮件包含多方意见（如审稿意见），用表格汇总立场，再逐一概要。

## 各方立场总览（如适用）

| 角色 | 立场 | 核心态度 |
|------|------|----------|
| ... | ... | ... |

## 综合概要

{Claude 生成 2-6 句概要，涵盖核心信息、关键要点、行动项}

---

# Part 3: 中文翻译

> 仅在邮件正文为英文时生成此部分。
> 翻译范围：编辑信/正文 + 所有审稿人/附件意见 + 概要。

## 正文翻译
{complete translation of the body}

## 附件内容翻译（如有）
{complete translation of attachment content}
```

Save to: `output/{folder_name}/{sanitized_subject}.md`

### Step 4: Generate Word Document

`generate_docx.py` 直接将 Markdown 文件转换为 Word 文档（支持标题、表格、加粗/斜体、列表、引用、分页等）。

**先生成 Markdown（Step 3），再一行命令出 Word：**

```bash
python "C:/Users/ASUS/.claude/skills/email-digest/scripts/generate_docx.py" "{md_file_path}" "{docx_output_path}"
```

例如：
```bash
python "C:/Users/ASUS/.claude/skills/email-digest/scripts/generate_docx.py" "D:/pythonPycharms/工具开发/057邮件处理/output/20260314_NatureCities_Decision/NatureCities_Decision.md" "D:/pythonPycharms/工具开发/057邮件处理/output/20260314_NatureCities_Decision/NatureCities_Decision.docx"
```

Save to: `output/{folder_name}/{sanitized_subject}.docx`

### Step 5: Report Results

Tell the user:
- Markdown file path
- Word file path
- Display the summary (and Chinese translation if applicable) directly in the conversation

## Important Notes

- **完整性第一**：Part 1 完整原文必须一字不漏地保留邮件中所有内容。附件不能只写"见附件"——内容型附件（如审稿人意见 PDF）嵌入到正文对应位置，独立型附件单独列出全文。
- **Language detection**: The parser outputs `is_english` field. If true, always include Chinese translation (Part 3).
- **Summary**: Claude should write the summary, not the script. Read the parsed body content and generate a concise summary.
- **Translation**: Claude should translate, not the script. Translate the body, attachments, and summary to Chinese.
- **Filename sanitization**: Replace special characters with underscores, limit to 50 chars.
- **Encoding**: Handle various email encodings (UTF-8, GBK, ISO-8859-1, Base64, Quoted-Printable).
- **Dependencies**: Run `pip install python-docx` if not already installed.
- **Word 文件**：Word 文件的内容应与 Markdown 保持一致（三段式结构），通过将完整数据写入 data.json 后调用 generate_docx.py 生成。如果内容过于复杂（如包含大量审稿意见原文），可直接将 Markdown 内容作为 Word 正文的数据源。
