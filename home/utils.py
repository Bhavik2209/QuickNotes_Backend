import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

load_dotenv()

def clean_markdown(text):
    """
    Clean and standardize markdown formatting
    """
    # Fix bold syntax
    text = re.sub(r'<strong>(.*?)<strong>', r'**\1**', text)
    
    # Fix code blocks
    text = re.sub(r'<code><code><code>(.*?)<code><code><code>', r'```\1```', text)
    text = re.sub(r'<code>(.*?)<code>', r'`\1`', text)
    
    # Ensure proper spacing around headers
    text = re.sub(r'(\n|^)#([^#\n]+)', r'\1# \2', text)
    
    # Ensure proper spacing around lists
    text = re.sub(r'(\n|^)\*([^\n*]+)', r'\1* \2', text)
    text = re.sub(r'(\n|^)\d+\.([^\n]+)', r'\1\1. \2', text)
    
    # Add proper spacing around code blocks
    text = re.sub(r'```(\w+)?\n', r'\n```\1\n', text)
    text = re.sub(r'\n```\n', r'\n\n```\n\n', text)
    
    return text

def get_gemini_response(transcript):
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    print("Hello")
    if not gemini_api_key:
        return "API key not found in environment."
    
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-pro")
    
    prompt = """
    Please analyze and provide a detailed, easy-to-follow explanation of the following transcript in english language only. 
    Format your response using proper markdown:
    - Use ** for bold text (e.g., **important term**)
    - Use ``` for code blocks
    - Use proper spacing for lists and headers
    - Use proper markdown syntax for all formatting
    - give explanation like you are explainig to a 10 year old.
    - Explanation must be in the english language only not any other language.
    
    Your response should be structured in a clear and organized way to make complex ideas understandable 
    for a broad audience. Break down any technical terms or concepts, offering examples or comparisons 
    when helpful. Summarize key points and include relevant context for each section, your response should be in the english language only not any other language.
    
    Transcript to analyze: {transcript}
    """
    print("hello")
    response = model.generate_content(prompt.format(transcript=transcript))
    print("Hello")
    # Clean and standardize the markdown formatting
    cleaned_response = clean_markdown(response.text)

    diagram = """
    graph TD;
        A[Start] --> B{Is it working?};
        B -- Yes --> C[Great!];
        B -- No --> D[Fix it];
        D --> B;
    """
    
    # Example: Create a simple flowchart definition
   

    return {
        'transcript':cleaned_response,
        'diagram' : diagram,
    }