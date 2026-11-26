import json
import os
import datetime
from pathlib import Path
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
HISTORY_FILE = ROOT / "history.json"

AVATAR_REF = ASSETS / "jasmin_color1_cobalt_gold_9x16.jpg"
REF_MAGAZINE = ASSETS / "ref_1_vogue_magazine.jpg"
REF_SCRAPBOOK = ASSETS / "ref_2_scrapbook_collage.jpg"

TOPICS = [
    "5 Free AI Prompts That Save 10 Hours a Week",
    "Stop Using ChatGPT Wrong — 4 Tiny Prompt Tweaks That 10x Results",
    "AI Tools That Feel Illegal to Know (All Free in 2026)",
    "How I Automate My Entire Morning in 15 Minutes Using Free AI",
    "3 Free AI Apps That Replace a $3,000/mo Creative Team",
    "The 2026 One-Person Business AI Stack ($0 to Start)",
    "NotebookLM Tricks Nobody Talks About (Turn Any PDF Into Gold)",
]


def crop_to_4x5(img: Image.Image) -> Image.Image:
    w, h = img.size
    target_ratio = 4 / 5
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    return img.resize((1080, 1350), Image.Resampling.LANCZOS).convert("RGB")


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posts": []}


def main():
    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    history = load_history()
    issue_num = len(history["posts"]) + 3  # Starts from Issue 03 (post_001 & post_002 already live)
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")
    topic = os.environ.get("TOPIC_OVERRIDE", "").strip()
    if not topic:
        topic = TOPICS[(issue_num - 3) % len(TOPICS)]

    out_dir = DOCS / "posts" / f"{today}_issue_{issue_num:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Plan 6-slide copy & caption using Gemini text model
    plan_prompt = f"""
You are the creative director for @jasmin.ver_1.0 (Jasmin [Ver 1.0]), an English global AI virtual creator Instagram account.
Create a viral, ultra-concise 6-slide Instagram carousel plan for Issue #{issue_num:02d} on the topic: "{topic}".

Rules:
- Keep every slide super punchy (short headlines, max 12-18 words per slide) so it looks like a luxury magazine & trendy handwritten scrapbook — NEVER like a corporate PowerPoint!
- Slide 1: Cover hook (2-4 word huge magazine headline + short 5-8 word subtitle).
- Slides 2-5: 4 concrete actionable tips/tools/prompts (short bold headline + 1 crisp sticky-note tip each).
- Slide 6: Warm CTA asking to SAVE, COMMENT a 1-word keyword, and FOLLOW @jasmin.ver_1.0.
- Also write an engaging English Instagram caption with 7 relevant hashtags.

Return STRICT JSON only:
{{
  "issue": {issue_num},
  "topic": "{topic}",
  "keyword": "AI",
  "caption": "...",
  "slides": [
    {{"num": 1, "headline": "...", "subline": "..."}},
    {{"num": 2, "headline": "...", "note": "..."}},
    {{"num": 3, "headline": "...", "note": "..."}},
    {{"num": 4, "headline": "...", "note": "..."}},
    {{"num": 5, "headline": "...", "note": "..."}},
    {{"num": 6, "headline": "...", "note": "..."}}
  ]
}}
"""
    plan_resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=plan_prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    plan = json.loads(plan_resp.text)

    avatar_img = Image.open(AVATAR_REF)
    mag_ref = Image.open(REF_MAGAZINE)
    scrap_ref = Image.open(REF_SCRAPBOOK)

    # 2. Generate 6 slides (Slide 1 = Vogue Magazine Cover, Slides 2-6 = Tactile Scrapbook Zine)
    for s in plan["slides"]:
        num = s["num"]
        if num == 1:
            img_prompt = (
                f"Create a 3:4 vertical Vogue x Kinfolk high-fashion editorial magazine cover Instagram slide, "
                f"matching the exact editorial photography style of reference 2 and the exact face, jet-black bob, "
                f"ivory gold-button blazer, and sunlit cobalt-blue studio wall of reference 1 (Jasmin). "
                f"Overlay clean luxury print typography (ZERO boxes, ZERO cards): "
                f"Top masthead: 'JASMIN [VER 1.0] — ISSUE {issue_num:02d}'. "
                f"Huge white serif headline partially tucked behind her hair: '{s['headline']}'. "
                f"Champagne gold italic subline: '{s.get('subline', '')}'. "
                f"Small 'SWIPE →' at bottom right."
            )
            refs = [avatar_img, mag_ref]
        elif num == 6:
            img_prompt = (
                f"Create a 3:4 vertical tactile cream-paper scrapbook zine final CTA slide matching the aesthetic of reference 2. "
                f"Feature a slightly tilted taped Polaroid of the woman from reference 1 (Jasmin in ivory blazer on cobalt blue). "
                f"Bold black brutalist headline: '{s['headline']}'. "
                f"Torn handwritten note below with yellow highlighter and ink doodles: '{s.get('note', '')}'. "
                f"Bottom text: '@jasmin.ver_1.0' and 'SAVE & FOLLOW ★'. Zero corporate boxes."
            )
            refs = [avatar_img, scrap_ref]
        else:
            img_prompt = (
                f"Create a 3:4 vertical tactile cream-paper digital scrapbook & zine Instagram slide matching the exact aesthetic of reference 1: "
                f"warm fine-grain cream paper background, masking tape, torn paper memo cutout, bright yellow highlighter stroke, "
                f"hand-drawn black ink arrows and tiny star doodles. Zero corporate boxes or PowerPoint grids. "
                f"Top small handwritten label: '0{num} / 06'. "
                f"Bold black editorial headline with key word highlighted in bright yellow: '{s['headline']}'. "
                f"Torn notebook/receipt paper taped at slight 3-degree tilt with clean handwritten note: '{s.get('note', '')}'. "
                f"Bottom left: '@jasmin.ver_1.0', bottom right: 'swipe →'."
            )
            refs = [scrap_ref]

        resp = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[img_prompt, *refs],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="3:4"),
            ),
        )
        saved = False
        for part in resp.candidates[0].content.parts:
            if part.inline_data is not None:
                im = Image.open(BytesIO(part.inline_data.data))
                im = crop_to_4x5(im)
                im.save(out_dir / f"slide_{num}.jpg", "JPEG", quality=92)
                print(f"Saved slide_{num}.jpg")
                saved = True
                break
        if not saved:
            raise RuntimeError(f"Failed to generate image for slide {num}")

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
    print("Carousel generation complete:", meta["folder"])


if __name__ == "__main__":
    main()
