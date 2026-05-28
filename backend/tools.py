import os
import subprocess
import datetime
import psutil
import pyautogui
import base64
import json
import httpx
from bs4 import BeautifulSoup
import socket

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "browser": "chrome.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
    "paint": "mspaint.exe",
    "terminal": "wt.exe",
    "spotify": "spotify.exe",
    "vscode": "code.exe",
    "discord": "discord.exe",
    "whatsapp": "WhatsApp.exe",
    "zoom": "Zoom.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "youtube": "chrome.exe https://www.youtube.com",
    "gmail": "chrome.exe https://mail.google.com",
    "github": "chrome.exe https://www.github.com",
}

def open_app(name):
    name = name.lower().strip()
    if name in APPS:
        val = APPS[name]
        if val.startswith("chrome.exe "):
            url = val.split(" ", 1)[1]
            subprocess.Popen(["chrome.exe", url], shell=True)
        else:
            subprocess.Popen(val, shell=True)
        return f"Opening {name.title()}"
    return None

def get_system_stats():
    cpu = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()
    now = datetime.datetime.now()
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return {
        "cpu": round(cpu, 1),
        "ram": round(mem.percent, 1),
        "ram_used_gb": round(mem.used / (1024**3), 1),
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "disk": round(disk.percent, 1),
        "battery": round(battery.percent, 1) if battery else None,
        "time": now.strftime("%I:%M:%S %p"),
        "date": now.strftime("%A, %B %d, %Y"),
        "hostname": hostname,
        "ip": ip,
    }

def get_weather(city: str):
    if not WEATHER_API_KEY:
        return {"error": "Weather API key not configured"}
    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={WEATHER_API_KEY}"
        geo_resp = httpx.get(geo_url, timeout=5).json()
        if not geo_resp:
            return {"error": f"City '{city}' not found"}
        lat, lon = geo_resp[0]["lat"], geo_resp[0]["lon"]
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        data = httpx.get(weather_url, timeout=5).json()
        return {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "temp": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
        }
    except Exception as e:
        return {"error": str(e)}

def get_news(query: str = "general", count: int = 5):
    if not NEWS_API_KEY:
        return {"error": "News API key not configured"}
    try:
        if query and query != "general":
            url = f"https://newsapi.org/v2/everything?q={query}&pageSize={count}&apiKey={NEWS_API_KEY}"
        else:
            url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize={count}&apiKey={NEWS_API_KEY}"
        data = httpx.get(url, timeout=10).json()
        if data.get("status") != "ok":
            return {"error": data.get("message", "News API error")}
        return [
            {"title": a["title"], "source": a["source"]["name"], "url": a["url"], "description": a.get("description", "")}
            for a in data.get("articles", [])
        ]
    except Exception as e:
        return {"error": str(e)}

def web_search(query: str, count: int = 5):
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        results = []
        for r in soup.select(".result")[:count]:
            title_el = r.select_one(".result__title a")
            snippet_el = r.select_one(".result__snippet")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el.get("href", ""),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                })
        return results
    except Exception as e:
        return [{"title": "Search error", "url": "", "snippet": str(e)}]

def take_screenshot():
    try:
        img = pyautogui.screenshot()
        buffered = img.tobytes()
        b64 = base64.b64encode(buffered).decode()
        return {
            "base64": b64,
            "width": img.width,
            "height": img.height,
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}

def get_sysinfo():
    import platform
    uname = platform.uname()
    return {
        "os": f"{uname.system} {uname.release}",
        "version": uname.version,
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "architecture": uname.machine,
        "processor": uname.processor,
        "python": platform.python_version(),
    }

def detect_intent(text: str):
    t = text.lower().strip()
    if any(w in t for w in ["weather", "temperature", "forecast", "rain"]):
        return "weather"
    if any(w in t for w in ["news", "headlines", "headline"]):
        return "news"
    if any(w in t for w in ["search", "google", "look up", "find"]):
        return "search"
    if any(w in t for w in ["time", "what time"]):
        return "time"
    if any(w in t for w in ["date", "what's the date", "today"]):
        return "date"
    if any(w in t for w in ["open ", "launch ", "start "]):
        return "open_app"
    if any(w in t for w in ["screenshot", "capture screen"]):
        return "screenshot"
    if any(w in t for w in ["cpu", "system", "memory", "ram", "battery", "hardware", "system info"]):
        return "system"
    if any(w in t for w in ["joke", "funny", "make me laugh"]):
        return "joke"
    if any(w in t for w in ["ip", "my ip", "hostname", "computer name"]):
        return "sysinfo"
    return "chat"
