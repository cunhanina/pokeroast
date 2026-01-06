import warnings
import json
import google.generativeai as genai
import streamlit as st
from .config import get_api_key, get_model_candidates

warnings.filterwarnings("ignore")

genai.configure(api_key=get_api_key())

def generate_roast_data(team_list: list[str], game_context: str = "General Pokemon") -> dict:
    candidates = get_model_candidates()
    
    # Prompt Setup
    prompt = f"""
    You are a competitive Pokemon veteran. 
    The user is playing: **{game_context}**.
    Analyze this team: {', '.join(team_list)}.
    
    Goal: Roast them based on the specific meta/bosses of {game_context}.
    Be toxic but accurate.
    
    Return ONLY JSON:
    {{
        "roast": "Your mean paragraph here...",
        "worst_pokemon": "ExactNameFromList"
    }}
    """
    
    errors = []

    # --- FAILOVER LOOP ---
    for model_name in candidates:
        try:
            # print(f"DEBUG: Trying model {model_name}...") # Uncomment for deep debugging
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            # Clean and Parse
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
            
        except Exception as e:
            error_str = str(e)
            
            # Intelligent logging for the user
            if "429" in error_str:
                print(f"⚠️ QUOTA EXCEEDED on {model_name}. Switching to next model...")
                errors.append(f"{model_name}: Rate Limit (429)")
            elif "404" in error_str:
                print(f"⚠️ MODEL NOT FOUND: {model_name}. Switching...")
                errors.append(f"{model_name}: Not Found (404)")
            else:
                print(f"⚠️ ERROR on {model_name}: {error_str}")
                errors.append(f"{model_name}: {error_str}")
            
            continue # Force loop to try next model in list

    # If loop finishes without returning, all models failed
    return {
        "roast": f"⚠️ SYSTEM FAILURE. All models busy or broken. Logs: {' || '.join(errors)}",
        "worst_pokemon": "System Error"
    }