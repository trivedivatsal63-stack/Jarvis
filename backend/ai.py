import os
import json
import datetime
from groq import AsyncGroq
import memory as mem
import memory_vector as mem_vec

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
gemini_client = None
if GEMINI_API_KEY:
    from google import genai
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the personal AI assistant. "
    "You are modeled after the AI from Iron Man. You are highly intelligent, formal, and efficient. "
    "You address the user as 'Sir'. You speak in a calm, composed British manner with subtle dry wit. "
    "You are concise — never ramble. You anticipate needs. "
    "When tools are available (weather, news, web search), you use them proactively. "
    "You never say you cannot do something — you find a way or suggest the best alternative. "
    "You have access to the user's system and can open applications, take screenshots, and monitor hardware."
)

def _build_context(session_id: str, user_msg: str) -> list:
    history = mem.get_history(session_id, 20)
    now = datetime.datetime.now()
    time_context = f"Current time: {now.strftime('%I:%M %p, %A, %B %d, %Y')}"
    system_content = SYSTEM_PROMPT + "\n" + time_context
    vec_context = mem_vec.get_relevant_context(user_msg)
    if vec_context:
        system_content += "\n" + vec_context
    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_msg})
    return messages

async def stream_groq(messages: list):
    if not groq_client:
        raise Exception("Groq not configured")
    stream = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,
        temperature=0.7,
        max_tokens=1024,
    )
    async for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if token:
            yield token

async def stream_gemini(messages: list):
    if not gemini_client:
        raise Exception("Gemini not configured")
    system = messages[0]["content"]
    conversation = messages[1:]
    prompt = system + "\n\n"
    for msg in conversation:
        role = "User" if msg["role"] == "user" else "Assistant"
        prompt += f"{role}: {msg['content']}\n"
    prompt += "Assistant: "
    response = gemini_client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text

async def generate_stream(session_id: str, user_msg: str):
    mem.add_message(session_id, "user", user_msg)
    messages = _build_context(session_id, user_msg)
    full_response = ""
    used_fallback = False

    try:
        async for token in stream_groq(messages):
            full_response += token
            yield token
    except Exception as groq_err:
        print(f"Groq failed: {groq_err}, falling back to Gemini")
        used_fallback = True
        try:
            async for token in stream_gemini(messages):
                full_response += token
                yield token
        except Exception as gemini_err:
            yield f"I apologize, Sir, but my primary and secondary neural processors are currently unreachable. Error: {gemini_err}"

    if full_response:
        mem.add_message(session_id, "assistant", full_response)
        try:
            history = mem.get_history(session_id, 20)
            if len(history) >= 3:
                mem_vec.store_conversation(session_id, history)
        except Exception:
            pass
