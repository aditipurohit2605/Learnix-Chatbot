import os
import re
import PyPDF2
import docx2txt
from .ai_client import ai_client

def extract_text_from_file(file_path, file_type):
    """
    Extracts plain text from docx, pdf, or txt.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    text = ""
    file_type = file_type.lower().strip('.')
    
    if file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            
    elif file_type == 'pdf':
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = []
                # Limit to first 20 pages to avoid performance spikes
                num_pages = min(len(reader.pages), 20)
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_content = page.extract_text()
                    if page_content:
                        pages_text.append(page_content)
                text = "\n".join(pages_text)
        except Exception as e:
            print(f"Error reading PDF file {file_path}: {e}")
            text = f"Failed to extract PDF text. Error details: {e}"
            
    elif file_type == 'docx':
        try:
            text = docx2txt.process(file_path)
        except Exception as e:
            print(f"Error reading DOCX file {file_path}: {e}")
            text = f"Failed to extract Word text. Error details: {e}"
            
    else:
        raise ValueError(f"Unsupported file format: .{file_type}")
        
    return text.strip()

def generate_summary(file_name, file_content):
    """
    Generates a three-tiered summary from file content.
    Returns: dict with 'title', 'short_summary', 'detailed_summary', 'bullet_points'
    """
    title = f"Summary of {os.path.basename(file_name)}"
    
    if not file_content:
        return {
            "title": title,
            "short_summary": "This document appears to be empty.",
            "detailed_summary": "No content could be extracted or found in the uploaded file.",
            "bullet_points": "Empty File"
        }
        
    # Check if AI client is available
    if ai_client.is_available():
        prompt = (
            f"You are a study assistant. Summarize the following document content.\n"
            f"Document Title: {file_name}\n"
            f"Content:\n{file_content[:5000]}\n\n"
            f"Output must be structured as a JSON block with the following keys:\n"
            f"- 'short_summary': A 2-3 sentence overview.\n"
            f"- 'detailed_summary': A comprehensive paragraph details review.\n"
            f"- 'bullet_points': 4-6 bullet points of the key concepts separated by double vertical bars '||'.\n"
        )
        try:
            messages = [
                {"role": "system", "content": "You are a professional educational summarizer. You output raw JSON structure with no extra text."},
                {"role": "user", "content": prompt}
            ]
            response = ai_client.get_completion(messages, temperature=0.5)
            import json
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("\n", 1)[0]
            cleaned = cleaned.strip("` \n")
            
            data = json.loads(cleaned)
            return {
                "title": title,
                "short_summary": data.get("short_summary", "Summary not available."),
                "detailed_summary": data.get("detailed_summary", "Detailed breakdown not available."),
                "bullet_points": data.get("bullet_points", "Concept A || Concept B")
            }
        except Exception as e:
            print(f"AI summary failed, resorting to analytical parser: {e}")
            # fall through to fallback

    # Offline/analytical fallback: extract key sentences using simple regex
    sentences = re.split(r'(?<=[.!?])\s+', file_content)
    clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    word_count = len(file_content.split())
    char_count = len(file_content)
    
    # Take first 2 sentences for short summary
    short_sum = " ".join(clean_sentences[:2]) if clean_sentences else "This file contains plain text content."
    if not short_sum:
        short_sum = f"No complete sentences detected. The document contains {word_count} words."
        
    # Take first 5 sentences for detailed summary
    detailed_sum = " ".join(clean_sentences[:6]) if len(clean_sentences) > 2 else file_content[:300]
    detailed_sum += f"\n\n[Analysis details: Document contains {word_count} total words and {char_count} characters. Processed offline.]"
    
    # Pick a few words as concepts
    words = re.findall(r'\b[A-Za-z]{5,}\b', file_content)
    unique_words = sorted(list(set([w.lower() for w in words])), key=len, reverse=True)
    concepts = [w.capitalize() for w in unique_words[:5]]
    
    if not concepts:
        concepts = ["Core Content", "Study Reference"]
    bullet_points = " || ".join(concepts)
    
    return {
        "title": title,
        "short_summary": short_sum,
        "detailed_summary": detailed_sum,
        "bullet_points": bullet_points
    }
