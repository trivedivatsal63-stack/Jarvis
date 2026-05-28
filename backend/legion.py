import os
import json
import asyncio

TOOL_KEYWORDS = {
    "weather": ["weather", "temperature", "rain", "forecast"],
    "news": ["news", "headlines", "latest"],
    "search": ["search", "find", "look up", "research"],
    "system": ["system", "stats", "cpu", "memory", "battery"],
    "apps": ["app", "open", "launch", "start"],
    "files": ["file", "folder", "directory", "note"],
    "vision": ["vision", "camera", "see", "look", "face"],
    "home": ["home", "light", "device", "thermostat"],
    "email": ["email", "mail", "inbox"],
    "calendar": ["calendar", "schedule", "event", "meeting"],
    "code": ["code", "run", "python", "script", "execute"],
    "reminder": ["remind", "reminder"],
}


def decompose_task(task_str):
    t = task_str.lower()
    matched_tools = set()
    for tool, keywords in TOOL_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                matched_tools.add(tool)
                break
    if not matched_tools:
        return [{"id": 1, "description": f"Process request: {task_str}", "tool_needed": "chat", "status": "pending"}]
    subtasks = []
    for idx, tool in enumerate(sorted(matched_tools), 1):
        desc_map = {
            "weather": "Fetch current weather data",
            "news": "Retrieve latest news headlines",
            "search": "Perform web search",
            "system": "Gather system statistics",
            "apps": "Manage applications",
            "files": "Handle file operations",
            "vision": "Process visual input",
            "home": "Control smart home devices",
            "email": "Check email",
            "calendar": "Check calendar events",
            "code": "Execute code or script",
            "reminder": "Handle reminders",
        }
        subtasks.append({
            "id": idx,
            "description": desc_map.get(tool, f"Execute {tool} operation"),
            "tool_needed": tool,
            "status": "pending",
        })
    return subtasks


def _dispatch_subtask(subtask):
    tool = subtask["tool_needed"]
    try:
        if tool == "weather":
            import tools as tls
            data = tls.get_weather("London")
            return data
        elif tool == "news":
            import tools as tls
            data = tls.get_news("general", 5)
            return {"articles": data} if isinstance(data, list) else data
        elif tool == "search":
            import tools as tls
            data = tls.web_search(subtask.get("description", "latest"))
            return {"results": data} if isinstance(data, list) else data
        elif tool == "system":
            import tools as tls
            return tls.get_system_stats()
        elif tool == "apps":
            return {"message": "Application control module ready"}
        elif tool == "files":
            return {"message": "File system module ready"}
        elif tool == "vision":
            import tools as tls
            return tls.take_screenshot()
        elif tool == "home":
            import smarthome
            return smarthome.get_status()
        elif tool == "email":
            return {"message": "Email module ready"}
        elif tool == "calendar":
            return {"message": "Calendar module ready"}
        elif tool == "code":
            return {"message": "Code execution module ready"}
        elif tool == "reminder":
            return {"message": "Reminder module ready"}
        else:
            return {"message": f"No handler for tool: {tool}"}
    except Exception as e:
        return {"error": str(e)}


async def execute_subtasks(task_str):
    subtasks = decompose_task(task_str)
    for s in subtasks:
        s["status"] = "in_progress"

    async def run_with_timeout(subtask):
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _dispatch_subtask, subtask),
                timeout=15,
            )
            subtask["result"] = result
            subtask["status"] = "completed"
        except asyncio.TimeoutError:
            subtask["result"] = {"error": "Subtask timed out after 15 seconds"}
            subtask["status"] = "failed"
        except Exception as e:
            subtask["result"] = {"error": str(e)}
            subtask["status"] = "failed"

    tasks = [run_with_timeout(s) for s in subtasks]
    await asyncio.gather(*tasks)
    return subtasks


def synthesize_results(task_str, subtask_results):
    lines = ["Sir, here is what I have gathered:"]
    for sr in subtask_results:
        desc = sr.get("description", "Task")
        status = sr.get("status", "unknown")
        result = sr.get("result", {})
        if status == "failed":
            err = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
            lines.append(f"  - {desc}: Failed — {err}")
            continue
        if isinstance(result, dict) and "error" in result:
            lines.append(f"  - {desc}: Error — {result['error']}")
            continue
        tool = sr.get("tool_needed", "")
        if tool == "weather" and isinstance(result, dict):
            temp = result.get("temp", "N/A")
            desc_text = result.get("description", "N/A")
            city = result.get("city", "Unknown")
            humidity = result.get("humidity", "N/A")
            lines.append(f"  - Weather in {city}: {desc_text}, {temp}°C, humidity {humidity}%")
        elif tool == "news" and isinstance(result, dict):
            articles = result.get("articles", [])
            if articles:
                lines.append("  - Top headlines:")
                for a in articles[:3]:
                    lines.append(f"    • {a.get('title', 'Untitled')}")
            else:
                lines.append("  - News: No articles found")
        elif tool == "search" and isinstance(result, dict):
            results = result.get("results", [])
            if results:
                lines.append("  - Top search results:")
                for r in results[:3]:
                    lines.append(f"    • {r.get('title', 'Untitled')}: {r.get('url', '')}")
            else:
                lines.append("  - Search: No results found")
        elif tool == "system" and isinstance(result, dict):
            cpu = result.get("cpu", "N/A")
            ram = result.get("ram", "N/A")
            battery = result.get("battery", None)
            line = f"  - System: CPU {cpu}%, RAM {ram}%"
            if battery is not None:
                line += f", Battery {battery}%"
            lines.append(line)
        elif tool == "home" and isinstance(result, dict):
            lights = result.get("lights", [])
            switches = result.get("switches", [])
            climate = result.get("climate", [])
            parts = []
            if lights:
                on_count = sum(1 for l in lights if l.get("state") == "on")
                parts.append(f"{len(lights)} light(s) ({on_count} on)")
            if switches:
                on_count = sum(1 for s in switches if s.get("state") == "on")
                parts.append(f"{len(switches)} switch(es) ({on_count} on)")
            if climate:
                parts.append(f"{len(climate)} climate device(s)")
            if parts:
                lines.append(f"  - Smart Home: {', '.join(parts)}")
            else:
                lines.append("  - Smart Home: No devices found")
        elif tool == "vision" and isinstance(result, dict):
            if "error" in result:
                lines.append(f"  - Vision: Error — {result['error']}")
            else:
                lines.append(f"  - Vision: Captured ({result.get('width', 0)}x{result.get('height', 0)})")
        else:
            msg = result.get("message", json.dumps(result)) if isinstance(result, dict) else str(result)
            lines.append(f"  - {desc}: {msg}")
    lines.append("Is there anything else you require, Sir?")
    return "\n".join(lines)


async def run_legion(task_str):
    subtasks = await execute_subtasks(task_str)
    synthesis = synthesize_results(task_str, subtasks)
    return {
        "task": task_str,
        "subtasks": subtasks,
        "synthesis": synthesis,
    }
