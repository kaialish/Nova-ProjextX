from google import genai

client = genai.Client(api_key="AIzaSyBp-i5_GmVYiuhpSMK5XtBE3dZB4eI68_0")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Hello, how are you?"
)

print(response.text)
