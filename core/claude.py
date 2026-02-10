import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiResponse:
    """Wrapper autour de la réponse Gemini pour unifier l'interface."""

    def __init__(self, response):
        self._response = response
        self.model = "gemini-adapter"
        self.role = "assistant"

    @property
    def function_calls(self):
        """Retourne la liste des appels de fonctions demandés par le modèle."""
        if self._response.function_calls:
            return self._response.function_calls
        return []

    @property
    def stop_reason(self):
        """Retourne 'tool_use' si le modèle demande un appel de fonction, sinon 'end_turn'."""
        if self.function_calls:
            return "tool_use"
        return "end_turn"

    @property
    def text(self):
        """Retourne le texte de la réponse, ou chaîne vide si c'est un appel de fonction."""
        try:
            return self._response.text or ""
        except Exception:
            return ""

    @property
    def candidates(self):
        """Accès aux candidats bruts de la réponse Gemini."""
        return self._response.candidates


class MockResponse:
    """Réponse de secours en cas d'erreur ou d'absence de client."""

    def __init__(self, text):
        self._text = text
        self.model = "gemini-adapter"
        self.role = "assistant"
        self.function_calls = []
        self.stop_reason = "end_turn"
        self.candidates = []

    @property
    def text(self):
        return self._text


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

    def _convert_mcp_tools_to_gemini(self, tools):
        """Convertit une liste d'outils MCP au format Gemini FunctionDeclaration."""
        if not tools:
            return None

        function_declarations = []
        for tool in tools:
            name = tool.get("name", "")
            description = tool.get("description", "")
            parameters = tool.get("input_schema", {})

            # Nettoyer le schema : supprimer les champs non supportés par Gemini
            cleaned_params = self._clean_schema(parameters) if parameters else None

            fd = types.FunctionDeclaration(
                name=name,
                description=description,
                parameters=cleaned_params,
            )
            function_declarations.append(fd)

        if not function_declarations:
            return None

        return [types.Tool(function_declarations=function_declarations)]

    def _clean_schema(self, schema):
        """Nettoie un schema JSON pour le rendre compatible avec Gemini."""
        if not isinstance(schema, dict):
            return schema

        cleaned = {}
        # Gemini supporte : type, properties, required, description, enum, items
        allowed_keys = {"type", "properties", "required", "description", "enum", "items", "format"}
        for key, value in schema.items():
            if key in allowed_keys:
                if key == "properties" and isinstance(value, dict):
                    cleaned[key] = {k: self._clean_schema(v) for k, v in value.items()}
                elif key == "items" and isinstance(value, dict):
                    cleaned[key] = self._clean_schema(value)
                else:
                    cleaned[key] = value
        return cleaned

    def add_user_message(self, messages: list, content):
        """Ajoute un message utilisateur à l'historique au format Gemini Content."""
        if isinstance(content, list):
            # C'est une liste de Part (résultats d'outils)
            messages.append(types.Content(role="user", parts=content))
        elif isinstance(content, types.Content):
            messages.append(content)
        elif isinstance(content, str):
            messages.append(types.Content(role="user", parts=[types.Part.from_text(text=content)]))
        else:
            messages.append(types.Content(role="user", parts=[types.Part.from_text(text=str(content))]))

    def add_assistant_message(self, messages: list, response):
        """Ajoute la réponse du modèle à l'historique."""
        if hasattr(response, 'candidates') and response.candidates:
            # Ajouter le Content brut du modèle (préserve function_call + thought_signature)
            messages.append(response.candidates[0].content)
        elif hasattr(response, 'text'):
            messages.append(types.Content(role="model", parts=[types.Part.from_text(text=response.text)]))

    def text_from_message(self, response):
        """Extrait le texte d'une réponse."""
        if hasattr(response, 'text'):
            return response.text or ""
        return ""

    def chat(self, messages, system=None, tools=None, **kwargs):
        if not self.client:
            return MockResponse("Pas de client Google configuré.")

        try:
            # Convertir les outils MCP au format Gemini
            gemini_tools = self._convert_mcp_tools_to_gemini(tools)

            # Construire la config
            config = types.GenerateContentConfig(
                system_instruction=system if system else None,
                tools=gemini_tools,
            )

            # Construire le contenu à envoyer
            contents = self._build_contents(messages)

            # Appel API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            return GeminiResponse(response)

        except Exception as e:
            return MockResponse(f"Erreur Gemini : {str(e)}")

    def _build_contents(self, messages):
        """Construit la liste de contents pour l'API Gemini à partir de l'historique."""
        contents = []
        for msg in messages:
            if isinstance(msg, types.Content):
                contents.append(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                if role == "assistant":
                    role = "model"
                content_text = msg.get("content", "")
                if isinstance(content_text, str):
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content_text)]
                    ))
            else:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=str(msg))]
                ))
        return contents