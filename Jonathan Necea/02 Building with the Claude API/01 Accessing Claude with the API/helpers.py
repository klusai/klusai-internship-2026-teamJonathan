from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()
model = "claude-haiku-4-5" # deprecating claude-sonnet-4-6 to claude-haiku-4-5 in order to be able to finish the courses

def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})

def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})

def chat(messages, system=None, temperature=1.0, stop_sequences=None, output_config=None):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
    }

    if system:
        params["system"] = system
    if stop_sequences:
        # replaced in newer models by output_config. For the course's sake, downgrade the model to claude-haiku-4-5
        params["stop_sequences"] = stop_sequences
    if output_config:
        # output_config={"format": {"type": "json_schema", "schema": YOUR_SCHEMA}} - replaces stop_sequences
        params["output_config"] = output_config

    message = client.messages.create(**params)

    return next((block.text for block in message.content if block.type == "text"), "")