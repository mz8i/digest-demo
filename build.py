#!/usr/bin/env python3
"""Build the static demo-link site from the sibling application repository."""

from __future__ import annotations

import argparse
import html
import importlib.util
import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parent
DOCS = REPO_ROOT / "docs"
DEFAULT_SOURCE = REPO_ROOT.parent / "digest" / "dev-tools" / "demo-data" / "senders.json"

# Product display name only. Repository names and the public URL remain unchanged.
APP_NAME = "Digest"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    return parser.parse_args()


def load_digest_generator(source_path: Path):
    generator_path = source_path.parent / "generate.py"
    spec = importlib.util.spec_from_file_location("digest_demo_generator", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in text.splitlines())
    if text.endswith("\n"):
        cleaned += "\n"
    path.write_text(cleaned, encoding="utf-8", newline="\n")


def shell(
    *,
    title: str,
    description: str,
    body: str,
    css_path: str,
    canonical: str,
    accent: str = "#f06a47",
    background: str = "#f4efe7",
    ink: str = "#20252b",
) -> str:
    esc = html.escape
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="stylesheet" href="{esc(css_path)}">
  <title>{esc(title)}</title>
</head>
<body style="--accent:{esc(accent)};--paper:{esc(background)};--ink:{esc(ink)}">
  {body}
</body>
</html>
"""


def story_body(sender: dict[str, Any], story: dict[str, Any]) -> str:
    esc = html.escape
    paragraphs = [story["paragraph"], *story.get("additionalParagraphs", [])]
    paragraphs_html = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in paragraphs)
    bullets_html = ""
    if story.get("bullets"):
        bullets_html = "<ul>" + "".join(
            f"<li>{esc(item)}</li>" for item in story["bullets"]
        ) + "</ul>"
    quote_html = f"<blockquote>{esc(story['quote'])}</blockquote>" if story.get("quote") else ""
    return f"""
<header class="masthead compact">
  <a class="back" href="../">← {esc(sender['name'])}</a>
  <div class="mark" aria-hidden="true">{esc(sender['mark'])}</div>
  <p class="eyebrow">{esc(sender['editionLabel'])}</p>
</header>
<main class="article">
  <h1>{esc(story['heading'])}</h1>
  <p class="standfirst">{esc(story['subject'])}</p>
  {paragraphs_html}
  {bullets_html}
  {quote_html}
  <aside class="demo-note"><strong>Fictional demo article.</strong> This page exists so a link opened from {esc(APP_NAME)}’s demo inbox has a safe, realistic destination.</aside>
</main>
<footer><a href="../">More from {esc(sender['name'])}</a><span>{esc(APP_NAME)} demo link</span></footer>
"""


def sender_index(sender: dict[str, Any], public_base: str) -> str:
    esc = html.escape
    stories = "".join(
        f'<li><a href="{esc(story["slug"])}/"><span>{esc(story["heading"])}</span>'
        f'<small>{esc(story["subject"])}</small></a></li>'
        for story in sender["stories"]
    )
    body = f"""
<header class="masthead">
  <a class="back" href="../">← All publications</a>
  <div class="mark" aria-hidden="true">{esc(sender['mark'])}</div>
  <p class="eyebrow">{esc(sender['editionLabel'])}</p>
  <h1>{esc(sender['masthead'])}</h1>
  <p class="deck">{esc(sender['deck'])}</p>
</header>
<main class="index-page">
  <h2>From the archive</h2>
  <ul class="story-list">{stories}</ul>
</main>
<footer><a href="preferences/">Email preferences</a><a href="unsubscribe/">Unsubscribe</a><span>Fictional publication</span></footer>
"""
    return shell(
        title=f"{sender['name']} — {APP_NAME} demo",
        description=sender["deck"],
        body=body,
        css_path="../assets/site.css",
        canonical=f"{public_base}/{sender['key']}/",
        accent=sender["accent"],
        background=sender["background"],
        ink=sender.get("ink", "#242424"),
    )


def status_page(sender: dict[str, Any], kind: str, public_base: str) -> str:
    esc = html.escape
    if kind == "unsubscribe":
        title = f"No subscription changed — {sender['name']}"
        heading = "Nothing was unsubscribed"
        copy = f"This is a fictional newsletter used by {APP_NAME}’s demo inbox. There is no mailing list and no personal information was submitted."
    else:
        title = f"Demo preferences — {sender['name']}"
        heading = "Demo email preferences"
        copy = "This fictional publication has no account or saved preferences. This page is a safe destination for the link in the demo email."
    body = f"""
<main class="status-card">
  <div class="mark" aria-hidden="true">{esc(sender.get('mark', 'D'))}</div>
  <p class="eyebrow">{esc(sender['name'])}</p>
  <h1>{esc(heading)}</h1>
  <p>{esc(copy)}</p>
  <a class="button" href="../">Return to the publication</a>
</main>
"""
    return shell(
        title=title,
        description=copy,
        body=body,
        css_path="../../assets/site.css",
        canonical=f"{public_base}/{sender['key']}/{kind}/",
        accent=sender["accent"],
        background=sender["background"],
        ink=sender.get("ink", "#242424"),
    )


def message_page(sender: dict[str, Any], message: dict[str, Any], public_base: str, slugify) -> str:
    esc = html.escape
    slug = slugify(message["subject"])
    paragraphs = "".join(f"<p>{esc(item)}</p>" for item in message["paragraphs"])
    action = esc(message.get("actionLabel", "Open"))
    body = f"""
<header class="service-head"><a class="back" href="../../../">← {esc(APP_NAME)} demo links</a><p>{esc(sender['name'])}</p></header>
<main class="article service">
  <h1>{esc(message['subject'])}</h1>
  {paragraphs}
  <div class="action-result"><strong>{action}</strong><span>This is a fictional destination. No account, booking, payment, or external action exists.</span></div>
</main>
<footer><span>Fictional service notification</span><span>No data collected</span></footer>
"""
    return shell(
        title=f"{message['subject']} — {sender['name']}",
        description=f"A fictional demo destination for {sender['name']}.",
        body=body,
        css_path="../../../assets/site.css",
        canonical=f"{public_base}/{sender['key']}/message/{slug}/",
        accent=sender["accent"],
        background=sender["background"],
    )


def landing(newsletters: list[dict[str, Any]], public_base: str) -> str:
    esc = html.escape
    cards = "".join(
        f'<a class="publication" href="{esc(sender["key"])}/" '
        f'style="--card-accent:{esc(sender["accent"])};--card-paper:{esc(sender["background"])};'
        f'--card-ink:{esc(sender["ink"])}">'
        f'<span class="mini-mark">{esc(sender["mark"])}</span><strong>{esc(sender["name"])}</strong>'
        f'<small>{esc(sender["deck"])}</small></a>'
        for sender in newsletters
    )
    body = f"""
<header class="home-hero">
  <p class="eyebrow">{esc(APP_NAME)} demo links</p>
  <h1>The stories behind the inbox</h1>
  <p>Safe, fictional destinations for links opened from {esc(APP_NAME)}’s newsletter demo. No sign-in, subscription, tracking, or personal data.</p>
</header>
<main class="home-main">
  <div class="intro-row"><h2>Publications</h2><p>{len(newsletters)} fictional archives</p></div>
  <div class="publication-grid">{cards}</div>
  <section class="about"><h2>Why this site exists</h2><p>{esc(APP_NAME)} is a calm seated VR space for catching up on newsletters. These static pages let its browser-opening interaction work during a demo without directing people to real publishers or changing services.</p></section>
</main>
<footer><span>Fictional demo content</span><span>No analytics or cookies</span></footer>
"""
    return shell(
        title=f"{APP_NAME} demo links",
        description=f"Fictional article destinations for the {APP_NAME} demo inbox.",
        body=body,
        css_path="assets/site.css",
        canonical=f"{public_base}/",
    )


def build(source_path: Path) -> None:
    generator = load_digest_generator(source_path)
    source = generator.load_source(source_path)
    generator.validate_source(source)
    public_base = source["publicBaseUrl"]

    newsletters = list(source["senders"])
    for arrival in source["arrivals"]:
        if arrival["kind"] == "new-newsletter":
            sender = dict(arrival["sender"])
            sender["publicBaseUrl"] = f"{public_base}/{sender['key']}"
            newsletters.append(sender)

    if DOCS.parent != REPO_ROOT or DOCS.name != "docs":
        raise RuntimeError(f"Refusing to replace unexpected output directory: {DOCS}")
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "assets").mkdir(parents=True)

    write(DOCS / ".nojekyll", "")
    write(DOCS / "robots.txt", "User-agent: *\nDisallow: /\n")
    write(DOCS / "assets" / "site.css", CSS)
    write(DOCS / "index.html", landing(newsletters, public_base))

    page_count = 1
    for sender in newsletters:
        sender_dir = DOCS / sender["key"]
        write(sender_dir / "index.html", sender_index(sender, public_base))
        write(sender_dir / "preferences" / "index.html", status_page(sender, "preferences", public_base))
        write(sender_dir / "unsubscribe" / "index.html", status_page(sender, "unsubscribe", public_base))
        page_count += 3
        for story in sender["stories"]:
            page = shell(
                title=f"{story['heading']} — {sender['name']}",
                description=story["paragraph"],
                body=story_body(sender, story),
                css_path="../../assets/site.css",
                canonical=f"{public_base}/{sender['key']}/{story['slug']}/",
                accent=sender["accent"],
                background=sender["background"],
                ink=sender["ink"],
            )
            write(sender_dir / story["slug"] / "index.html", page)
            page_count += 1

    others = {sender["key"]: sender for sender in source["others"]}
    arrival_messages: dict[str, list[dict[str, Any]]] = {}
    for arrival in source["arrivals"]:
        if arrival["kind"] == "other" and arrival["message"].get("bodyKind", others[arrival["senderKey"]]["bodyKind"]) == "html":
            arrival_messages.setdefault(arrival["senderKey"], []).append(arrival["message"])
    for sender in others.values():
        html_messages = [
            message
            for message in sender["messages"] + arrival_messages.get(sender["key"], [])
            if message.get("bodyKind", sender["bodyKind"]) == "html"
        ]
        for message in html_messages:
            slug = generator.slugify(message["subject"])
            write(
                DOCS / sender["key"] / "message" / slug / "index.html",
                message_page(sender, message, public_base, generator.slugify),
            )
            page_count += 1
        if sender["listUnsubscribe"]:
            write(
                DOCS / sender["key"] / "unsubscribe" / "index.html",
                status_page(sender, "unsubscribe", public_base),
            )
            page_count += 1

    not_found = """
<main class="status-card"><div class="mark" aria-hidden="true">{html.escape(APP_NAME[:1].upper() or "D")}</div><p class="eyebrow">{html.escape(APP_NAME)} demo links</p><h1>That fictional page is missing</h1><p>The link may belong to a newer version of the demo dataset.</p><a class="button" href="/digest-demo/">Browse the demo publications</a></main>
"""
    write(
        DOCS / "404.html",
        shell(
            title=f"Page not found — {APP_NAME} demo",
            description=f"This fictional {APP_NAME} demo page was not found.",
            body=not_found,
            css_path="/digest-demo/assets/site.css",
            canonical=f"{public_base}/404.html",
        ),
    )
    dataset = generator.build_dataset(source)
    public_links = set()
    for entry in dataset["messages"] + dataset["arrivals"]:
        public_links.update(
            link
            for link in re.findall(r'href="([^"]+)"', entry["html"], re.IGNORECASE)
            if link.startswith(public_base + "/")
        )
    missing = []
    base_path = urlparse(public_base).path.rstrip("/") + "/"
    for link in sorted(public_links):
        path = unquote(urlparse(link).path)
        if not path.startswith(base_path):
            missing.append(link)
            continue
        relative = path[len(base_path):]
        target = DOCS / relative
        if path.endswith("/"):
            target /= "index.html"
        if not target.is_file():
            missing.append(link)
    if missing:
        raise RuntimeError("Missing generated targets:\n" + "\n".join(missing))
    print(f"Built {page_count + 1} HTML pages in {DOCS}")
    print(f"Validated {len(public_links)} unique URLs used by DemoMail.json")


CSS = r"""
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper);font-synthesis:none}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:var(--paper);color:var(--ink)}a{color:inherit}.masthead,.home-hero,.service-head{max-width:760px;margin:0 auto;padding:64px 28px 48px}.masthead.compact{padding-bottom:12px}.back{display:inline-block;margin-bottom:40px;text-decoration:none;font-size:.9rem;opacity:.68}.mark,.mini-mark{display:grid;place-items:center;background:var(--accent);color:var(--ink);font-weight:800;letter-spacing:-.04em}.mark{width:72px;height:72px;border-radius:22px;margin-bottom:22px}.mini-mark{width:44px;height:44px;border-radius:14px;font-size:.78rem}.eyebrow{font-size:.76rem;font-weight:750;letter-spacing:.15em;text-transform:uppercase;opacity:.66}.masthead h1,.home-hero h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(2.7rem,8vw,5.8rem);line-height:.94;letter-spacing:-.045em;margin:.18em 0}.deck,.home-hero>p:last-child{font-family:Georgia,"Times New Roman",serif;font-size:1.35rem;line-height:1.55;max-width:650px}.article,.index-page,.home-main{max-width:760px;margin:0 auto;padding:24px 28px 80px}.article h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(2.4rem,7vw,4.9rem);line-height:1.02;letter-spacing:-.035em;margin:.25em 0}.article p,.article li{font-family:Georgia,"Times New Roman",serif;font-size:1.2rem;line-height:1.75}.article .standfirst{font-style:italic;font-size:1.06rem;opacity:.7;margin-bottom:42px}.article blockquote{font-family:Georgia,"Times New Roman",serif;font-size:1.55rem;line-height:1.5;border-left:5px solid var(--accent);margin:38px 0;padding:8px 0 8px 25px}.demo-note,.action-result{margin-top:54px;padding:22px 24px;border-radius:18px;background:color-mix(in srgb,var(--accent) 16%,white);font-size:.95rem;line-height:1.6}.story-list{list-style:none;margin:0;padding:0;border-top:1px solid color-mix(in srgb,var(--ink) 20%,transparent)}.story-list a{display:flex;justify-content:space-between;gap:24px;padding:21px 4px;border-bottom:1px solid color-mix(in srgb,var(--ink) 20%,transparent);text-decoration:none}.story-list span{font-family:Georgia,"Times New Roman",serif;font-size:1.15rem}.story-list small{max-width:250px;text-align:right;opacity:.6}.home-hero{padding-top:90px}.home-hero h1{max-width:700px}.intro-row{display:flex;align-items:baseline;justify-content:space-between}.intro-row p{opacity:.6}.publication-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.publication{display:flex;min-height:210px;flex-direction:column;gap:15px;padding:22px;border-radius:22px;text-decoration:none;color:var(--card-ink);background:var(--card-paper);border:1px solid color-mix(in srgb,var(--card-accent) 45%,transparent)}.publication .mini-mark{margin-bottom:auto;background:var(--card-accent);color:var(--card-ink)}.publication strong{font-family:Georgia,"Times New Roman",serif;font-size:1.2rem}.publication small{line-height:1.45;opacity:.68}.about{margin-top:70px;padding:36px;border-radius:24px;background:#fff9}.about p{font-family:Georgia,"Times New Roman",serif;font-size:1.18rem;line-height:1.65}.status-card{max-width:620px;margin:12vh auto;padding:48px;border-radius:28px;background:#fff9;box-shadow:0 20px 70px #0001}.status-card h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(2.2rem,7vw,4rem);line-height:1}.status-card p{font-size:1.08rem;line-height:1.65}.button{display:inline-block;margin-top:18px;padding:13px 18px;border-radius:12px;background:var(--accent);text-decoration:none;font-weight:750}.service-head{padding-bottom:10px}.service-head p{font-weight:800;color:var(--accent)}.action-result{display:flex;flex-direction:column;gap:5px}.action-result span{font-family:inherit;font-size:.92rem}footer{display:flex;flex-wrap:wrap;gap:18px;justify-content:center;padding:28px;border-top:1px solid color-mix(in srgb,var(--ink) 18%,transparent);font-size:.8rem;opacity:.7}footer a{text-decoration:none}@media(max-width:720px){.publication-grid{grid-template-columns:1fr 1fr}.story-list a{flex-direction:column;gap:7px}.story-list small{text-align:left;max-width:none}}@media(max-width:470px){.publication-grid{grid-template-columns:1fr}.masthead,.home-hero,.service-head{padding-left:20px;padding-right:20px}.article,.index-page,.home-main{padding-left:20px;padding-right:20px}.status-card{margin:20px;padding:30px}}
"""


if __name__ == "__main__":
    build(parse_args().source.resolve())
