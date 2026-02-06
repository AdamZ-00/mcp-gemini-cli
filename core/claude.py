import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

class MockContentBlock:
    def __init__(self, text):
        self.text = text
        self.type = 'text'

class MockMessage:
    def __init__(self, text):
        self.content = [MockContentBlock(text)]
        self.usage = None
        self.stop_reason = "end_turn"
        self.model = "gemini-adapter"
        self.role = "assistant"

# Adaptateur Gemini 
class Claude:
    def __init__(self, model: str):
        raw_model = model if model else "gemini-2.5-flash"
        self.model_name = raw_model.replace("models/", "")

        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Erreur init client: {e}")

    def add_user_message(self, messages: list, message):
        content = message
        if hasattr(message, 'content'): 
             raw_content = getattr(message, 'content', '')
             if isinstance(raw_content, list):
                 content = raw_content[0].text if raw_content else ""
        messages.append({"role": "user", "content": str(content)})

    def add_assistant_message(self, messages: list, message):
        content = message
        if hasattr(message, 'content'):
             raw_content = getattr(message, 'content', '')
             if isinstance(raw_content, list):
                 content = raw_content[0].text if raw_content else ""
        messages.append({"role": "model", "content": str(content)})

    def text_from_message(self, message):
        return "\n".join([b.text for b in message.content if b.type == "text"])

    def chat(self, messages, system=None, tools=None, **kwargs):
        if not self.client:
            return MockMessage("Pas de client Google configuré.")

        try:
            last_msg = messages[-1]['content']
            
            if system:
                last_msg = f"Système: {system}\n\nQuestion: {last_msg}"

            # Appel API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=last_msg
            )
            
            return MockMessage(response.text)

        except Exception as e:
            return MockMessage(f"Erreur Gemini : {str(e)}")