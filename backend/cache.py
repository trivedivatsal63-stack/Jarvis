import os
import threading
import json
import tools
from dotenv import load_dotenv
load_dotenv()

_redis_url = os.getenv("REDIS_URL", "")
_redis_client = None
_lock = threading.Lock()
cache_available = True

if not _redis_url:
    cache_available = False

def get_redis():
    global _redis_client, cache_available
    if _redis_client is not None:
        return _redis_client
    if not cache_available:
        return None
    with _lock:
        if _redis_client is not None:
            return _redis_client
        try:
            import redis
            _redis_client = redis.from_url(_redis_url, socket_connect_timeout=2, socket_timeout=2)
            _redis_client.ping()
        except Exception:
            cache_available = False
            _redis_client = None
    return _redis_client

def cache_get(key):
    try:
        r = get_redis()
        if r is None:
            return None
        val = r.get(key)
        if val is not None:
            return val.decode("utf-8")
        return None
    except Exception:
        return None

def cache_set(key, value, ttl=300):
    try:
        r = get_redis()
        if r is None:
            return
        r.setex(key, ttl, value)
    except Exception:
        pass

def cache_response(query, response):
    key = f"ai_response:{query.lower().strip()}"
    cache_set(key, response, ttl=600)

def get_cached_response(query):
    key = f"ai_response:{query.lower().strip()}"
    return cache_get(key)

def cache_weather(city, data_json):
    key = f"weather:{city.lower()}"
    cache_set(key, data_json, ttl=600)

def get_cached_weather(city):
    key = f"weather:{city.lower()}"
    return cache_get(key)

def cache_news(query, data_json):
    key = f"news:{query.lower()}"
    cache_set(key, data_json, ttl=600)

def get_cached_news(query):
    key = f"news:{query.lower()}"
    return cache_get(key)

def cache_stats(stats_json):
    cache_set("system_stats", stats_json, ttl=10)

def get_cached_stats():
    return cache_get("system_stats")

def cache_prefetch():
    try:
        weather_data = tools.get_weather("London")
        if "error" not in weather_data:
            cache_weather("London", json.dumps(weather_data))
    except Exception:
        pass
    try:
        news_data = tools.get_news("general")
        if isinstance(news_data, list):
            cache_news("general", json.dumps(news_data))
    except Exception:
        pass

def clear_cache(pattern="*"):
    try:
        r = get_redis()
        if r is None:
            return
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                r.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass
