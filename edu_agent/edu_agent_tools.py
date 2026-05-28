from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests

from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from pathlib import Path
import re
import json
from pypdf import PdfReader
PYPDF_AVAILABLE = True


load_dotenv(override=True)
pushover_token = os.getenv("pushover_token")
pushover_user = os.getenv("pushover_user")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

async def playwright_tool():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

def push(text: str):
    """send a push notification to a user"""
    requests.post(pushover_url, data = {"token" : pushover_token, "user" : pushover_user, "message" : text})
    return "success"

def get_file_tool():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


 
SERPER_API_KEY = os.getenv("SERPER_API_KEY") or os.getenv("SERPERDEV_API_KEY")
 
HOCHSCHULKOMPASS_URL = "https://www.hochschulkompass.de/en/study-in-germany/study-search/advanced-search.html"
DAAD_BASE = "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/result/"
 
 
def _serper_search(query: str, num: int = 10) -> list[dict]:
    """Raw Serper API call, returns list of organic results."""
    if not SERPER_API_KEY:
        raise EnvironmentError("SERPER_API_KEY not set in environment.")
    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("organic", [])


def _build_search_queries(profile: dict) -> list[str]:
    """
    Build targeted search queries from the student profile dict.
    Profile keys expected:
        degree_level, fields, language_pref, budget, cgpa, aps
    """
    degree = profile.get("degree_level", "Masters")
    fields = profile.get("fields", [profile.get("field_of_study", "Computer Science")])
    if isinstance(fields, str):
        fields = [fields]
    lang = profile.get("language_pref", "English")
    budget = profile.get("budget", "zero-fee")
 
    queries = []
    for field in fields[:3]:  # cap at 3 fields
        base = f"German public university {degree} {field}"
        if "english" in lang.lower():
            base += " English taught"
        if "zero" in str(budget).lower():
            base += " no tuition fee"
        queries.append(base + " site:daad.de OR site:hochschulkompass.de OR site:uni-assist.de")
        queries.append(f"{degree} {field} Germany admission requirements Pakistani students IELTS 2024 2025")
 
    return queries
 
 
def search_universities_for_profile(profile_json: str) -> str:
    """
    Main tool function. Accepts a JSON string of the student profile,
    runs multiple targeted searches, and returns a structured markdown report.
 
    Args:
        profile_json: JSON string with keys:
            degree_level, fields (list), language_pref, budget, cgpa, aps,
            ielts_score (optional)
 
    Returns:
        Markdown-formatted university recommendations with links.
    """
    try:
        profile = json.loads(profile_json)
    except json.JSONDecodeError:
        # Fallback: treat as plain text description
        profile = {"field_of_study": profile_json, "degree_level": "Masters"}
 
    queries = _build_search_queries(profile)
    all_results: list[dict] = []
 
    for q in queries:
        try:
            results = _serper_search(q, num=8)
            all_results.extend(results)
        except Exception as e:
            all_results.append({"title": f"Search error: {e}", "link": "", "snippet": ""})
 
    # Deduplicate by URL
    seen_links = set()
    unique_results = []
    for r in all_results:
        link = r.get("link", "")
        if link and link not in seen_links:
            seen_links.add(link)
            unique_results.append(r)
 
    # Prioritise official sources
    priority_domains = ["daad.de", "hochschulkompass.de", "uni-assist.de", ".uni-", "tu-", "fh-"]
    def priority_score(r):
        link = r.get("link", "").lower()
        return sum(1 for d in priority_domains if d in link)
 
    unique_results.sort(key=priority_score, reverse=True)
    top_results = unique_results[:15]
 
    # Format output
    degree = profile.get("degree_level", "Masters")
    fields = profile.get("fields", [profile.get("field_of_study", "the requested field")])
    if isinstance(fields, str):
        fields = [fields]
 
    lines = [
        f"## 🎓 University Matches — {degree} in {' / '.join(fields)}",
        "",
        f"*Based on: {profile.get('language_pref', 'English')}-taught | "
        f"Budget: {profile.get('budget', 'flexible')} | "
        f"CGPA: {profile.get('cgpa', 'N/A')}*",
        "",
        "---",
        "",
    ]
 
    for i, r in enumerate(top_results, 1):
        title = r.get("title", "Untitled")
        link = r.get("link", "#")
        snippet = r.get("snippet", "")
        lines.append(f"### {i}. [{title}]({link})")
        if snippet:
            lines.append(f"> {snippet}")
        lines.append("")
 
    lines += [
        "---",
        "",
        "**Next steps:**",
        "1. Check APS certificate status before applying → https://aps-southasia.de",
        "2. Apply via uni-assist for most programs → https://www.uni-assist.de",
        "3. Check DoSV for Medicine/Pharmacy/Psychology → https://hochschulstart.de",
        "4. Explore DAAD scholarships → https://www.daad.de/en/study-and-research-in-germany/scholarships/",
    ]
 
    return "\n".join(lines)
 
 
def get_university_search_tool() -> Tool:
    return Tool(
        name="search_universities",
        func=search_universities_for_profile,
        description=(
            "Search for German universities matching a student's profile. "
            "Call this IMMEDIATELY after the student confirms their profile summary is correct. "
            "Input must be a JSON string with keys: degree_level, fields (list of strings), "
            "language_pref, budget, cgpa, aps, ielts_score. "
            "Example: '{\"degree_level\": \"Masters\", \"fields\": [\"AI\", \"Cybersecurity\"], "
            "\"language_pref\": \"English\", \"budget\": \"zero-fee\", \"cgpa\": \"3.2/4.0\", "
            "\"aps\": true, \"ielts_score\": \"6.5\"}'"
        ),
    )

SANDBOX_DIR = Path("sandbox")
 
 
def read_pdf_from_sandbox(filename: str) -> str:
    """
    Reads a PDF from the sandbox/ directory and returns extracted text.
    Useful when a student says their document is saved locally and provides a filename.
 
    Args:
        filename: Just the filename (e.g. "transcript.pdf") or relative path
                  within sandbox/ (e.g. "docs/ielts.pdf")
 
    Returns:
        Extracted plain text from the PDF, or an error message.
    """
    if not PYPDF_AVAILABLE:
        return (
            "❌ PDF reading is not available. Please install pypdf:\n"
            "  pip install pypdf\n"
            "Then restart the agent."
        )
 
    # Sanitise path — no traversal outside sandbox
    safe_name = Path(filename).name  # strips any directory components
    target = SANDBOX_DIR / safe_name
 
    if not target.exists():
        # Try with the full relative path but still confined to sandbox
        target_alt = (SANDBOX_DIR / filename).resolve()
        sandbox_resolved = SANDBOX_DIR.resolve()
        if str(target_alt).startswith(str(sandbox_resolved)) and target_alt.exists():
            target = target_alt
        else:
            available = [f.name for f in SANDBOX_DIR.glob("**/*.pdf")] if SANDBOX_DIR.exists() else []
            hint = f"\nAvailable PDFs in sandbox: {available}" if available else "\nNo PDFs found in sandbox/ folder."
            return f"❌ File not found: sandbox/{filename}{hint}"
 
    try:
        reader = PdfReader(str(target))
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(f"[Page {i+1}]\n{text.strip()}")
 
        if not pages_text:
            return f"⚠️ PDF '{filename}' was found but no text could be extracted (may be a scanned image). Try uploading a text-based PDF."
 
        full_text = "\n\n".join(pages_text)
        # Cap at ~4000 chars to avoid flooding context
        if len(full_text) > 4000:
            full_text = full_text[:4000] + f"\n\n... [truncated — {len(reader.pages)} pages total]"
 
        return f"📄 Contents of '{filename}':\n\n{full_text}"
 
    except Exception as e:
        return f"❌ Error reading PDF '{filename}': {e}"


def get_pdf_reader_tool() -> Tool:
    return Tool(
        name="read_pdf_from_sandbox",
        func=read_pdf_from_sandbox,
        description=(
            "Read a PDF document from the local sandbox/ folder. "
            "Use this when a student says they have a document saved locally and provides a filename. "
            "Input: just the filename, e.g. 'transcript.pdf' or 'docs/ielts_certificate.pdf'. "
            "Returns the extracted text content of the document."
        ),
    )

async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="use this tool to send a push notification to a user when needed")
    file_tools = get_file_tool()

    tool_search = Tool(
        name="Search",
        func=serper.run,
        description="useful for when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()

    return file_tools + [push_tool, tool_search, wiki_tool, python_repl]


def get_edu_extra_tools() -> list[Tool]:
    """
    Returns all extra EduAgent tools ready to be merged with your existing tool list.
 
    Usage in edu_agent.py:
        from edu_tools import get_edu_extra_tools
        extra = get_edu_extra_tools()
        all_tools = existing_tools + extra
    """
    tools = [
        get_university_search_tool(),
        get_pdf_reader_tool(),
    ]
    return tools