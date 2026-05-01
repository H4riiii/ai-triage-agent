import os 
from dotenv import load_dotenv
import chromadb
from google import genai
from google.genai import types
from models import TicketTriage
import json

load_dotenv()
client = genai.Client()

# --- HARDCODED MODEL ---
WORKING_MODEL = "gemini-3.1-flash-lite-preview"
print(f"Using hardcoded model: {WORKING_MODEL}")
# -----------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "chroma_db")

chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection = chroma_client.get_collection(name="support_corpus")

def retrieve_context(issue_text: str, company: str, n_results: int = 4) -> str:
    where_filter = None
    if company and str(company).lower() != "none" and str(company).strip() != "":
        where_filter={"company": str(company).lower()}

    try:
        results = collection.query(
            query_texts=[issue_text],
            n_results=n_results,
            where=where_filter
        )

        if results['documents'] and results['documents'][0]:
            return "\n\n---\n\n".join(results['documents'][0])
    except Exception as e:
        print(f"ChromaDB retrieval error: {e}")

    return "No relevant support documents found."

def triage_ticket(issue: str, subject: str, company: str) -> dict:
    context = retrieve_context(issue, company)

    prompt = f"""
    You are an automated Support Triage Agent for HackerRank, Claude, and Visa.
    Your strict objective is to resolve or escalate customer support tickets using ONLY the provided knowledge base.
    
    TICKET DETAILS:
    - Company: {company}
    - Subject: {subject}
    - Issue: {issue}
    
    SUPPORT KNOWLEDGE BASE:
    {context}
    
    RULES:
    1. Read the TICKET DETAILS and compare it to the SUPPORT KNOWLEDGE BASE.
    2. If the answer is clearly found in the knowledge base, draft a helpful `response` and set `status` to 'replied'.
    3. You MUST rely ONLY on the provided knowledge base. Do not use outside knowledge or hallucinate policies.
    4. ESCALATION: If the issue involves high-risk topics (billing disputes, severe bugs, fraud, account lockouts), or if the answer is NOT in the knowledge base, set `status` to 'escalated' and draft a response politely informing the user that their ticket has been routed to a human.
    5. If the Company is 'None', use context clues in the issue to determine the correct company and handling.
    """

    try:
        response = client.models.generate_content(
            model=WORKING_MODEL, 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TicketTriage,
                temperature=0.1
            )
        )
        return json.loads(response.text)
    
    except Exception as e:
        raise e