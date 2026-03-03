#!/usr/bin/env python3
"""
get_bibtex.py

Usage:
    python get_bibtex.py <url>

This script tries to fetch BibTeX for a given paper URL. Supported/attempted sources:
- arXiv (via arXiv bibtex endpoint)
- ACL Anthology (.bib endpoint)
- OpenReview / ICLR / other pages using citation_* meta tags
- DOI content-negotiation (doi.org Accept: application/x-bibtex)
- Generic scraping of BibTeX blocks or .bib links

Outputs BibTeX to stdout.

Requirements: requests, beautifulsoup4

"""

from __future__ import annotations
import sys
import re
import argparse
from urllib.parse import urlparse, urljoin
import html
import requests
from bs4 import BeautifulSoup

UA = "get-bibtex-script/1.1 (+https://github.com/your/repo)"

session = requests.Session()
session.headers.update({"User-Agent": UA})


def fetch(url: str, **kwargs) -> requests.Response:
    return session.get(url, timeout=15, **kwargs)


# ---------------------- Helpers for keys and extraction ----------------------


def make_bibkey(authors_field: str, year: str, title: str) -> str:
    """
    Build a deterministic key like 'fehr2024nonparametric'.
    authors_field: 'Fabio James Fehr and James Henderson' or similar.
    """
    if not authors_field:
        first = "anon"
    else:
        if " and " in authors_field:
            first_author = authors_field.split(" and ")[0].strip()
        elif ";" in authors_field:
            first_author = authors_field.split(";")[0].strip()
        else:
            first_author = authors_field.strip()
        if "," in first_author:
            family = first_author.split(",")[0].strip()
        else:
            parts = first_author.split()
            family = parts[-1] if parts else first_author
        first = re.sub(r"\W+", "", family).lower() or "anon"
    year_part = re.sub(r"\D", "", str(year))[:4] or "n.d."
    short_title = re.sub(r"\W+", "", (title.split()[0] if title else "paper")).lower()
    key = f"{first}{year_part}{short_title}"
    # limit length
    return key[:60]


def extract_year_from_meta_or_text(soup: BeautifulSoup, html_text: str) -> str | None:
    m = soup.find("meta", attrs={"name": "citation_year"})
    if m and m.get("content"):
        return m["content"].strip()
    m = soup.find("meta", attrs={"name": "citation_date"})
    if m and m.get("content"):
        y = re.search(r"(19|20)\d{2}", m["content"])
        if y:
            return y.group(0)
    # try other meta names
    for name in ("dc.date", "citation_publication_date", "citation_online_date"):
        m = soup.find("meta", attrs={"name": name})
        if m and m.get("content"):
            y = re.search(r"(19|20)\d{2}", m["content"])
            if y:
                return y.group(0)
    # fallback: find first 4-digit year in the visible text
    y = re.search(r"\b(19|20)\d{2}\b", html_text)
    if y:
        return y.group(0)
    return None


# ---------------------- Site-specific attempts ----------------------


def try_arxiv(url: str) -> str | None:
    m = re.search(r"arxiv\.org/(abs|pdf)/(?P<id>\d{4}\.\d{4,5}(v\d+)?)", url)
    if not m:
        m2 = re.search(r"arxiv\.org/(abs|pdf)/(?P<id>[a-zA-Z\-]+/\d{7}(v\d+)?)", url)
        if m2:
            m = m2
    if not m:
        return None
    arxiv_id = m.group("id")
    bib_url = f"https://arxiv.org/bibtex/{arxiv_id}"
    try:
        r = fetch(bib_url)
        r.raise_for_status()
    except Exception:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    pre = soup.find("pre")
    if pre:
        text = pre.get_text().strip()
        if text.lower().startswith("@"):
            return text
    text = r.text.strip()
    if text.lower().startswith("@"):
        return text
    return None


def try_aclanthology(url: str) -> str | None:
    if "aclanthology.org" not in url:
        return None
    bib_url = url.rstrip("/") + ".bib"
    try:
        r = fetch(bib_url)
        if r.status_code == 200 and r.text.strip().startswith("@"):
            return r.text.strip()
    except Exception:
        pass
    return None


# ---------------------- DOI and CrossRef ----------------------


def doi_to_bibtex(doi: str) -> str | None:
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/x-bibtex"}
    try:
        r = fetch(url, headers=headers, allow_redirects=True)
        if r.status_code == 200 and r.text.strip().startswith("@"):
            return r.text.strip()
    except Exception:
        pass
    # fallback: CrossRef JSON -> build simple bib
    try:
        cr = fetch(
            f"https://api.crossref.org/works/{doi}",
            headers={"Accept": "application/json"},
        )
        if cr.status_code == 200:
            j = cr.json()
            item = j.get("message", {})
            bib = build_bib_from_crossref(item)
            if bib:
                return bib
    except Exception:
        pass
    return None


def build_bib_from_crossref(item: dict) -> str | None:
    if not item:
        return None
    typemap = {
        "journal-article": "@article",
        "book-chapter": "@incollection",
        "proceedings-article": "@inproceedings",
        "report": "@techreport",
        "book": "@book",
    }
    typ = typemap.get(item.get("type", ""), "@misc")
    authors = item.get("author", [])
    if authors:
        first = authors[0]
        lastname = first.get("family", "author").replace(" ", "")
    else:
        lastname = "anon"
    year = (item.get("issued", {}).get("date-parts", [[None]])[0][0]) or "n.d."
    title = item.get("title", [""])[0]
    key = (
        re.sub(
            r"\W+", "", (lastname + str(year) + (title.split()[0] if title else ""))
        )[:40]
        or "key"
    )
    bib = [f"{typ}{{{key},", f"  title = {{{title}}},"]
    if authors:
        astrings = []
        for a in authors:
            parts = []
            if a.get("given"):
                parts.append(a.get("given"))
            if a.get("family"):
                parts.append(a.get("family"))
            astrings.append(" ".join(parts))
        bib.append(f"  author = {{{' and '.join(astrings)}}},")
    container = item.get("container-title", [])
    if container:
        bib.append(f"  booktitle = {{{container[0]}}},")
    if year and year != "n.d.":
        bib.append(f"  year = {{{year}}},")
    doi = item.get("DOI")
    if doi:
        bib.append(f"  doi = {{{doi}}},")
    url = item.get("URL")
    if url:
        bib.append(f"  url = {{{url}}},")
    bib.append("}")
    return "\n".join(bib)


# ---------------------- Generic page heuristics ----------------------


def find_bibtex_blocks(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for tagname in ("pre", "textarea", "code"):
        for tag in soup.find_all(tagname):
            txt = tag.get_text().strip()
            if txt.startswith("@") and "@" in txt:
                candidates.append(txt)
    for div in soup.find_all("div"):
        cls = " ".join(div.get("class") or [])
        if "bib" in cls.lower() or div.get("id", "").lower().startswith("bib"):
            txt = div.get_text().strip()
            if txt.startswith("@"):
                candidates.append(txt)
    if candidates:
        return candidates[0]
    return None


def find_direct_bib_links(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".bib"):
            bib_url = urljoin(base_url, href)
            try:
                r = fetch(bib_url)
                if r.status_code == 200 and r.text.strip().startswith("@"):
                    return r.text.strip()
            except Exception:
                continue
    return None


def find_doi_on_page(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    m = soup.find("meta", attrs={"name": "citation_doi"})
    if m and m.get("content"):
        return m["content"].strip()
    m = soup.find("meta", attrs={"name": "DC.Identifier"})
    if m and m.get("content") and "doi.org" in m["content"]:
        return m["content"].split("doi.org/")[-1].strip()
    txt = soup.get_text(separator=" ").strip()
    doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", txt)
    if doi_match:
        return doi_match.group(0)
    for a in soup.find_all("a", href=True):
        if "doi.org/" in a["href"]:
            return a["href"].split("doi.org/")[-1].strip()
    return None


def build_bib_from_meta_tags(
    soup: BeautifulSoup, page_url: str, html_text: str
) -> str | None:
    title = None
    tmeta = soup.find("meta", attrs={"name": "citation_title"})
    if tmeta and tmeta.get("content"):
        title = tmeta["content"].strip()
    authors_tags = [
        tag.get("content").strip()
        for tag in soup.find_all("meta", attrs={"name": "citation_author"})
        if tag.get("content")
    ]
    author_field = " and ".join(authors_tags) if authors_tags else None
    venue = None
    for name in (
        "citation_conference_title",
        "citation_journal_title",
        "citation_publication_title",
        "citation_conference",
    ):
        m = soup.find("meta", attrs={"name": name})
        if m and m.get("content"):
            venue = m["content"].strip()
            break
    year = extract_year_from_meta_or_text(soup, html_text) or ""
    key = make_bibkey(author_field or "", year, title or "")
    entry_type = (
        "@inproceedings"
        if venue
        else (
            "@article"
            if soup.find("meta", attrs={"name": "citation_journal_title"})
            else "@misc"
        )
    )
    bib = [f"{entry_type}{{{key},", f"  title = {{{html.unescape(title or '')}}},"]
    if author_field:
        bib.append(f"  author = {{{author_field}}},")
    if venue:
        bib.append(f"  booktitle = {{{venue}}},")
    if year:
        bib.append(f"  year = {{{year}}},")
    # prefer the canonical page URL (not a found PDF link)
    bib.append(f"  url = {{{page_url}}},")
    # include DOI if present
    doi = None
    dm = soup.find("meta", attrs={"name": "citation_doi"})
    if dm and dm.get("content"):
        doi = dm["content"].strip()
        bib.append(f"  doi = {{{doi}}},")
    bib.append("}")
    return "\n".join(bib)


def generic_page_attempt(url: str) -> str | None:
    try:
        r = fetch(url)
        r.raise_for_status()
    except Exception:
        return None
    html_text = r.text
    # 1) direct .bib links
    bib = find_direct_bib_links(html_text, url)
    if bib:
        return bib
    # 2) bibtex blocks
    bib = find_bibtex_blocks(html_text)
    if bib:
        return bib
    soup = BeautifulSoup(html_text, "html.parser")
    # 3) Prefer meta-based construction (OpenReview, modern pages)
    meta_bib = build_bib_from_meta_tags(soup, url, html_text)
    if meta_bib:
        return meta_bib
    # 4) DOI -> try DOI content-negotiation
    doi = find_doi_on_page(html_text)
    if doi:
        bib = doi_to_bibtex(doi)
        if bib:
            return bib
    # 5) look for 'BibTeX' links
    for a in soup.find_all(
        "a", string=re.compile(r"BibTeX|bibtex|BibTex", re.I), href=True
    ):
        bib_url = urljoin(url, a["href"])
        try:
            r2 = fetch(bib_url)
            if r2.status_code == 200 and r2.text.strip().startswith("@"):
                return r2.text.strip()
            t = find_bibtex_blocks(r2.text)
            if t:
                return t
        except Exception:
            continue
    # 6) Try appending .bib
    try:
        r2 = fetch(url + ".bib")
        if r2.status_code == 200 and r2.text.strip().startswith("@"):
            return r2.text.strip()
    except Exception:
        pass
    # 7) fallback: try DOI-only in url
    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", url)
    if doi_match:
        doi = doi_match.group(0)
        result = doi_to_bibtex(doi)
        if result:
            return result
    return None


# ---------------------- Orchestration ----------------------


def get_bibtex_from_url(url: str) -> str | None:
    print(f"[INFO] Trying URL: {url}")
    # 1) arXiv
    result = try_arxiv(url)
    if result:
        print("[INFO] Found arXiv bibtex.")
        return result
    # 2) ACL Anthology
    result = try_aclanthology(url)
    if result:
        print("[INFO] Found ACL Anthology .bib endpoint.")
        return result
    # 3) Generic
    result = generic_page_attempt(url)
    if result:
        print("[INFO] Found bibtex via generic scraping/DOI/meta.")
        return result
    # 4) try DOI in the raw URL
    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", url)
    if doi_match:
        doi = doi_match.group(0)
        result = doi_to_bibtex(doi)
        if result:
            print("[INFO] Found bibtex via DOI.")
            return result
    # last resort: try append .bib
    try:
        r = fetch(url + ".bib")
        if r.status_code == 200 and r.text.strip().startswith("@"):
            print("[INFO] Found .bib by appending .bib")
            return r.text.strip()
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Fetch BibTeX for a given paper URL (arXiv, ACL Anthology, NeurIPS, ICML, ICLR, OpenReview, etc.)"
    )
    parser.add_argument("url", help="paper URL")
    args = parser.parse_args()

    url = args.url
    print(f"[INFO] Trying to fetch BibTeX for: {url}")
    bib = get_bibtex_from_url(url)
    if bib:
        print("\n--- BibTeX ---\n")
        print(bib)
    else:
        print("[ERROR] Could not find BibTeX automatically for this URL.")
        print("Suggestions:")
        print(
            " - If this is arXiv, try the /bibtex endpoint (https://arxiv.org/bibtex/<id>)"
        )
        print(" - If ACL Anthology, append .bib to the URL")
        print(" - If the site uses DOI, ensure the DOI is present on the page")
        print(
            " - As a last resort, you can create BibTeX manually or provide the DOI/identifier."
        )


if __name__ == "__main__":
    main()
