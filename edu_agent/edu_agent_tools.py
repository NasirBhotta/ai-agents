from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from pydantic import BaseModel, Field
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
from datetime import datetime
from langchain_core.tools import StructuredTool

PYPDF_AVAILABLE = True


load_dotenv(override=True)
pushover_token = os.getenv("pushover_token")
pushover_user = os.getenv("pushover_user")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()


class UpdateStudentprofileInput(BaseModel):
    update_json: str = Field(description="JSON string containing profile updates")

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


 
# SERPER_API_KEY = os.getenv("SERPER_API_KEY") or os.getenv("SERPERDEV_API_KEY")
 
HOCHSCHULKOMPASS_URL = "https://www.hochschulkompass.de/en/study-in-germany/study-search/advanced-search.html"
DAAD_BASE = "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/result/"
SANDBOX_DIR = Path("sandbox")

PROFILE_PATH = SANDBOX_DIR / "student_profile.json"
SERPER_API_KEY = os.getenv("SERPER_API_KEY") or os.getenv("SERPERDEV_API_KEY")
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  PROFILE SCHEMA — mirrors the future Supabase row exactly
#  When you integrate Supabase, swap _save_profile() with a supabase.upsert()
# ─────────────────────────────────────────────────────────────────────────────
 
def _empty_profile() -> dict:
    """Returns a blank profile matching the Supabase schema."""
    return {
        # ── Identity (Supabase will auto-generate id/timestamps) ──
        "id": "local-session-001",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "user_id": None,                        # populated when auth is added
 
        # ── Core profile fields ──
        "degree_level": None,                   # "Masters" | "Bachelors"
        "fields": [],                           # ["AI", "Cybersecurity", "Data Science"]
        "language_pref": None,                  # "English" | "German" | "Both"
        "budget": None,                         # "zero-fee" | "flexible"
        "cgpa": None,                           # "3.23/4.0" | "78%"
        "aps_certificate": None,                # true | false
 
        # ── Document status ──
        "documents": {
            "matric": False,
            "fsc": False,
            "bachelors_degree": False,
            "bachelors_transcripts": False,
            "cv": False,
            "ielts_certificate": False,
            "ielts_score": None,                # "6.5" | null
            "work_experience": False,
        },
 
        # ── Extracted doc data (populated by read_and_extract_pdf) ──
        "extracted_docs": {},
 
        # ── University search results (populated by search_universities) ──
        "university_results": None,
 
        # ── Full chat history (managed by agent executor separately) ──
        "chat_history": [],
    }
 
 
def _load_profile() -> dict:
    """Load profile from sandbox/student_profile.json, or return empty profile."""
    SANDBOX_DIR.mkdir(exist_ok=True)
    if PROFILE_PATH.exists():
        try:
            with open(PROFILE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return _empty_profile()
 
 
def _save_profile(profile: dict) -> None:
    """Save profile to sandbox/student_profile.json."""
    SANDBOX_DIR.mkdir(exist_ok=True)
    profile["updated_at"] = datetime.now().isoformat()
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  1. UPDATE STUDENT PROFILE
# ─────────────────────────────────────────────────────────────────────────────
 
def update_student_profile(updates_json: str) -> str:
    """
    Merge new data into the student profile and save it.
    Call this after EVERY interview answer to keep the profile up to date.
 
    Args:
        updates_json: JSON string of fields to update. Only include changed fields.
 
        Top-level field examples:
          {"degree_level": "Masters"}
          {"fields": ["AI", "Cybersecurity"]}
          {"cgpa": "3.23/4.0", "aps_certificate": true}
          {"language_pref": "English", "budget": "zero-fee"}
 
        To update nested documents object, use "documents" key:
          {"documents": {"matric": true, "ielts_certificate": true, "ielts_score": "6.5"}}
 
        To update extracted_docs, use "extracted_docs" key:
          {"extracted_docs": {"ielts_certificate": {"overall_band": "6.5", ...}}}
 
    Returns:
        Confirmation string with the updated profile summary.
    """
    try:
        updates = json.loads(updates_json)
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON: {e}"
 
    profile = _load_profile()
 
    # Deep merge for nested dicts (documents, extracted_docs)
    for key, value in updates.items():
        if key in ("documents", "extracted_docs") and isinstance(value, dict):
            profile[key] = {**profile.get(key, {}), **value}
        else:
            profile[key] = value
 
    _save_profile(profile)
 
    # Return a clean confirmation
    summary_fields = {
        "degree_level": profile.get("degree_level"),
        "fields": profile.get("fields"),
        "language_pref": profile.get("language_pref"),
        "budget": profile.get("budget"),
        "cgpa": profile.get("cgpa"),
        "aps_certificate": profile.get("aps_certificate"),
        "documents": profile.get("documents"),
    }
    return f"✅ Profile updated and saved.\nCurrent profile:\n{json.dumps(summary_fields, indent=2)}"
 
 
def get_update_profile_tool() -> Tool:
    return StructuredTool(
        name="update_student_profile",
        func=update_student_profile,
        description=(
            "Save or update the student's profile data to sandbox/student_profile.json. "
            "Call this after EVERY interview answer as soon as a field is collected. "
            "Input: a JSON string of only the fields that changed. "
            "For nested fields use 'documents' or 'extracted_docs' as the key. "
            "Examples: "
            "'{\"degree_level\": \"Masters\"}' "
            "'{\"fields\": [\"AI\", \"Cybersecurity\"]}' "
            "'{\"documents\": {\"matric\": true}}' "
            "'{\"cgpa\": \"3.23/4.0\", \"aps_certificate\": true}'"
        ),
        args_schema=UpdateStudentprofileInput
    )
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  2. GET STUDENT PROFILE
# ─────────────────────────────────────────────────────────────────────────────
 
def get_student_profile(_: str = "") -> str:
    """
    Read the current student profile from sandbox/student_profile.json.
    Use this when you need to recall what has been collected so far,
    or when building the university search input.
 
    Returns:
        The full profile as a formatted JSON string.
    """
    profile = _load_profile()
    return json.dumps(profile, indent=2)
 
 
def get_read_profile_tool() -> Tool:
    return Tool(
        name="get_student_profile",
        func=get_student_profile,
        description=(
            "Read the current student profile from sandbox/student_profile.json. "
            "Use this to recall collected data at any point, or before calling search_universities "
            "to build the input JSON from saved profile data. "
            "Input: empty string (no input needed)."
        ),
    )
 

 
def _serper_search(query: str, num: int = 10) -> list[dict]:
    if not SERPER_API_KEY:
        raise EnvironmentError("SERPER_API_KEY not set in environment.")
    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("organic", [])
 
 
def _build_search_queries(profile: dict) -> list[str]:
    degree = profile.get("degree_level", "Masters")
    fields = profile.get("fields", [profile.get("field_of_study", "Computer Science")])
    if isinstance(fields, str):
        fields = [fields]
    lang = profile.get("language_pref", "English")
    budget = profile.get("budget", "zero-fee")
 
    queries = []
    for field in fields[:3]:
        base = f"German public university {degree} {field}"
        if "english" in lang.lower():
            base += " English taught"
        if "zero" in str(budget).lower():
            base += " no tuition fee"
        queries.append(base + " site:daad.de OR site:hochschulkompass.de OR site:uni-assist.de")
        queries.append(f"{degree} {field} Germany admission requirements Pakistani students IELTS 2025 2026")
    return queries
 
 
def search_universities_for_profile(profile_json: str) -> str:
    """
    Search for German universities matching the student profile.
    Saves results into the profile JSON under 'university_results'.
 
    Args:
        profile_json: JSON string with keys from the student profile,
                      OR pass empty string "" to auto-load from saved profile.
    """
    # Auto-load from saved profile if no input given
    if not profile_json.strip() or profile_json.strip() == '""':
        profile = _load_profile()
    else:
        try:
            profile = json.loads(profile_json)
        except json.JSONDecodeError:
            profile = _load_profile()
 
    queries = _build_search_queries(profile)
    all_results: list[dict] = []
 
    for q in queries:
        try:
            results = _serper_search(q, num=8)
            all_results.extend(results)
        except Exception as e:
            all_results.append({"title": f"Search error: {e}", "link": "", "snippet": ""})
 
    # Deduplicate
    seen_links = set()
    unique_results = []
    for r in all_results:
        link = r.get("link", "")
        if link and link not in seen_links:
            seen_links.add(link)
            unique_results.append(r)
 
    # Prioritise official sources
    priority_domains = ["daad.de", "hochschulkompass.de", "uni-assist.de", ".uni-", "tu-", "fh-"]
    unique_results.sort(
        key=lambda r: sum(1 for d in priority_domains if d in r.get("link", "").lower()),
        reverse=True,
    )
    top_results = unique_results[:15]
 
    # Save results into profile JSON
    saved_results = [
        {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")}
        for r in top_results
    ]
    profile_stored = _load_profile()
    profile_stored["university_results"] = {
        "searched_at": datetime.now().isoformat(),
        "query_profile": {
            "degree_level": profile.get("degree_level"),
            "fields": profile.get("fields"),
            "language_pref": profile.get("language_pref"),
            "budget": profile.get("budget"),
            "cgpa": profile.get("cgpa"),
        },
        "results": saved_results,
    }
    _save_profile(profile_stored)
 
    # Format markdown output for the user
    degree = profile.get("degree_level", "Masters")
    fields = profile.get("fields", [profile.get("field_of_study", "the requested field")])
    if isinstance(fields, str):
        fields = [fields]
 
    lines = [
        f"## 🎓 University Matches — {degree} in {' / '.join(fields)}",
        "",
        f"*{profile.get('language_pref', 'English')}-taught | "
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
        "**Next steps:**",
        "1. APS certificate → https://aps-southasia.de",
        "2. Apply via uni-assist → https://www.uni-assist.de",
        "3. DoSV (Medicine/Pharmacy/Psychology) → https://hochschulstart.de",
        "4. DAAD scholarships → https://www.daad.de/en/study-and-research-in-germany/scholarships/",
        "",
        "*Results saved to your profile.*",
    ]
    return "\n".join(lines)
 
 
def get_university_search_tool() -> Tool:
    return Tool(
        name="search_universities",
        func=search_universities_for_profile,
        description=(
            "Search for German universities matching the student profile. "
            "Call this IMMEDIATELY after the student confirms their profile summary is correct. "
            "Pass empty string to auto-load from saved profile, or pass a JSON string with keys: "
            "degree_level, fields (list), language_pref, budget, cgpa, aps_certificate, ielts_score. "
            "Results are automatically saved into sandbox/student_profile.json under 'university_results'."
        ),
    )
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  4. READ AND EXTRACT PDF
# ─────────────────────────────────────────────────────────────────────────────
 
# Field extraction prompts per document type — the LLM uses these to know what to pull out
PDF_EXTRACTION_SCHEMAS = {
    "ielts": {
        "candidate_name": "string",
        "overall_band": "string e.g. '6.5'",
        "listening": "string",
        "reading": "string",
        "writing": "string",
        "speaking": "string",
        "issue_date": "string YYYY-MM-DD",
        "expiry_date": "string YYYY-MM-DD",
        "test_centre": "string",
    },
    "transcript": {
        "institution": "string",
        "degree": "string",
        "cgpa": "string e.g. '3.23/4.0'",
        "graduation_year": "string",
        "student_name": "string",
    },
    "degree_certificate": {
        "institution": "string",
        "degree_title": "string",
        "student_name": "string",
        "award_date": "string YYYY-MM-DD",
        "result": "string e.g. 'First Class'",
    },
    "matric": {
        "institution": "string",
        "student_name": "string",
        "year": "string",
        "total_marks": "string",
        "obtained_marks": "string",
        "percentage": "string",
        "board": "string e.g. 'BISE Lahore'",
    },
    "cv": {
        "candidate_name": "string",
        "email": "string",
        "education": "list of degree entries",
        "work_experience": "list of job entries with company, role, duration",
        "skills": "list",
    },
    "default": {
        "document_type": "string — best guess of what this document is",
        "key_information": "string — most important information found",
        "dates": "list of any dates found",
        "names": "list of any names found",
        "numbers": "list of any important numbers or scores",
    },
}
 
 
def _detect_doc_type(filename: str, text_preview: str) -> str:
    """Guess document type from filename and first 500 chars of text."""
    combined = (filename + " " + text_preview).lower()
    if any(k in combined for k in ["ielts", "british council", "idp", "band score"]):
        return "ielts"
    if any(k in combined for k in ["transcript", "grades", "semester", "cgpa", "gpa"]):
        return "transcript"
    if any(k in combined for k in ["degree", "bachelor", "master", "awarded", "conferred"]):
        return "degree_certificate"
    if any(k in combined for k in ["matric", "secondary", "ssc", "bise", "board"]):
        return "matric"
    if any(k in combined for k in ["cv", "resume", "curriculum vitae", "experience", "skills"]):
        return "cv"
    return "default"
 
 
def read_and_extract_pdf(input_json: str) -> str:
    """
    Read a PDF from sandbox/, extract structured fields, and save them
    into sandbox/student_profile.json under 'extracted_docs'.
 
    Args:
        input_json: JSON string with:
          - "filename": required — e.g. "transcript.pdf"
          - "doc_key":  optional — key to store under in extracted_docs
                        e.g. "bachelors_transcript", "ielts_certificate"
                        If omitted, auto-detected from filename.
 
        Example: '{"filename": "ielts.pdf", "doc_key": "ielts_certificate"}'
 
    Returns:
        Extracted structured data as JSON string + confirmation it was saved.
    """
    if not PYPDF_AVAILABLE:
        return (
            "❌ PDF reading unavailable. Install with: pip install pypdf"
        )
 
    # Parse input
    try:
        inp = json.loads(input_json)
        filename = inp.get("filename", input_json)  # fallback: treat whole string as filename
        doc_key = inp.get("doc_key", None)
    except (json.JSONDecodeError, AttributeError):
        filename = input_json.strip().strip('"')
        doc_key = None
 
    # Locate file safely within sandbox
    safe_name = Path(filename).name
    target = SANDBOX_DIR / safe_name
    if not target.exists():
        target_alt = (SANDBOX_DIR / filename).resolve()
        sandbox_resolved = SANDBOX_DIR.resolve()
        if str(target_alt).startswith(str(sandbox_resolved)) and target_alt.exists():
            target = target_alt
        else:
            available = [f.name for f in SANDBOX_DIR.glob("**/*.pdf")] if SANDBOX_DIR.exists() else []
            return f"❌ File not found: sandbox/{filename}. Available PDFs: {available}"
 
    # Extract text
    try:
        reader = PdfReader(str(target))
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(text.strip())
        full_text = "\n\n".join(pages_text)
    except Exception as e:
        return f"❌ Error reading PDF: {e}"
 
    if not full_text.strip():
        return f"⚠️ No text could be extracted from '{filename}' — may be a scanned image PDF."
 
    # Detect document type
    doc_type = _detect_doc_type(filename, full_text[:500])
    schema = PDF_EXTRACTION_SCHEMAS.get(doc_type, PDF_EXTRACTION_SCHEMAS["default"])
 
    # Auto-set doc_key if not provided
    if not doc_key:
        doc_key = doc_type if doc_type != "default" else Path(filename).stem
 
    # Build structured extraction result
    # The agent LLM will naturally extract these fields from the text
    # because we return the text + the schema it should fill — the agent
    # does the extraction as part of its reasoning before calling update_student_profile
    extraction_prompt_hint = (
        f"\n\n📋 DOCUMENT TYPE DETECTED: {doc_type.upper()}\n"
        f"Please extract the following fields from the text above and call "
        f"update_student_profile with:\n"
        f'{{"extracted_docs": {{"{doc_key}": {json.dumps(schema, indent=2)}}}}}\n'
        f"Fill in the actual values from the document. Use null for any field not found."
    )
 
    # Cap text to avoid flooding context
    display_text = full_text[:3000] + (f"\n...[truncated]" if len(full_text) > 3000 else "")
 
    return (
        f"📄 Contents of '{filename}':\n\n"
        f"{display_text}"
        f"{extraction_prompt_hint}"
    )
 
 
def get_pdf_reader_tool() -> Tool:
    return Tool(
        name="read_and_extract_pdf",
        func=read_and_extract_pdf,
        description=(
            "Read a PDF from sandbox/ folder, extract structured fields, and save them "
            "into the student profile JSON. Use when a student mentions a document filename. "
            "Input: JSON string with 'filename' and optional 'doc_key'. "
            "Examples: "
            "'{\"filename\": \"ielts.pdf\", \"doc_key\": \"ielts_certificate\"}' "
            "'{\"filename\": \"transcript.pdf\", \"doc_key\": \"bachelors_transcript\"}' "
            "After this tool returns, call update_student_profile to save the extracted fields."
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
        get_update_profile_tool(),
        get_read_profile_tool(),
        get_university_search_tool(),
        get_pdf_reader_tool(),
    ]
    return tools