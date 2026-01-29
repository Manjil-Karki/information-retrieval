import asyncio
import csv
import json
import random
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Set, List
from datetime import datetime

import httpx
from bs4 import BeautifulSoup, NavigableString

from src.core.config import (
    BASE_URL,
    ROBOTS_URL,
    HEADERS,
    DEPARTMENT_KEYWORDS,
    PERSONS_CSV,
    PUBLICATIONS_CSV,
    DATA_JSON,
    PERSON_CONCURRENCY,
    PUB_CONCURRENCY,
    MIN_DELAY,
    MAX_DELAY,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)s │ %(message)s",
)
log = logging.getLogger("crawler")


def normalize_url(url: str) -> str:
    return url.rstrip("/").lower()

def normalize_name(name: str) -> str:
    return name.lower().replace(".", "").replace(" ", "")

def parse_sitemap(xml: bytes) -> List[str]:
    root = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text for loc in root.findall(".//sm:loc", ns)]

def load_seen(csv_path: Path) -> Set[str]:
    if not csv_path.exists():
        return set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {normalize_url(r["url"]) for r in csv.DictReader(f)}

def append_csv(csv_path: Path, fieldnames: List[str], row: dict):
    exists = csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)

async def safe_fetch(client: httpx.AsyncClient, url: str):
    """Fetch URL safely, return None on any network/read error."""
    try:
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        r = await client.get(url, timeout=60)
        if r.status_code != 200:
            log.warning(f" Non-200 for {url}: {r.status_code}")
            return None
        return r
    except httpx.HTTPError as e:
        log.warning(f" HTTP error for {url}: {e}")
    except Exception as e:
        log.warning(f" Unexpected error for {url}: {e}")
    return None


async def crawl_persons(client: httpx.AsyncClient):
    seen = load_seen(PERSONS_CSV)
    new_count = 0

    robots = (await safe_fetch(client, ROBOTS_URL)).text
    sitemap_index = next(
        l.split(":", 1)[1].strip()
        for l in robots.splitlines()
        if l.lower().startswith("sitemap:")
    )

    xml = (await safe_fetch(client, sitemap_index)).content
    sitemaps = parse_sitemap(xml)
    persons_sitemap = next(s for s in sitemaps if "persons.xml" in s)

    xml = (await safe_fetch(client, persons_sitemap)).content
    person_urls = parse_sitemap(xml)

    sem = asyncio.Semaphore(PERSON_CONCURRENCY)

    async def handle(url):
        nonlocal new_count
        url = normalize_url(url)
        if url in seen:
            return

        async with sem:
            r = await safe_fetch(client, url)
            if r is None:
                append_csv(
                    PERSONS_CSV,
                    ["url", "name", "department", "interested"],
                    {"url": url, "name": "", "department": "", "interested": False},
                )
                seen.add(url)
                new_count += 1
                return

            soup = BeautifulSoup(r.text, "lxml")
            name_tag = soup.select_one("h1")
            name = name_tag.get_text(strip=True) if name_tag else ""

            org = soup.find("a", {"rel": "Organisation"})
            department = org.get_text(strip=True) if org else ""

            interested = any(k in department.lower() for k in DEPARTMENT_KEYWORDS)

            append_csv(
                PERSONS_CSV,
                ["url", "name", "department", "interested"],
                {
                    "url": url,
                    "name": name,
                    "department": department,
                    "interested": interested,
                },
            )

            seen.add(url)
            new_count += 1

    await asyncio.gather(*(handle(u) for u in person_urls))
    log.info(f" New persons appended: {new_count}")


def load_interested_persons() -> Set[str]:
    if not PERSONS_CSV.exists():
        return set()
    with open(PERSONS_CSV, newline="", encoding="utf-8") as f:
        return {
            normalize_name(r["name"])
            for r in csv.DictReader(f)
            if r["interested"] == "True"
        }

async def crawl_publications(client: httpx.AsyncClient):
    seen = load_seen(PUBLICATIONS_CSV)
    interested_persons = load_interested_persons()
    new_count = 0

    robots = (await safe_fetch(client, ROBOTS_URL)).text
    sitemap_index = next(
        l.split(":", 1)[1].strip()
        for l in robots.splitlines()
        if l.lower().startswith("sitemap:")
    )

    xml = (await safe_fetch(client, sitemap_index)).content
    sitemaps = parse_sitemap(xml)
    pubs_base = next(s for s in sitemaps if "publications.xml" in s)

    pub_sitemaps = [pubs_base] + [f"{pubs_base}?n={i}" for i in range(1, 17)]
    pub_urls = []

    for s in pub_sitemaps:
        xml = (await safe_fetch(client, s))
        if xml:
            pub_urls.extend(parse_sitemap(xml.content))

    sem = asyncio.Semaphore(PUB_CONCURRENCY)

    async def handle(url):
        nonlocal new_count
        url = normalize_url(url)
        if url in seen:
            return

        async with sem:
            r = await safe_fetch(client, url)
            if r is None:
                append_csv(PUBLICATIONS_CSV, ["url", "interested"], {"url": url, "interested": False})
                seen.add(url)
                new_count += 1
                return

            soup = BeautifulSoup(r.text, "lxml")
            block = soup.select_one("p.relations.persons")
            names = []

            if block:
                for node in block.children:
                    if isinstance(node, NavigableString):
                        names.extend([normalize_name(p) for p in node.split(",") if p.strip()])
                    elif node.name == "a":
                        names.append(normalize_name(node.get_text(strip=True)))

            interested = any(n in interested_persons for n in names)

            append_csv(PUBLICATIONS_CSV, ["url", "interested"], {"url": url, "interested": interested})
            seen.add(url)
            new_count += 1

    await asyncio.gather(*(handle(u) for u in pub_urls))
    log.info(f" New publications appended: {new_count}")

def extract_authors(soup):
    authors = []
    block = soup.select_one("p.relations.persons")
    if not block:
        return authors

    for node in block.children:
        if isinstance(node, NavigableString):
            for name in [p.strip() for p in node.split(",") if p.strip()]:
                authors.append({"name": name, "url": None})
        elif node.name == "a":
            href = node.get("href")
            authors.append({
                "name": node.get_text(strip=True),
                "url": href if href.startswith("http") else f"{BASE_URL}{href}",
            })
    return authors

def extract_citations(soup):
    tag = soup.select_one("div.metric.scopus-citations span.count")
    try:
        return int(tag.get_text(strip=True)) if tag else None
    except ValueError:
        return None

def extract_publication_details(soup):
    details = {}
    rows = soup.select("table.properties tr")
    for row in rows:
        k = row.select_one("th")
        v = row.select_one("td")
        if not k or not v:
            continue
        label = k.get_text(strip=True).lower()
        value = v.get_text(" ", strip=True)

        if label == "journal":
            details["journal"] = value
        elif label == "volume":
            details["volume"] = value
        elif label == "number of pages":
            details["pages"] = value
        elif label == "article number":
            details["article_number"] = value
        elif label == "dois":
            link = v.select_one("a[href*='doi.org']")
            details["doi"] = link.get_text(strip=True) if link else value
        elif label == "publication status":
            details["publication_date"] = value
        elif label == "early online date":
            details["early_online_date"] = value

    return details

async def populate_data_json(client: httpx.AsyncClient):
    data = {"publications": {}}
    if DATA_JSON.exists():
        data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    with open(PUBLICATIONS_CSV, newline="", encoding="utf-8") as f:
        interested_urls = [r["url"] for r in csv.DictReader(f) if r["interested"] == "True"]

    missing = [u for u in interested_urls if u not in data["publications"]]
    log.info(f" Publications to populate in JSON: {len(missing)}")

    for url in missing:
        r = await safe_fetch(client, url)
        if r is None:
            continue

        soup = BeautifulSoup(r.text, "lxml")
        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else "[no title]"

        abstract_tag = soup.select_one("div[class*='rendering_abstractportal'] .textblock")
        abstract = abstract_tag.get_text(strip=True) if abstract_tag else "[no abstract]"

        data["publications"][url] = {
            "url": url,
            "title": title,
            "abstract": abstract,
            "authors": extract_authors(soup),
            "citations_scopus": extract_citations(soup),
            **extract_publication_details(soup),
        }

        log.info(f" JSON populated: {title}")

    DATA_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

async def main():
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, http2=True, timeout=60) as client:
        await crawl_persons(client)
        await crawl_publications(client)
        await populate_data_json(client)

    log.info(" Incremental crawl finished")

if __name__ == "__main__":
    asyncio.run(main())
