#!/usr/bin/env python3
"""md_to_email_html.py - turn a report summary (sections 1-3) into email-ready HTML.

The weekly report is markdown tables. Sending it as plain text destroys the tables and
the clickable founder LinkedIn links, which are the whole point of the email. This emits
compact inline-styled HTML that renders in Gmail, Superhuman and Outlook.

Usage:
  python3 scripts/md_to_email_html.py state/reports/<date>.summary.md > /tmp/email.html
  python3 scripts/md_to_email_html.py <file> --title "YC Nexus Scout - 2026-09-28"

Stdlib only. Handles: # / ## headings, pipe tables, **bold**, *italic*, `code`,
[text](url) links, <br> passthrough, and bare paragraphs. Anything else is escaped.
"""
import argparse
import html
import re
import sys

LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
CODE = re.compile(r"`([^`]+)`")

# Attribute-based table styling instead of per-cell inline CSS: roughly a third of the
# bytes and better supported by Gmail/Outlook, which strip <style> blocks.
TD = "vertical-align:top"
TH = "text-align:left;background:#f4f4f5"


def inline(text):
    """Escape, then re-apply the small set of markdown we support."""
    # Protect <br> before escaping, since report cells use it to stack founders.
    text = text.replace("<br>", "\x00BR\x00")
    out = html.escape(text, quote=False)
    out = LINK.sub(lambda m: '<a href="%s" style="color:#1a56db;text-decoration:none">%s</a>'
                   % (html.escape(m.group(2), quote=True), m.group(1)), out)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    out = ITALIC.sub(r"<em>\1</em>", out)
    out = CODE.sub(r'<code style="background:#f4f4f5;padding:1px 4px;border-radius:3px">\1</code>', out)
    return out.replace("\x00BR\x00", "<br>")


def split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def is_divider(line):
    return bool(re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", line)) and "-" in line


def convert(md):
    lines = md.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Table: a pipe row followed by a divider row.
        if stripped.startswith("|") and i + 1 < len(lines) and is_divider(lines[i + 1]):
            header = split_row(stripped)
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(split_row(lines[i].strip()))
                i += 1
            out.append('<table border="1" cellspacing="0" cellpadding="6" '
                       'style="border-collapse:collapse;font-size:12px;line-height:1.45;'
                       'border-color:#d8d8d8;margin:10px 0 18px">')
            out.append("<tr>" + "".join('<th style="%s">%s</th>' % (TH, inline(c)) for c in header) + "</tr>")
            for row in body:
                row += [""] * (len(header) - len(row))
                out.append("<tr>" + "".join('<td style="%s">%s</td>' % (TD, inline(c)) for c in row[:len(header)]) + "</tr>")
            out.append("</table>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            lvl = len(m.group(1))
            size = {1: 19, 2: 15, 3: 13, 4: 12}[lvl]
            top = 4 if lvl == 1 else 20
            out.append('<h%d style="font-size:%dpx;margin:%dpx 0 6px;font-weight:600">%s</h%d>'
                       % (min(lvl, 4), size, top, inline(m.group(2)), min(lvl, 4)))
            i += 1
            continue

        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append('<ul style="margin:6px 0 12px;padding-left:20px;font-size:13px;line-height:1.5">'
                       + "".join("<li>%s</li>" % inline(x) for x in items) + "</ul>")
            continue

        # Paragraph: gather until a blank line or a structural line.
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("|", "#", "- ")):
            para.append(lines[i].strip())
            i += 1
        out.append('<p style="margin:6px 0 12px;font-size:13px;line-height:1.55">%s</p>'
                   % inline(" ".join(para)))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="markdown file, e.g. state/reports/<date>.summary.md")
    ap.add_argument("--title", default=None, help="optional <title>/preheader text")
    a = ap.parse_args()
    md = open(a.file, encoding="utf-8").read() if a.file != "-" else sys.stdin.read()
    body = convert(md)
    shell = (
        '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif;'
        'color:#18181b;max-width:1100px">'
        + (('<div style="display:none;max-height:0;overflow:hidden">%s</div>' % html.escape(a.title))
           if a.title else "")
        + body
        + '<p style="margin:20px 0 0;font-size:11px;color:#71717a;line-height:1.5">'
          'Generated by the yc-nexus-scout cloud routine. Full report with per-company evidence, '
          'appendices and run log is in the yc-tracking repository. Any outreach drafts in the full '
          'report are for you to send by hand; the routine never contacts founders.</p>'
        + "</div>"
    )
    sys.stdout.write(shell)


if __name__ == "__main__":
    main()
