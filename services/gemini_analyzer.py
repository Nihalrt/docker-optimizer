import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAnalyzer:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found, error")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    
    def analyze_dockerfile_for_optimizations(self, dockerfile_content: str):
        prompt = f"""
        As an expert in Docker and containerization, please analyze the following Dockerfile.
        Provide a detailed, actionable list of suggestions to optimize it for smaller image size,
        faster build times, and better security. For each suggestion, explain why it's important
        and provide a code snippet showing the "before" and "after".

        Dockerfile content:
        ---
        {dockerfile_content}
        ---
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"there's an error: {str(e)}"
        


