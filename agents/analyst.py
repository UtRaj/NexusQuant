# agents/analyst.py 

import os
import json
from groq import Groq
from .base import BaseAgent
from dotenv import load_dotenv

load_dotenv()

class AnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Analyst")
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def run(self, symbol: str, context: str = "") -> dict:
        """
        Analyze sentiment for a specific asset given market context.
        """
        prompt = f"""
        Analyze the current sentiment and outlook for {symbol}.
        Context: {context}
        
        Return JSON:
        {{
            "outlook": "BULLISH" | "BEARISH" | "NEUTRAL",
            "confidence": <float 0.0 to 1.0>,
            "reasoning": "<brief institutional-grade rationale>"
        }}
        """
        
        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a senior macro analyst for a hedge fund. Output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(completion.choices[0].message.content)
            
            # Advice record is handled by engine in 3.0
            return analysis

        except Exception as e:
            print(f"Analyst Error for {symbol}: {e}")
            return {"outlook": "NEUTRAL", "confidence": 0.0, "reasoning": "Error in analysis"}
