import time
import re
import html
import urllib.parse
import warnings
warnings.filterwarnings("ignore", ".*duckduckgo_search.*")

# --- Optional dependencies ---
_have_ddg = False
_have_httpx = False
_have_fake_useragent = False
_have_readability = False
_have_newspaper = False
_have_bs4 = False
_have_requests = False

try:
    from duckduckgo_search import DDGS
    _have_ddg = True
except ImportError:
    DDGS = None

try:
    import httpx
    _have_httpx = True
except ImportError:
    httpx = None

try:
    from fake_useragent import UserAgent as _UA
    _have_fake_useragent = True
except ImportError:
    _UA = None

try:
    from readability import Document
    _have_readability = True
except ImportError:
    Document = None

try:
    from newspaper import Article
    _have_newspaper = True
except ImportError:
    Article = None

try:
    from bs4 import BeautifulSoup
    _have_bs4 = True
except ImportError:
    BeautifulSoup = None

try:
    import requests
    _have_requests = True
except ImportError:
    requests = None

_DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def _get_ua():
    if _have_fake_useragent:
        try:
            return str(_UA().random)
        except Exception:
            pass
    return _DEFAULT_UA


def _get_url(entry):
    for key in ("href", "link", "url"):
        val = entry.get(key)
        if val:
            return val
    return ""


def _resolve_ddg_url(raw_url):
    if not raw_url:
        return ""
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    parsed = urllib.parse.urlparse(raw_url)
    if "duckduckgo.com" in parsed.netloc and parsed.query:
        qs = urllib.parse.parse_qs(parsed.query)
        if "uddg" in qs:
            return qs["uddg"][0]
    return raw_url


# ---- 1. Web Search ----

def search_web(query, max_results=10):
    try:
        if _have_ddg:
            results = list(DDGS().text(query, max_results=max_results))
            if results:
                return [
                    {
                        "title": r.get("title", ""),
                        "url": _get_url(r),
                        "snippet": r.get("body", ""),
                        "source": "duckduckgo",
                    }
                    for r in results
                ]
    except Exception as ddg_err:
        pass

    try:
        if not _have_requests or not _have_bs4:
            raise ImportError("requests or bs4 not available")
        url = f"https://html.duckduckgo.com/html/?q={query}"
        resp = requests.get(
            url,
            headers={"User-Agent": _get_ua()},
            timeout=10,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result")[:max_results]:
            title_el = r.select_one(".result__title a")
            snippet_el = r.select_one(".result__snippet")
            if title_el:
                raw_url = title_el.get("href", "")
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": _resolve_ddg_url(raw_url),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    "source": "duckduckgo_html",
                })
        if results:
            return results
    except Exception as bs_err:
        pass

    return {"error": "Web search unavailable — no search libraries available or all backends failed"}


# ---- 2. Image Search ----

def search_images(query, max_results=9):
    try:
        if _have_ddg:
            results = list(DDGS().images(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("image", ""),
                    "thumbnail": r.get("thumbnail", ""),
                    "source": r.get("source", ""),
                    "width": r.get("width"),
                    "height": r.get("height"),
                }
                for r in results
            ]
    except Exception as e:
        return {"error": f"Image search failed: {str(e)}"}
    return {"error": "Image search unavailable — duckduckgo_search not installed"}


# ---- 3. News Search ----

def search_news(query, max_results=10):
    try:
        if _have_ddg:
            results = list(DDGS().news(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                }
                for r in results
            ]
    except Exception as e:
        return {"error": f"News search failed: {str(e)}"}
    return {"error": "News search unavailable — duckduckgo_search not installed"}


# ---- 4. Video Search ----

def search_videos(query, max_results=6):
    try:
        if _have_ddg:
            results = list(DDGS().videos(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("content", ""),
                    "thumbnail": r.get("thumbnail", ""),
                    "duration": r.get("duration", ""),
                    "platform": r.get("source", ""),
                    "views": r.get("views", ""),
                }
                for r in results
            ]
    except Exception as e:
        return {"error": f"Video search failed: {str(e)}"}
    return {"error": "Video search unavailable — duckduckgo_search not installed"}


# ---- 5. Content Extraction ----

def _extract_text_from_html(html_content):
    if _have_bs4:
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except Exception:
            pass
    text = re.sub(r"<[^>]+>", " ", html_content)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_content(url):
    start = time.time()
    html_content = None
    title = ""
    author = ""
    publish_date = ""

    try:
        if _have_httpx:
            headers = {
                "User-Agent": _get_ua(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=15)
            resp.raise_for_status()
            html_content = resp.text
    except Exception:
        pass

    if not html_content and _have_requests:
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": _get_ua()},
                timeout=15,
            )
            resp.raise_for_status()
            html_content = resp.text
        except Exception:
            pass

    if not html_content:
        return {"error": f"Could not fetch URL: {url}", "url": url, "success": False}

    content = ""
    if _have_readability:
        try:
            doc = Document(html_content)
            content_html = doc.summary()
            title = doc.title() or ""
            content = _extract_text_from_html(content_html)
        except Exception:
            pass

    if not content and _have_newspaper:
        try:
            article = Article(url)
            article.download()
            article.parse()
            content = article.text or ""
            title = article.title or title
            author = ", ".join(article.authors) if article.authors else ""
            publish_date = (
                article.publish_date.isoformat()
                if article.publish_date
                else ""
            )
        except Exception:
            pass

    if not content and html_content:
        content = _extract_text_from_html(html_content)

    if not content:
        return {"error": "Could not extract content from page", "url": url, "success": False}

    words = content.split()
    elapsed = round(time.time() - start, 2)

    return {
        "title": title,
        "content": content,
        "author": author,
        "publish_date": publish_date,
        "word_count": len(words),
        "url": url,
        "success": True,
        "extract_time_seconds": elapsed,
    }


# ---- 6. Research Pipeline ----

def _split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _extractive_summary(text, max_chars):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    sentences = []
    for p in paragraphs:
        first_sent = _split_sentences(p)
        if first_sent:
            sentences.append(first_sent[0])
    summary = " ".join(sentences)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 3] + "..."
    return summary


def _extract_key_points(text, max_points=6):
    sentences = _split_sentences(text)
    key_sentences = []
    for s in sentences:
        if len(s) > 40 and len(s) < 300:
            key_sentences.append(s)
        if len(key_sentences) >= max_points:
            break
    if len(key_sentences) < max_points and sentences:
        for s in sentences:
            if s not in key_sentences and len(s) < 400:
                key_sentences.append(s)
            if len(key_sentences) >= max_points:
                break
    return key_sentences[:max_points]


def _identify_sub_questions(text):
    sentences = _split_sentences(text)
    topics = []
    for s in sentences:
        lowered = s.lower()
        if any(kw in lowered for kw in ["such as", "including", "for example", "like "]):
            topics.append(s)
        if any(q in lowered for q in ["what is", "how does", "why do", "what are", "who is"]):
            topics.append(s)
    seen = set()
    unique = []
    for t in topics:
        norm = t.lower()[:60]
        if norm not in seen:
            seen.add(norm)
            unique.append(t)
    return unique[:3]


def research_pipeline(topic, depth=2):
    start = time.time()
    depth = min(max(depth, 1), 3)

    result_count = 5 if depth == 1 else 10
    extract_count = 3 if depth == 1 else 5

    search_results = search_web(topic, max_results=result_count)
    if isinstance(search_results, dict) and "error" in search_results:
        return {
            "topic": topic,
            "depth": depth,
            "sources": [],
            "summary": f"Research failed: {search_results['error']}",
            "key_points": [],
            "research_time_seconds": round(time.time() - start, 2),
            "source_count": 0,
        }

    sources_data = []
    extracted = []
    for r in search_results[:extract_count]:
        url = r.get("url", "")
        if url:
            result = extract_content(url)
            if isinstance(result, dict) and result.get("success"):
                sources_data.append({
                    "title": result.get("title", r.get("title", "")),
                    "url": url,
                    "word_count": result.get("word_count", 0),
                })
                extracted.append(result.get("content", ""))

    all_text = " ".join(extracted)
    max_summary_chars = {1: 500, 2: 1500, 3: 3000}
    summary = _extractive_summary(all_text, max_summary_chars[depth])
    key_points = _extract_key_points(all_text, 6)

    result = {
        "topic": topic,
        "depth": depth,
        "sources": sources_data,
        "summary": summary,
        "key_points": key_points,
        "research_time_seconds": round(time.time() - start, 2),
        "source_count": len(sources_data),
    }

    if depth >= 3 and extracted:
        sub_questions = _identify_sub_questions(all_text)
        for sq in sub_questions:
            if len(result["sources"]) >= 15:
                break
            sub_results = search_web(sq, max_results=4)
            if isinstance(sub_results, list):
                for sr in sub_results[:3]:
                    sub_url = sr.get("url", "")
                    if sub_url and sub_url not in [s["url"] for s in result["sources"]]:
                        sub_extract = extract_content(sub_url)
                        if isinstance(sub_extract, dict) and sub_extract.get("success"):
                            result["sources"].append({
                                "title": sub_extract.get("title", sr.get("title", "")),
                                "url": sub_url,
                                "word_count": sub_extract.get("word_count", 0),
                            })
                            sub_content = sub_extract.get("content", "")
                            if sub_content:
                                sub_summary = _extractive_summary(sub_content, 800)
                                result["summary"] += "\n\n" + sub_summary
                            result["source_count"] = len(result["sources"])

        if len(result["summary"]) > 3000:
            result["summary"] = result["summary"][:2997] + "..."

        new_key_points = _extract_key_points(result["summary"], 6)
        if new_key_points:
            result["key_points"] = new_key_points

    result["research_time_seconds"] = round(time.time() - start, 2)
    return result


# ---- 7. Search and Synthesize ----

def search_and_synthesize(query):
    results = search_web(query, max_results=3)
    if isinstance(results, dict) and "error" in results:
        return {"query": query, "error": results["error"], "results": []}

    synthesized = []
    for r in results[:3]:
        url = r.get("url", "")
        content_snippet = ""
        if url:
            extracted = extract_content(url)
            if isinstance(extracted, dict) and extracted.get("success"):
                content = extracted.get("content", "")
                words = content.split()
                content_snippet = " ".join(words[:80])
                if len(words) > 80:
                    content_snippet += "..."
        synthesized.append({
            "title": r.get("title", ""),
            "url": url,
            "snippet": r.get("snippet", ""),
            "content_snippet": content_snippet,
        })

    return {"query": query, "results": synthesized}
