# Email Digest Skill

A Claude Code skill that parses raw email content (MIME/headers/body/attachments), organizes it into structured Markdown and Word files, generates summaries, and translates English emails to Chinese.

## Features

- Parse standard MIME `.eml` files and non-standard email formats (forwarded, copy-pasted)
- Generate three-part structured documents:
  - **Part 1**: Complete original content (verbatim, with content-type attachments inlined)
  - **Part 2**: Structured summary
  - **Part 3**: Chinese translation (for English emails)
- Output both Markdown (`.md`) and Word (`.docx`) files
- Automatic folder organization by date and subject (`YYYYMMDD_Topic`)
- Smart attachment handling: content-type attachments inlined at correct position, standalone attachments listed separately

## Trigger Phrases

`/email-digest`, `解析邮件`, `邮件整理`, `邮件摘要`, `parse email`, `email digest`, `整理邮件`

## Directory Structure

```
D:/pythonPycharms/工具开发/057邮件处理/
├── input/
│   └── 20260314_Q1_Review/
│       └── raw.eml
└── output/
    └── 20260314_Q1_Review/
        ├── Q1_Review.md
        ├── Q1_Review.docx
        └── data.json
```

## Scripts

- `scripts/parse_email.py` — Parse standard MIME `.eml` files, output structured JSON
- `scripts/generate_docx.py` — Convert Markdown files to styled Word documents

## Dependencies

```bash
pip install python-docx
```

## Installation

```bash
npx skills add 24kchengYe/email-digest
```

---

![Visitors](https://visitor-badge.laobi.icu/badge?page_id=24kchengYe.email-digest)

[![Star History Chart](https://api.star-history.com/svg?repos=24kchengYe/email-digest&type=Date)](https://star-history.com/#24kchengYe/email-digest&Date)