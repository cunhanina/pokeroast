import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    # 1. Try Secrets (Cloud)
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    
    # 2. Try Local Env
    key = os.getenv("GROQ_API_KEY")
    
    if not key:
        st.error("❌ CRITICAL: GROQ_API_KEY is missing. Get one at console.groq.com")
        st.stop()
        
    return key