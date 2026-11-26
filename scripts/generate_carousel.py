import base64
import datetime
import html
import json
import os
from pathlib import Path
from PIL import Image
from google import genai
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
HISTORY_FILE = ROOT / "history.json"
AVATAR_REF = ASSETS / "jasmin_color1_cobalt_gold_9x16.jpg"

TOPICS = [
    "5 Free AI Prompts That Save 10 Hours a Week",
    "Stop Using ChatGPT Wrong — 4 Tiny Prompt Tweaks That 10x Results",
    "AI Tools That Feel Illegal to Know (All Free in 2026)",
    "How I Automate My Entire Morning in 15 Minutes Using Free AI",
    "3 Free AI Apps That Replace a $3,000/mo Creative Team",
    "The 2026 One-Person Business AI Stack ($0 to Start)",
    "NotebookLM Tricks Nobody Talks About (Turn Any PDF Into Gold)",
]


def extract_json(text: str) -> dict:
    s = text.strip()
    if "```" in s:
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    start = s.find("{")
    end = s.rfind("}")
    return json.loads(s[start : end + 1])


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posts": []}


def esc(t: str) -> str:
    return html.escape(str(t or ""))


def highlight_word(headline: str, word: str) -> str:
    h = esc(headline)
    w = esc(word)
    if w and w.lower() in h.lower():
        idx = h.lower().find(w.lower())
        orig = h[idx : idx + len(w)]
        return h[:idx] + f'<span class="hl">{orig}</span>' + h[idx + len(w) :]
    return h


def build_slide_html(slide: dict, issue_num: int, avatar_b64: str) -> str:
    num = slide["num"]
    fonts = """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,500;1,700&family=Caveat:wght@600;700&family=Anton&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    """

    # SLIDE 1: VOGUE / KINFOLK FULL-BLEED EDITORIAL MAGAZINE COVER (0% corporate!)
    if num == 1:
        return f"""<!doctype html><html><head><meta charset="utf-8">{fonts}<style>
        *{{box-sizing:border-box;margin:0;padding:0}}
        body{{width:1080px;height:1350px;overflow:hidden;position:relative;background:#071B5B;font-family:'Inter',sans-serif;}}
        .bg-photo{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 15%;filter:contrast(1.04) saturate(1.06);}}
        .vignette{{position:absolute;inset:0;background:linear-gradient(180deg, rgba(5,16,58,0.68) 0%, rgba(5,16,58,0.12) 32%, rgba(5,16,58,0.08) 65%, rgba(5,16,58,0.72) 100%);}}
        .grain{{position:absolute;inset:0;opacity:0.08;background-image:radial-gradient(#fff 1px, transparent 0);background-size:4px 4px;}}
        .masthead{{position:absolute;top:52px;left:0;right:0;text-align:center;font-size:24px;letter-spacing:0.28em;color:#FDE68A;font-weight:600;text-transform:uppercase;text-shadow:0 2px 12px rgba(0,0,0,0.4);}}
        .title{{position:absolute;top:105px;left:56px;right:56px;text-align:center;font-family:'Playfair Display',serif;font-weight:900;font-size:128px;line-height:0.96;color:#FFFFFF;letter-spacing:-0.02em;text-shadow:0 12px 35px rgba(4,12,42,0.55);}}
        .subline{{position:absolute;bottom:118px;left:72px;max-width:680px;font-family:'Playfair Display',serif;font-style:italic;font-size:42px;line-height:1.25;color:#FDE68A;text-shadow:0 4px 20px rgba(0,0,0,0.65);}}
        .footer{{position:absolute;bottom:48px;left:72px;right:72px;display:flex;justify-content:space-between;align-items:center;color:rgba(255,255,255,0.92);font-size:24px;letter-spacing:0.12em;font-weight:600;}}
        </style></head><body>
          <img class="bg-photo" src="{avatar_b64}" />
          <div class="vignette"></div>
          <div class="grain"></div>
          <div class="masthead">JASMIN [VER 1.0] &mdash; ISSUE {issue_num:02d}</div>
          <div class="title">{esc(slide.get("headline", ""))}</div>
          <div class="subline">{esc(slide.get("subline", ""))}</div>
          <div class="footer"><span>@jasmin.ver_1.0</span><span>SWIPE &rarr;</span></div>
        </body></html>"""

    # SLIDES 2-6: TACTILE CREAM-PAPER SCRAPBOOK & COLLAGE ZINE (0% corporate!)
    tilt_note = [-2.6, 2.2, -1.8, 2.5, -2.0][num - 2]
    tilt_photo = [3.5, -3.2, 2.8, -3.5, -4.0][num - 2]
    hl_headline = highlight_word(slide.get("headline", ""), slide.get("highlight", ""))
    is_final = num == 6

    polaroid_block = ""
    if is_final:
        polaroid_block = f"""
        <div class="polaroid" style="transform:rotate({tilt_photo}deg);">
          <div class="tape tape-l"></div>
          <div class="tape tape-r"></div>
          <img src="{avatar_b64}" />
          <div class="pol-cap">Jasmin [Ver 1.0]</div>
        </div>
        """

    return f"""<!doctype html><html><head><meta charset="utf-8">{fonts}<style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{
      width:1080px;height:1350px;overflow:hidden;position:relative;
      background:#F2EBDD;
      background-image:
        radial-gradient(rgba(120,100,70,0.09) 1.2px, transparent 0),
        radial-gradient(rgba(160,135,95,0.06) 1px, transparent 0);
      background-size:28px 28px, 19px 19px;
      background-position:0 0, 9px 11px;
      color:#161616;font-family:'Inter',sans-serif;
    }}
    .wrap{{position:relative;z-index:2;width:100%;height:100%;padding:72px 76px 64px;display:flex;flex-direction:column;justify-content:space-between;}}
    .top{{display:flex;justify-content:space-between;align-items:center;font-family:'Caveat',cursive;font-size:38px;color:#3F3A32;}}
    .headline{{font-family:'Anton',sans-serif;font-size:{"92px" if not is_final else "86px"};line-height:1.05;letter-spacing:0.01em;text-transform:uppercase;color:#141414;text-align:center;margin-top:10px;}}
    .hl{{background:linear-gradient(180deg, transparent 15%, #E7FF3D 15%, #E7FF3D 92%, transparent 92%);padding:0 14px;display:inline-block;transform:rotate(-1deg);}}
    .polaroid{{
      width:380px;margin:18px auto 8px;background:#FFFFFF;padding:18px 18px 54px;
      box-shadow:0 18px 40px rgba(30,24,12,0.22);position:relative;
    }}
    .polaroid img{{width:100%;height:340px;object-fit:cover;object-position:center 18%;display:block;}}
    .pol-cap{{position:absolute;bottom:10px;left:0;right:0;text-align:center;font-family:'Caveat',cursive;font-size:32px;color:#222;}}
    .tape{{position:absolute;top:-22px;width:128px;height:40px;background:rgba(245,239,220,0.78);box-shadow:0 2px 6px rgba(0,0,0,0.08);}}
    .tape-l{{left:-22px;transform:rotate(-26deg);}}
    .tape-r{{right:-22px;transform:rotate(24deg);}}
    .torn-note{{
      position:relative;margin:{"12px" if is_final else "36px"} auto;width:88%;
      background:#FFFCF5;padding:{"38px 46px" if is_final else "56px 54px"};
      box-shadow:0 20px 45px rgba(35,28,15,0.16);
      transform:rotate({tilt_note}deg);
      border-top:4px dashed #DDD3C0;
      border-bottom:5px dashed #DDD3C0;
    }}
    .tape-top{{position:absolute;top:-24px;left:50%;transform:translateX(-50%) rotate(-3deg);width:170px;height:44px;background:rgba(235,226,202,0.82);box-shadow:0 2px 6px rgba(0,0,0,0.08);}}
    .note-text{{font-family:'Caveat',cursive;font-size:{"46px" if is_final else "58px"};line-height:1.28;color:#1A1A1A;font-weight:700;}}
    .sub-tip{{margin-top:24px;font-family:'Inter',sans-serif;font-size:27px;line-height:1.45;color:#4A453B;font-weight:600;}}
    .doodle{{position:absolute;pointer-events:none;}}
    .foot{{display:flex;justify-content:space-between;align-items:center;font-family:'Caveat',cursive;font-size:40px;font-weight:700;color:#181818;}}
    </style></head><body>
      <svg class="doodle" style="top:310px;right:48px;width:110px;height:140px;" viewBox="0 0 110 140" fill="none">
        <path d="M25 10 C80 35, 90 85, 45 122" stroke="#181818" stroke-width="4.5" stroke-linecap="round"/>
        <path d="M35 105 L44 124 L65 116" stroke="#181818" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <svg class="doodle" style="bottom:195px;left:44px;width:90px;height:90px;" viewBox="0 0 90 90" fill="none">
        <path d="M45 8 L53 33 L80 35 L58 51 L66 78 L45 62 L24 78 L32 51 L10 35 L37 33 Z" stroke="#181818" stroke-width="3.5" stroke-linejoin="round"/>
      </svg>
      <div class="wrap">
        <div class="top">
          <span>Issue #{issue_num:02d} &middot; Jasmin’s Notes</span>
          <span>0{num} / 06</span>
        </div>
        <div class="headline">{hl_headline}</div>
        {polaroid_block}
        <div class="torn-note">
          <div class="tape-top"></div>
          <div class="note-text">{esc(slide.get("note", ""))}</div>
          {"<div class='sub-tip'>" + esc(slide.get("tip", "")) + "</div>" if slide.get("tip") else ""}
        </div>
        <div class="foot">
          <span>@jasmin.ver_1.0</span>
          <span>{"save &amp; follow ★" if is_final else "swipe &rarr;"}</span>
        </div>
      </div>
    </body></html>"""


def main():
    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})

    history = load_history()
    issue_num = len(history["posts"]) + 3
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")
    topic = os.environ.get("TOPIC_OVERRIDE", "").strip()
    if not topic:
        topic = TOPICS[(issue_num - 3) % len(TOPICS)]

    out_dir = DOCS / "posts" / f"{today}_issue_{issue_num:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    plan_prompt = f"""
You are the creative director for @jasmin.ver_1.0 (Jasmin [Ver 1.0]), an English global AI virtual creator Instagram account.
Create a viral, ultra-punchy 6-slide Instagram carousel plan for Issue #{issue_num:02d} on the topic: "{topic}".

Rules:
- Slide 1 (Magazine Cover): "headline" MUST be super short (2-3 words max, e.g. "5 Free Prompts" or "Work Smarter"), "subline" 6-10 words.
- Slides 2-5 (Handwritten Scrapbook Zine): "headline" 3-6 words, "highlight" 1 key word from headline to highlight in neon yellow, "note" 1 punchy handwritten-style insight (10-16 words), "tip" 1 concrete action/example (10-16 words).
- Slide 6 (Final CTA): "headline" 3-5 words, "highlight" 1 word, "note" warm CTA with SAVE, COMMENT a 1-word keyword, FOLLOW @jasmin.ver_1.0.
- "caption": Engaging English Instagram caption with 7 hashtags.

Return STRICT JSON only:
{{
  "issue": {issue_num},
  "topic": "{topic}",
  "caption": "...",
  "slides": [
    {{"num": 1, "headline": "...", "subline": "..."}},
    {{"num": 2, "headline": "...", "highlight": "...", "note": "...", "tip": "..."}},
    {{"num": 3, "headline": "...", "highlight": "...", "note": "...", "tip": "..."}},
    {{"num": 4, "headline": "...", "highlight": "...", "note": "...", "tip": "..."}},
    {{"num": 5, "headline": "...", "highlight": "...", "note": "...", "tip": "..."}},
    {{"num": 6, "headline": "...", "highlight": "...", "note": "..."}}
  ]
}}
"""
    plan_resp = None
    for text_model in ["gemini-2.5-flash", "gemini-4-hydrogen", "gemini-2.0-flash"]:
        try:
            plan_resp = client.models.generate_content(model=text_model, contents=plan_prompt)
            print("Planned copy using:", text_model)
            break
        except Exception as e:
            print(f"Text model {text_model} skipped: {e}")
    if plan_resp is None:
        raise RuntimeError("No text model succeeded")
    plan = extract_json(plan_resp.text)

    avatar_b64 = "data:image/jpeg;base64," + base64.b64encode(AVATAR_REF.read_bytes()).decode("ascii")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for s in plan["slides"]:
            num = s["num"]
            html_file = out_dir / f"slide_{num}.html"
            png_file = out_dir / f"slide_{num}.png"
            jpg_file = out_dir / f"slide_{num}.jpg"
            html_file.write_text(build_slide_html(s, issue_num, avatar_b64), encoding="utf-8")
            page.goto(f"file://{html_file}", wait_until="networkidle")
            page.wait_for_timeout(500)
            page.screenshot(path=str(png_file), full_page=False)
            Image.open(png_file).convert("RGB").save(jpg_file, "JPEG", quality=92)
            png_file.unlink()
            html_file.unlink()
            print(f"Rendered v2 slide_{num}.jpg")
        browser.close()

    meta = {
        "issue": issue_num,
        "date": today,
        "folder": out_dir.relative_to(DOCS).as_posix(),
        "topic": plan["topic"],
        "caption": plan["caption"],
        "slides": [f"slide_{i}.jpg" for i in range(1, 7)],
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (DOCS / "latest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    history["posts"].append(meta)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print("v2 Magazine + Scrapbook carousel complete:", meta["folder"])


if __name__ == "__main__":
    main()
