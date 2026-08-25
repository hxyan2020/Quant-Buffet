"""Check EN non-ascii and EN/ZH overlap."""
from __future__ import annotations

import re
import sqlite3

con = sqlite3.connect("prisma/dev.db")
con.row_factory = sqlite3.Row

non = con.execute(
    """
    SELECT slug, title, hasPythonCode, length(pythonCodeHtml) n
    FROM Strategy WHERE locale='en' AND published=1
    """
).fetchall()
non = [r for r in non if not re.fullmatch(r"[a-z0-9\-]+", r["slug"] or "")]
print("nonascii sample:")
for r in non[:15]:
    print(repr(r["slug"][:40]), "|", (r["title"] or "")[:40], "code", bool(r["n"] and r["n"] > 50))

en_slugs = {
    r["slug"]
    for r in con.execute("SELECT slug FROM Strategy WHERE locale='en' AND published=1")
}
zh_slugs = {
    r["slug"]
    for r in con.execute("SELECT slug FROM Strategy WHERE locale='zh' AND published=1")
}
print("zh only", len(zh_slugs - en_slugs))
print("en only", len(en_slugs - zh_slugs))
print("overlap", len(en_slugs & zh_slugs))
print("zh-only samples", list(zh_slugs - en_slugs)[:10])
