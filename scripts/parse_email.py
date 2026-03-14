#!/usr/bin/env python3
"""Parse raw email (.eml) file and output structured JSON."""

import email
import email.policy
import email.header
import email.utils
import html.parser
import json
import re
import sys
from pathlib import Path


class HTMLTextExtractor(html.parser.HTMLParser):
    """Extract readable text from HTML, stripping tags."""

    def __init__(self):
        super().__init__()
        self._pieces = []
        self._skip = False
        self._skip_tags = {"style", "script", "head"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True
        if tag in ("br", "p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._pieces.append("\n")

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False
        if tag in ("p", "div", "tr", "table", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._pieces.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self._pieces.append(data)

    def get_text(self):
        text = "".join(self._pieces)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_text(html_content):
    """Convert HTML to plain text."""
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html_content)
        return extractor.get_text()
    except Exception:
        # Fallback: regex strip
        text = re.sub(r"<[^>]+>", "", html_content)
        return text.strip()


def decode_header_value(value):
    """Decode RFC 2047 encoded header values."""
    if not value:
        return ""
    decoded_parts = email.header.decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)


def parse_address(addr_str):
    """Parse an email address string into {name, email}."""
    if not addr_str:
        return []
    addresses = email.utils.getaddresses([addr_str])
    result = []
    for name, addr in addresses:
        result.append({
            "name": decode_header_value(name) if name else "",
            "email": addr,
        })
    return result


def format_size(size_bytes):
    """Format byte size to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def detect_english(text):
    """Simple heuristic: if >60% of alpha chars are ASCII letters, likely English."""
    if not text:
        return False
    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return False
    ascii_alpha = sum(1 for c in alpha_chars if ord(c) < 128)
    ratio = ascii_alpha / len(alpha_chars)
    return ratio > 0.6


def parse_email_file(file_path):
    """Parse an .eml file and return structured data."""
    path = Path(file_path)
    raw = path.read_bytes()

    msg = email.message_from_bytes(raw, policy=email.policy.default)

    # Extract headers
    subject = decode_header_value(msg.get("Subject", ""))
    from_list = parse_address(msg.get("From", ""))
    to_list = parse_address(msg.get("To", ""))
    cc_list = parse_address(msg.get("Cc", ""))
    date_str = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")

    # Parse date
    date_tuple = email.utils.parsedate_tz(date_str)
    date_formatted = date_str
    if date_tuple:
        import datetime
        ts = email.utils.mktime_tz(date_tuple)
        dt = datetime.datetime.fromtimestamp(ts)
        date_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")

    # Extract body and attachments
    body_text = ""
    body_html = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                # Attachment
                filename = part.get_filename()
                if filename:
                    filename = decode_header_value(filename)
                else:
                    filename = "unnamed"
                payload = part.get_payload(decode=True)
                size = len(payload) if payload else 0
                attachments.append({
                    "filename": filename,
                    "content_type": content_type,
                    "size_bytes": size,
                    "size_human": format_size(size),
                })
            elif content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body_text += payload.decode(charset, errors="replace")
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body_html += payload.decode(charset, errors="replace")
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if content_type == "text/html":
                body_html = decoded
            else:
                body_text = decoded

    # If no plain text but HTML exists, extract text from HTML
    body_clean = body_text
    if not body_text.strip() and body_html:
        body_clean = html_to_text(body_html)

    is_english = detect_english(body_clean)

    result = {
        "subject": subject,
        "from": from_list[0] if from_list else {"name": "", "email": ""},
        "to": to_list,
        "cc": cc_list,
        "date": date_str,
        "date_formatted": date_formatted,
        "message_id": message_id,
        "body_text": body_text,
        "body_html": body_html,
        "body_clean": body_clean,
        "attachments": attachments,
        "is_english": is_english,
    }

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: parse_email.py <eml_file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = parse_email_file(file_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
