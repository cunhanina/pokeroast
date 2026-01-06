import json
import streamlit as st
from groq import Groq
from .config import get_api_key

def generate_roast_data(team_list: list[str], game_context: str = "General Pokemon") -> dict:
    # 1. Initialize Client
    client = Groq(api_key=get_api_key())
    
    # 2. Define the Roast
    prompt = f"""
    You are a toxic competitive Pokemon player. The user is playing: **{game_context}**.
    Their team: {', '.join(team_list)}.
    
    ROAST THEM. Be mean, be specific about their bad type coverage, weak stats, or basic choices.
    
    Return ONLY JSON format:
    {{
        "roast": "Your roast paragraph...",
        "worst_pokemon": "The exact name of the worst pokemon on their team"
    }}
    """
    
    try:
        # 3. Call Llama 3.3 (The new flagship model)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # 4. Parse Result
        content = completion.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return {
            "roast": f"The roast machine broke. Error: {str(e)}",
            "worst_pokemon": "Magikarp"
        }