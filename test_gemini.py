import google.generativeai as genai

genai.configure(api_key="YOUR_GOOGLE_API_KEY")

model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content(
    "Help me prepare for software engineering interviews"
)

print(response.text)