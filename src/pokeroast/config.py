import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    # 1. Try Local Environment (.env) FIRST (Prevents local crashes)
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key: return key

    # 2. Try Streamlit Secrets (Cloud) SECOND
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except:
        pass

    # 3. Stop if missing
    st.error("❌ CRITICAL: GOOGLE_API_KEY is missing. Add it to .env (local) or Streamlit Secrets (Cloud).")
    st.stop()

def get_model_candidates():
    """
    Returns a list of models to try in order.
    """
    # 1. Get string from Env or Secrets
    env_models = os.getenv("GEMINI_MODELS")
    if not env_models:
        try:
            env_models = st.secrets.get("GEMINI_MODELS")
        except:
            pass

    # 2. Process the list or use Defaults
    if env_models:
        raw_list = [m.strip() for m in env_models.split(',') if m.strip()]
    else:
        # FAILSAFE: Based on your debug logs, these are the models YOU have access to.
        # We put 2.0-flash FIRST because 2.5 has a tiny quota limit (20/day).
        raw_list = [
            "gemini-2.0-flash",       # High quota, stable
            "gemini-2.0-flash-lite",  # High quota, fast
            "gemini-2.5-flash",       # Low quota (20/day), good backup
            "gemini-exp-1206"         # Experimental backup
        ]

    # 3. Cleanup: Strip 'models/' prefix to avoid 404 errors
    clean_list = []
    for m in raw_list:
        if m.startswith("models/"):
            clean_list.append(m.replace("models/", ""))
        else:
            clean_list.append(m)
            
    return clean_list   