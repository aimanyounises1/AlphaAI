from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def save_to_supabase(doc_id, request, response, system_prompt):
    data = {
        "doc_id": doc_id,
        "request": request,
        "response": response,
        "system_prompt": system_prompt
    }
    supabase.table("conversations").insert([data]).execute()
