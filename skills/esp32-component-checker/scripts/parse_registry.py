#!/usr/bin/env python3
"""
ESP Component Registry Parser
Поиск компонентов через components.espressif.com API.
Вывод в красивых ASCII-боксах, HTML или JSON.

Использование:
  esp-checker search --target esp32s3 --limit 5
  esp-checker info espressif/ssd1306
  esp-checker check lvgl/lvgl --board heltec-v4
  esp-checker search --target esp32s3 --query sensor --format html
"""
import urllib.request, urllib.parse, json, sys, os

API_BASE = "https://components.espressif.com/api"

# ─── Box drawing ────────────────────────────────────────────────

def wline(w, text=""):
    """Строка внутри бокса: |текст| с заполнением пробелами до w-2."""
    return "│" + str(text).ljust(w-2) + "│"

def box_component(c, w=58):
    ns = c.get("namespace","")
    nm = c.get("name","?")
    ver = c.get("version","")
    dl = c.get("downloads",0)
    targets = c.get("targets",[])
    lic = c.get("license","?")
    desc = c.get("description","")
    feat = c.get("featured",False)
    full = f"{ns}/{nm}" if ns else nm
    lname = lic.get("name",str(lic)) if isinstance(lic,dict) else str(lic) if lic else "?"
    s = "★ FEATURED" if feat else "COMPONENT"
    lines = ["┌"+"─"*(w-2)+"┐",
             "│"+f" {s} ".center(w-2,"─")+"│",
             "│"+f"  {full}  v{ver}".ljust(w-2)+"│",
             "│"+(("  ★  "+desc[:w-8]) if feat and desc else ("     "+desc[:w-8]) if desc else "").ljust(w-2)+"│",
             "├"+"─"*(w-2)+"┤",
             "│"+f"  Downloads: {dl:,}".ljust(w-2)+"│"]
    if targets:
        t = "Targets: All" if "all" in targets else f"Targets: {', '.join(targets)}"
        lines.append("│"+f"  {t}".ljust(w-2)+"│")
    if lname and lname != "?":
        lines.append("│"+f"  License: {lname}".ljust(w-2)+"│")
    lines.append("└"+"─"*(w-2)+"┘")
    return lines

def _wrap_label_url(label, url, w):
    """Переносит длинный URL на несколько строк внутри бокса."""
    lines = []
    max_w = w - 4
    prefix = f"  {label}: "
    remaining = url
    first = True
    while remaining:
        if first:
            line = prefix + remaining
        else:
            line = "  " + remaining
        if len(line) <= max_w:
            lines.append("│" + line.ljust(w-2) + "│")
            break
        # отступ для первых строк с label, для продолжений без label
        avail = max_w - len(prefix) if first else max_w - 2
        if avail < 10:
            avail = max_w - 10
        lines.append("│" + (prefix + remaining[:avail] if first else "  " + remaining[:avail]).ljust(w-2) + "│")
        remaining = remaining[avail:]
        first = False
    return lines

def box_info(info, w=58):
    name = info.get("name","?")
    lines = []
    lines.append("┌"+"─"*(w-2)+"┐")
    lines.append("│"+f"  {name}".ljust(w-2)+"│")
    lines.append("├"+"─"*(w-2)+"┤")
    if info.get("error"):
        lines.append("│"+f"  ERROR: {info['error']}".ljust(w-2)+"│")
        lines.append("└"+"─"*(w-2)+"┘")
        return lines
    ok = info.get("supports_all",False)
    lines.append("│"+f"  Supports all targets: {'[OK]' if ok else '[--]'}".ljust(w-2)+"│")
    l = info.get("license")
    if l:
        lname = l.get("name",str(l)) if isinstance(l,dict) else str(l)
        lines.append("│"+f"  License: {lname}".ljust(w-2)+"│")
    if info.get("version"):
        lines.append("│"+f"  Version: {info['version']}".ljust(w-2)+"│")
    if info.get("description"):
        lines.append("│"+f"  {info['description'][:w-4]}".ljust(w-2)+"│")
    if info.get("examples"):
        lines.append("│"+f"  Examples: {info['examples']}".ljust(w-2)+"│")
    if info.get("cmd"):
        lines.append("├"+"─"*(w-2)+"┤")
        lines.append("│"+"  Add to project:".ljust(w-2)+"│")
        lines.append("│"+f"  $ {info['cmd']}".ljust(w-2)+"│")
    # Links (full URLs, no truncation)
    link_items = []
    if info.get("homepage"): link_items.append(("GitHub", info["homepage"]))
    if info.get("docs_readme"): link_items.append(("Docs", info["docs_readme"]))
    if info.get("repository"): link_items.append(("Repo", info["repository"]))
    if link_items:
        lines.append("├"+"─"*(w-2)+"┤")
        for label, url in link_items:
            lines.extend(_wrap_label_url(label, url, w))
    lines.append("└"+"─"*(w-2)+"┘")
    return lines

def box_check(r, w=58):
    lines = []
    lines.append("┌"+"─"*(w-2)+"┐")
    lines.append("│"+f"  Compatibility: {r.get('component','?')}".ljust(w-2)+"│")
    lines.append("│"+f"  Board: {r.get('board','?')}  ({r.get('chip','?')})".ljust(w-2)+"│")
    lines.append("├"+"─"*(w-2)+"┤")
    if r.get("error"):
        lines.append("│"+f"  ERROR: {r['error']}".ljust(w-2)+"│")
    else:
        ok = r.get("compatible",False)
        lines.append("│"+f"  {'[OK] Compatible' if ok else '[--] Not confirmed'}".ljust(w-2)+"│")
        lines.append("│"+f"  Supports all targets: {'Yes' if r.get('supports_all') else '?'}".ljust(w-2)+"│")
        if r.get("cmd"):
            lines.append("├"+"─"*(w-2)+"┤")
            lines.append("│"+f"  $ {r['cmd']}".ljust(w-2)+"│")
    lines.append("└"+"─"*(w-2)+"┘")
    return lines

# ─── HTML ──────────────────────────────────────────────────────

def html_table(components):
    h = '<table style="border-collapse:collapse;width:100%;font-family:monospace;">\n'
    h += '<tr style="background:#e8e8e8;">'
    for c in ["Component","Version","Targets","License","Downloads"]:
        h += f'<th style="border:1px solid #aaa;padding:6px;text-align:left;">{c}</th>'
    h += '</tr>\n'
    for c in components:
        nm = f"{c.get('namespace','?')}/{c.get('name','?')}"
        ver = c.get("version","?")
        tg = "All" if "all" in c.get("targets",[]) else ", ".join(c.get("targets",["?"]))
        l = c.get("license","?")
        lname = l.get("name",str(l)) if isinstance(l,dict) else str(l)
        dl = f"{c.get('downloads',0):,}"
        h += '<tr>'
        h += f'<td style="border:1px solid #aaa;padding:6px;"><b>{nm}</b></td>'
        h += f'<td style="border:1px solid #aaa;padding:6px;">v{ver}</td>'
        h += f'<td style="border:1px solid #aaa;padding:6px;">{tg}</td>'
        h += f'<td style="border:1px solid #aaa;padding:6px;">{lname}</td>'
        h += f'<td style="border:1px solid #aaa;padding:6px;text-align:right;">{dl}</td>'
        h += '</tr>\n'
    h += '</table>\n'
    return h

def html_info(info):
    name = info.get("name","?")
    err = info.get("error")
    if err:
        return f'<div style="color:red;font-family:monospace;">ERROR: {err}</div>'
    l = info.get("license","?")
    lname = l.get("name",str(l)) if isinstance(l,dict) else str(l)
    h = f'<div style="font-family:monospace;background:#f5f5f5;padding:12px;border-radius:6px;">'
    h += f'<b>{name}</b><br>'
    h += f'Targets: {"All [OK]" if info.get("supports_all") else "[--]"}<br>'
    h += f'Version: {info.get("version","?")}<br>'
    h += f'License: {lname}<br>'
    if info.get("cmd"):
        h += f'<br><code style="background:#e0e0e0;padding:4px 8px;">{info["cmd"]}</code><br>'
    if info.get("homepage"):
        h += f'<br><a href="{info["homepage"]}">GitHub</a>'
    if info.get("docs_readme"):
        h += f' | <a href="{info["docs_readme"]}">Docs</a>'
    if info.get("repository"):
        h += f' | <a href="{info["repository"]}">Repo</a>'
    h += '</div>'
    return h

# ─── API ───────────────────────────────────────────────────────

def api_search(target=None, query=None, limit=20):
    q_parts = []
    if target: q_parts.append(f"target:{target}")
    if query: q_parts.append(query)
    q = " ".join(q_parts) if q_parts else ""
    url = f"{API_BASE}/components?{urllib.parse.urlencode({'q': q})}"
    sys.stderr.write(f"  [API] {url}\n")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except Exception as e:
        sys.stderr.write(f"  Error: {e}\n"); return []
    result = []
    for item in (data or [])[:limit]:
        lv = item.get("latest_version",{})
        tg = lv.get("targets")
        if tg is None or tg == []: tg = ["all"]
        elif isinstance(tg,list): pass
        else: tg = [str(tg)]
        result.append({
            "namespace": item.get("namespace",""),
            "name": lv.get("name") or item.get("name",""),
            "version": lv.get("version",""),
            "description": lv.get("description",""),
            "targets": tg,
            "downloads": lv.get("downloads_total",0),
            "license": lv.get("license","?"),
            "examples": len(lv.get("examples",[])),
            "featured": item.get("featured",False),
        })
    result.sort(key=lambda x: x["downloads"], reverse=True)
    return result

def api_component_info(namespace, name):
    url = f"{API_BASE}/components/{namespace}/{name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}
    lv = data.get("latest_version") or (data.get("versions") and data["versions"][0]) or {}
    return {
        "name": f"{namespace}/{name}",
        "version": lv.get("version","?"),
        "supports_all": lv.get("targets") is None or lv.get("targets",[]) == [] or "all" in lv.get("targets",[]),
        "cmd": f'idf.py add-dependency "{namespace}/{name}^{lv.get("version","")}"' if lv.get("version") else "",
        "license": lv.get("license","?"),
        "examples": len(lv.get("examples",[])),
        "description": lv.get("description",""),
        "homepage": lv.get("homepage"),
        "docs_readme": lv.get("docs",{}).get("readme") if isinstance(lv.get("docs"), dict) else None,
        "repository": lv.get("repository"),
    }

BOARDS = {
    "heltec-v4": {"chip":"esp32s3","interfaces":["i2c","gpio","spi","wifi"],"display":"ssd1306_i2c_128x64"},
    "korvo-1": {"chip":"esp32s31","interfaces":["i2c","spi","i2s","gpio","camera","wifi"],"display":"lcd_4.3_800x480"},
}

def check_compat(name, board_name="heltec-v4"):
    board = BOARDS.get(board_name)
    if not board: return {"error": f"Unknown board: {board_name}"}
    parts = name.split("/",1)
    if len(parts) != 2: return {"error": "Format: namespace/name"}
    i = api_component_info(parts[0], parts[1])
    return {
        "component": name, "board": board_name, "chip": board.get("chip"),
        "supports_all": i.get("supports_all",False),
        "compatible": i.get("supports_all",False),
        "cmd": i.get("cmd",""),
        "error": i.get("error"),
    }

# ─── CLI ──────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__ % {"prog": os.path.basename(sys.argv[0])}); sys.exit(1)
    cmd = sys.argv[1]
    target=query=None; limit=20; fmt="box"; board="heltec-v4"
    i=2
    while i < len(sys.argv):
        a=sys.argv[i]
        if a=="--target" and i+1<len(sys.argv): target=sys.argv[i+1];i+=1
        elif a=="--query" and i+1<len(sys.argv): query=sys.argv[i+1];i+=1
        elif a=="--limit" and i+1<len(sys.argv): limit=int(sys.argv[i+1]);i+=1
        elif a=="--format" and i+1<len(sys.argv): fmt=sys.argv[i+1];i+=1
        elif a=="--board" and i+1<len(sys.argv): board=sys.argv[i+1];i+=1
        i+=1

    if cmd == "search":
        res = api_search(target=target, query=query, limit=limit)
        if not res: print("[No components found]"); sys.exit(0)
        if fmt == "html":
            print("<html><body style='padding:20px'><h3>ESP Components</h3>"+html_table(res)+"</body></html>")
        elif fmt == "json":
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"\n  target={target or '*'}, query={query or '*'}")
            print(f"  Showing {len(res)} components\n")
            for c in res:
                for l in box_component(c): print(l)
                print()

    elif cmd == "info":
        name = sys.argv[2] if len(sys.argv) > 2 else (target or "")
        parts = name.split("/",1)
        if len(parts)!=2: print("Error: need namespace/name (e.g. espressif/ssd1306)"); sys.exit(1)
        info = api_component_info(parts[0], parts[1])
        if fmt == "html":
            print("<html><body>"+html_info(info)+"</body></html>")
        elif fmt == "json":
            print(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            for l in box_info(info): print(l)

    elif cmd == "check":
        name = sys.argv[2] if len(sys.argv) > 2 else (target or "")
        r = check_compat(name, board)
        if fmt == "json": print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            for l in box_check(r): print(l)

    else:
        print(f"Unknown: {cmd}")
        print(__doc__ % {"prog": os.path.basename(sys.argv[0])})