import os 
from dotenv import load_dotenv
import chromadb
import google.generativeai as genai
from models import TicketTriage
import json

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not set.")

genai.configure(api_key = api_key)

model = genai.GenerativeModel('gemini-2.5-flash')

chroma_client = chromadb.PersistentClient(path= "./chroma_db")
collection = chroma_client.get_collection(name = "support_corpus")

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

    context = retrieve_context(issue,company)

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
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=TicketTriage,
                temperature=0.1
            )
        )
        return json.loads(response.text)
    
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return{
            "status": "escalated",
            "request_type": "invalid",
            "product_area": "unknown",
            "response": "System error processing your request. Escalating to human support.",
            "justification": f"API Failure {str(e)}"
        }
    