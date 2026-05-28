import os
import json
import asyncio
import datetime
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

import ai
import tools
import memory as mem
import voice as vc
import scheduler
import ws as ws_mod
import memory_vector as mem_vec
import telegram_bot as tb_mod
import cache as cache_mod

app = FastAPI(title="J.A.R.V.I.S", version="4.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler.start()
mem_vec.init_vector_memory()
cache_mod.cache_prefetch()
tb_mod.setup_bot(app)

# --- Optional modules (graceful import) ---
vision = None
system_control = None
smarthome = None
legion = None
search_engine = None

try:
    import vision as vis_mod
    vision = vis_mod
except ImportError:
    pass

try:
    import system_control as sc_mod
    system_control = sc_mod
except ImportError:
    pass

try:
    import smarthome as sh_mod
    smarthome = sh_mod
except ImportError:
    pass

try:
    import legion as leg_mod
    legion = leg_mod
except ImportError:
    pass

try:
    import search as srch_mod
    search_engine = srch_mod
except ImportError:
    pass

# --- Pydantic models ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class TTSRequest(BaseModel):
    text: str

class ReminderRequest(BaseModel):
    message: str
    minutes: float

class NoteCreate(BaseModel):
    title: str
    content: str = ""
    tags: str = ""

class NoteUpdate(BaseModel):
    title: str = None
    content: str = None
    tags: str = None

class LegionRequest(BaseModel):
    task: str

class CodeRunRequest(BaseModel):
    code: str

class DeviceControl(BaseModel):
    entity_id: str
    action: str
    params: dict = {}

class ResearchRequest(BaseModel):
    topic: str
    depth: int = 2

# ======================================================================
# CHAT ENDPOINT
# ======================================================================
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    sys_resp = handle_system_command(req.message)
    if sys_resp:
        async def sys_gen():
            yield json.dumps({"token": sys_resp, "type": "system"}) + "\n"
            yield json.dumps({"done": True}) + "\n"
        return StreamingResponse(sys_gen(), media_type="text/event-stream")

    async def generate():
        tool_result = await handle_tool_command(req.message)
        if tool_result:
            yield json.dumps({"token": tool_result, "type": "system"}) + "\n"
            yield json.dumps({"done": True}) + "\n"
            return
        async for token in ai.generate_stream(req.session_id, req.message):
            yield json.dumps({"token": token, "type": "ai"}) + "\n"
        yield json.dumps({"done": True}) + "\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/chat/reset")
async def reset_chat(session_id: str = "default"):
    mem.clear_history(session_id)
    return {"message": "Conversation reset, Sir."}

# ======================================================================
# WEBSOCKET
# ======================================================================
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    session_id = ws.query_params.get("session_id", "default")

    async def handle_message(ws: WebSocket, sid: str, msg: str):
        sys_resp = handle_system_command(msg)
        if sys_resp:
            await ws_mod.manager.send_to(ws, {"type": "token", "token": sys_resp, "type_label": "system"})
            await ws_mod.manager.send_to(ws, {"type": "done"})
            return

        tool_result = await handle_tool_command(msg)
        if tool_result:
            await ws_mod.manager.send_to(ws, {"type": "token", "token": tool_result, "type_label": "system"})
            await ws_mod.manager.send_to(ws, {"type": "done"})
            return

        await ws_mod.manager.send_to(ws, {"type": "thinking"})
        async for token in ai.generate_stream(sid, msg):
            await ws_mod.manager.send_to(ws, {"type": "token", "token": token, "type_label": "ai"})
        await ws_mod.manager.send_to(ws, {"type": "done"})

    await ws_mod.handle_ws(ws, session_id, handle_message)

# ======================================================================
# SYSTEM COMMAND DISPATCH
# ======================================================================
def handle_system_command(text: str) -> str | None:
    t = text.lower().strip()
    intent = tools.detect_intent(t)
    if intent in ("time", "date"):
        stats = tools.get_system_stats()
        if intent == "time":
            return f"The time is {stats['time']}, Sir."
        return f"Today is {stats['date']}, Sir."
    if intent == "joke":
        try:
            import pyjokes
            return pyjokes.get_joke()
        except:
            return None
    if intent == "open_app":
        for kw in ["open ", "launch ", "start "]:
            if kw in t:
                app_name = t.split(kw, 1)[-1].strip()
                if system_control:
                    result = system_control.open_app(app_name)
                else:
                    result = tools.open_app(app_name)
                if result and "error" not in result:
                    return result.get("message", f"Launching {app_name}, Sir.")
                return f"I could not find an application named '{app_name}', Sir."
    if intent == "screenshot":
        if system_control:
            result = system_control.screenshot()
        else:
            result = tools.take_screenshot()
        if "error" in result:
            return f"Screenshot failed: {result['error']}"
        return "Screenshot captured, Sir."
    if intent == "sysinfo":
        info = tools.get_sysinfo()
        return f"System: {info['os']}, Host: {info['hostname']}, IP: {info['ip']}"
    return None

# ======================================================================
# TOOL COMMAND DISPATCH
# ======================================================================
async def handle_tool_command(text: str) -> str | None:
    t = text.lower().strip()
    intent = tools.detect_intent(t)

    if intent == "weather":
        city = t
        for prefix in ["weather in ", "weather of ", "temperature in ", "weather for ", "forecast for "]:
            if prefix in t:
                city = t.split(prefix, 1)[-1].strip()
                break
        else:
            words = t.split()
            for i, w in enumerate(words):
                if w in ("in", "of", "for", "at") and i + 1 < len(words):
                    city = words[i + 1]
                    break
            else:
                city = "London"
        cached = cache_mod.get_cached_weather(city)
        if cached:
            data = json.loads(cached)
        else:
            data = tools.get_weather(city)
            if "error" not in data:
                cache_mod.cache_weather(city, json.dumps(data))
        if "error" in data:
            return f"I apologize, Sir, but I could not fetch the weather. {data['error']}"
        return (
            f"Weather in {data['city']}, {data['country']}: {data['description']}. "
            f"Temperature is {data['temp']}°C (feels like {data['feels_like']}°C). "
            f"Humidity: {data['humidity']}%, Wind: {data['wind_speed']} m/s."
        )

    if intent == "news":
        query = "general"
        for prefix in ["news about ", "news on ", "headlines about "]:
            if prefix in t:
                query = t.split(prefix, 1)[-1].strip()
                break
        cached = cache_mod.get_cached_news(query)
        if cached:
            articles = json.loads(cached)
        else:
            articles = tools.get_news(query)
            if isinstance(articles, list):
                cache_mod.cache_news(query, json.dumps(articles))
        if isinstance(articles, dict) and "error" in articles:
            return f"News unavailable: {articles['error']}"
        if not articles:
            return "No news articles found, Sir."
        lines = [f"{i+1}. {a['title']} — {a['source']}" for i, a in enumerate(articles)]
        return "Here are the top headlines, Sir:\n" + "\n".join(lines)

    if intent == "search":
        query = t
        for prefix in ["search for ", "search ", "google ", "look up ", "find "]:
            if prefix in t:
                query = t.split(prefix, 1)[-1].strip()
                break
        if search_engine:
            results = search_engine.search_web(query)
        else:
            results = tools.web_search(query)
        if isinstance(results, list) and results:
            lines = [f"{i+1}. {r['title']}: {r.get('snippet', '')[:200]}" for i, r in enumerate(results)]
            return f"Search results for '{query}', Sir:\n" + "\n".join(lines)

    if intent == "system":
        cached = cache_mod.get_cached_stats()
        if cached:
            stats = json.loads(cached)
        else:
            stats = tools.get_system_stats()
            cache_mod.cache_stats(json.dumps(stats))
        return (
            f"System status, Sir — CPU: {stats['cpu']}%, "
            f"RAM: {stats['ram']}% ({stats['ram_used_gb']}/{stats['ram_total_gb']} GB), "
            f"Disk: {stats['disk']}%"
            + (f", Battery: {stats['battery']}%" if stats['battery'] is not None else "")
        )

    if intent == "smarthome" and smarthome:
        devices = smarthome.get_devices()
        if devices.get("available"):
            count = len(devices.get("lights", [])) + len(devices.get("switches", []))
            return f"Smart home connected. {count} devices available, Sir."
        return "Smart home is not configured, Sir."

    if intent == "vision" and vision:
        return "Vision systems online, Sir. Use the camera interface to scan."

    if intent == "reminder":
        return "I can set reminders for you, Sir. Just tell me what to remember and when."

    if intent == "research" and search_engine:
        query = t
        for prefix in ["research ", "deep research ", "investigate "]:
            if prefix in t:
                query = t.split(prefix, 1)[-1].strip()
                break
        result = search_engine.research_pipeline(query, depth=2)
        if "error" in result:
            return f"Research failed: {result['error']}"
        return (
            f"Research complete on '{result['topic']}', Sir. "
            f"Found {result['source_count']} sources. "
            f"{result['summary'][:500]}"
        )

    return None

# ======================================================================
# VISION ENDPOINTS
# ======================================================================
if vision:
    @app.post("/vision/register")
    async def vision_register(name: str, file: UploadFile = File(...)):
        data = await file.read()
        result = vision.register_face(name, data)
        return result

    @app.post("/vision/identify")
    async def vision_identify(file: UploadFile = File(...)):
        data = await file.read()
        result = vision.identify_faces(data)
        return result

    @app.post("/vision/scan")
    async def vision_scan(file: UploadFile = File(...)):
        data = await file.read()
        objects = vision.detect_objects(data)
        threat = vision.check_threat(objects)
        return {"objects": objects, "threat": threat}

    @app.post("/vision/analyze")
    async def vision_analyze(file: UploadFile = File(...)):
        data = await file.read()
        description = vision.analyze_scene(data)
        return {"description": description}

    @app.post("/read-screen")
    async def read_screen():
        description = vision.read_screen()
        return {"description": description}

# ======================================================================
# SYSTEM CONTROL ENDPOINTS
# ======================================================================
if system_control:
    @app.get("/system/stats")
    async def system_stats():
        return system_control.get_system_stats()

    @app.get("/system/apps")
    async def system_apps():
        return {"apps": system_control.list_apps()}

    @app.post("/system/apps/open")
    async def system_apps_open(name: str = Query(...)):
        return system_control.open_app(name)

    @app.post("/system/apps/close")
    async def system_apps_close(name: str = Query(...)):
        return system_control.close_app(name)

    @app.get("/files/list")
    async def files_list(path: str = Query(".")):
        return system_control.list_files(path)

    @app.get("/files/read")
    async def files_read(path: str = Query(...)):
        return system_control.read_file(path)

    @app.post("/files/create")
    async def files_create(path: str = Query(...), content: str = Query("")):
        return system_control.create_file(path, content)

    @app.get("/files/search")
    async def files_search(query: str = Query(...)):
        return {"results": system_control.search_files(query)}

    @app.delete("/files/delete")
    async def files_delete(path: str = Query(...), confirm: bool = Query(False)):
        return system_control.delete_file(path, confirm)

    @app.post("/code/run")
    async def code_run(req: CodeRunRequest):
        return system_control.run_code(req.code)

    @app.post("/screenshot")
    async def screenshot():
        return system_control.screenshot()

# ======================================================================
# SMART HOME ENDPOINTS
# ======================================================================
if smarthome:
    @app.get("/home/devices")
    async def home_devices():
        return smarthome.get_devices()

    @app.post("/home/control")
    async def home_control(req: DeviceControl):
        return smarthome.control_device(req.entity_id, req.action, **req.params)

    @app.get("/home/status")
    async def home_status():
        return smarthome.get_status()

# ======================================================================
# IRON LEGION ENDPOINTS
# ======================================================================
if legion:
    @app.post("/legion/run")
    async def legion_run(req: LegionRequest):
        import time
        start = time.time()
        result = await legion.run_legion(req.task)
        result["execution_time"] = round(time.time() - start, 2)
        return result

    @app.post("/legion/decompose")
    async def legion_decompose(req: LegionRequest):
        return {"subtasks": legion.decompose_task(req.task)}

# ======================================================================
# SEARCH ENDPOINTS
# ======================================================================
if search_engine:
    @app.get("/search")
    async def web_search(q: str = Query(...)):
        results = search_engine.search_web(q)
        return {"results": results}

    @app.get("/search/images")
    async def search_images(q: str = Query(...)):
        results = search_engine.search_images(q)
        return {"results": results}

    @app.get("/search/news")
    async def search_news(q: str = Query(...)):
        results = search_engine.search_news(q)
        return {"results": results}

    @app.get("/search/videos")
    async def search_videos(q: str = Query(...)):
        results = search_engine.search_videos(q)
        return {"results": results}

    @app.post("/search/deep")
    async def search_deep(url: str = Query(...)):
        result = search_engine.extract_content(url)
        return result

    @app.post("/research")
    async def research(req: ResearchRequest):
        return search_engine.research_pipeline(req.topic, req.depth)

# ======================================================================
# LEGACY REST ENDPOINTS (maintain backward compat)
# ======================================================================
@app.get("/weather")
async def weather_endpoint(city: str = Query("London")):
    cached = cache_mod.get_cached_weather(city)
    if cached:
        return json.loads(cached)
    data = tools.get_weather(city)
    if "error" not in data:
        cache_mod.cache_weather(city, json.dumps(data))
    return data

@app.get("/news")
async def news_endpoint(query: str = Query("general")):
    cached = cache_mod.get_cached_news(query)
    if cached:
        return {"articles": json.loads(cached)}
    articles = tools.get_news(query)
    if isinstance(articles, list):
        cache_mod.cache_news(query, json.dumps(articles))
    return {"articles": articles}

@app.get("/system")
async def system_endpoint():
    cached = cache_mod.get_cached_stats()
    if cached:
        return json.loads(cached)
    stats = tools.get_system_stats()
    cache_mod.cache_stats(json.dumps(stats))
    return stats

@app.get("/web-search")
async def web_search_endpoint(q: str = Query(...)):
    return {"results": tools.web_search(q)}

@app.get("/sysinfo")
async def sysinfo_endpoint():
    return tools.get_sysinfo()

@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    audio = vc.text_to_speech(req.text)
    return Response(content=audio, media_type="audio/mpeg")

@app.post("/stt")
async def stt_endpoint(body: bytes):
    text = vc.speech_to_text(body)
    return {"text": text}

@app.post("/reminder")
async def reminder_endpoint(req: ReminderRequest):
    trigger_at = scheduler.schedule_reminder(req.message, req.minutes)
    return {"message": f"Reminder set for {trigger_at}", "trigger_at": trigger_at}

# ======================================================================
# NOTES ENDPOINTS
# ======================================================================
@app.post("/notes")
async def notes_create(req: NoteCreate):
    note_id = mem.create_note(req.title, req.content, req.tags)
    return {"id": note_id, "message": "Note created, Sir."}

@app.get("/notes")
async def notes_list():
    notes = mem.list_notes()
    return {"notes": notes}

@app.get("/notes/search")
async def notes_search(q: str = Query(...)):
    results = mem.search_notes(q)
    return {"results": results}

@app.get("/notes/{note_id}")
async def notes_get(note_id: int):
    note = mem.get_note(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return note

@app.put("/notes/{note_id}")
async def notes_update(note_id: int, req: NoteUpdate):
    mem.update_note(note_id, req.title, req.content, req.tags)
    return {"message": "Note updated, Sir."}

@app.delete("/notes/{note_id}")
async def notes_delete(note_id: int):
    mem.delete_note(note_id)
    return {"message": "Note deleted, Sir."}

# ======================================================================
# MEMORY ENDPOINTS
# ======================================================================
@app.post("/memory/query")
async def memory_query(query: str = Query(...)):
    results = mem_vec.query_memories(query)
    return {"results": results}

@app.get("/memory/count")
async def memory_count():
    try:
        return {"count": mem_vec.init_vector_memory()}
    except:
        return {"count": 0}

# ======================================================================
# CACHE ENDPOINTS
# ======================================================================
@app.get("/cache/status")
async def cache_status():
    r = cache_mod.get_redis()
    if r is None:
        return {"available": False}
    return {"available": True}

@app.post("/cache/clear")
async def cache_clear(pattern: str = Query("*")):
    cache_mod.clear_cache(pattern)
    return {"message": "Cache cleared, Sir."}

# ======================================================================
# HEALTH
# ======================================================================
@app.get("/health")
async def health():
    return {
        "status": "online",
        "assistant": "J.A.R.V.I.S",
        "version": "4.1.0",
        "modules": {
            "vision": vision is not None,
            "system_control": system_control is not None,
            "smarthome": smarthome is not None,
            "legion": legion is not None,
            "search_engine": search_engine is not None,
            "memory_vector": True,
            "telegram_bot": tb_mod.bot_available,
            "cache": cache_mod.cache_available,
        },
        "time": datetime.datetime.now().isoformat(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
