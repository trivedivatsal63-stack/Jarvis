import os
import io
import re
import json
import time
import socket
import base64
import platform
import subprocess
import datetime
import tempfile

import psutil
import pyautogui

try:
    import speedtest
    speedtest_available = True
except ImportError:
    speedtest_available = False

try:
    import GPUtil
    gputil_available = True
except ImportError:
    gputil_available = False

SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"
IS_MAC = SYSTEM == "Darwin"

HOME_DIR = os.path.expanduser("~")

APPS = {
    "chrome": {"Windows": "chrome.exe", "Linux": "google-chrome", "Darwin": "Google Chrome"},
    "firefox": {"Windows": "firefox.exe", "Linux": "firefox", "Darwin": "Firefox"},
    "edge": {"Windows": "msedge.exe", "Linux": "microsoft-edge", "Darwin": "Microsoft Edge"},
    "spotify": {"Windows": "spotify.exe", "Linux": "spotify", "Darwin": "Spotify"},
    "vscode": {"Windows": "code.exe", "Linux": "code", "Darwin": "Visual Studio Code"},
    "notepad": {"Windows": "notepad.exe", "Linux": "gedit", "Darwin": "TextEdit"},
    "notepad++": {"Windows": "notepad++.exe", "Linux": "notepadqq", "Darwin": ""},
    "calculator": {"Windows": "calc.exe", "Linux": "gnome-calculator", "Darwin": "Calculator"},
    "terminal": {"Windows": "wt.exe", "Linux": "gnome-terminal", "Darwin": "Terminal"},
    "cmd": {"Windows": "cmd.exe", "Linux": "", "Darwin": ""},
    "explorer": {"Windows": "explorer.exe", "Linux": "nautilus", "Darwin": "Finder"},
    "file explorer": {"Windows": "explorer.exe", "Linux": "nautilus", "Darwin": "Finder"},
    "discord": {"Windows": "discord.exe", "Linux": "discord", "Darwin": "Discord"},
    "steam": {"Windows": "steam.exe", "Linux": "steam", "Darwin": "Steam"},
    "vlc": {"Windows": "vlc.exe", "Linux": "vlc", "Darwin": "VLC"},
    "obsidian": {"Windows": "obsidian.exe", "Linux": "obsidian", "Darwin": "Obsidian"},
    "slack": {"Windows": "slack.exe", "Linux": "slack", "Darwin": "Slack"},
    "zoom": {"Windows": "Zoom.exe", "Linux": "zoom", "Darwin": "zoom.us"},
    "outlook": {"Windows": "OUTLOOK.EXE", "Linux": "", "Darwin": "Microsoft Outlook"},
    "word": {"Windows": "WINWORD.EXE", "Linux": "libreoffice", "Darwin": "Microsoft Word"},
    "excel": {"Windows": "EXCEL.EXE", "Linux": "libreoffice", "Darwin": "Microsoft Excel"},
    "powerpoint": {"Windows": "POWERPNT.EXE", "Linux": "libreoffice", "Darwin": "Microsoft PowerPoint"},
    "settings": {"Windows": "ms-settings:", "Linux": "gnome-control-center", "Darwin": ""},
}

_network_speed_cache = {"data": None, "timestamp": 0}
_NETWORK_CACHE_TTL = 30

def _get_network_speed():
    now = time.time()
    if _network_speed_cache["data"] and (now - _network_speed_cache["timestamp"]) < _NETWORK_CACHE_TTL:
        return _network_speed_cache["data"]
    if not speedtest_available:
        return {"download": None, "upload": None}
    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        download = round(s.download() / 1_000_000, 1)
        upload = round(s.upload() / 1_000_000, 1)
        result = {"download_mbps": download, "upload_mbps": upload}
        _network_speed_cache["data"] = result
        _network_speed_cache["timestamp"] = now
        return result
    except Exception:
        return {"download": None, "upload": None}

def _get_gpu_info():
    if not gputil_available:
        return None
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return None
        return [
            {
                "name": gpu.name,
                "load_percent": round(gpu.load * 100, 1),
                "memory_total_mb": gpu.memoryTotal,
                "memory_used_mb": gpu.memoryUsed,
                "temperature_c": gpu.temperature,
            }
            for gpu in gpus
        ]
    except Exception:
        return None

def _get_temperature():
    if IS_WINDOWS:
        try:
            output = subprocess.check_output(
                "wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature /format:l",
                shell=True, timeout=5, stderr=subprocess.DEVNULL
            ).decode()
            temps = re.findall(r"\d+", output)
            if temps:
                vals = [int(t) for t in temps[1:]]
                if vals:
                    return [{"label": "CPU", "celsius": round((vals[0] - 2732) / 10, 1)}]
        except Exception:
            pass
    if IS_LINUX:
        try:
            output = subprocess.check_output(["sensors", "-j"], timeout=5, stderr=subprocess.DEVNULL).decode()
            data = json.loads(output)
            temps = []
            for chip, sensors in data.items():
                for sensor, values in sensors.items():
                    if isinstance(values, dict) and "temp1_input" in values:
                        temps.append({"label": sensor, "celsius": round(values["temp1_input"], 1)})
            return temps if temps else None
        except Exception:
            pass
    if IS_MAC:
        try:
            output = subprocess.check_output(["osx-cpu-temp"], timeout=5, stderr=subprocess.DEVNULL).decode()
            val = re.search(r"(\d+\.?\d*)", output)
            if val:
                return [{"label": "CPU", "celsius": round(float(val.group(1)), 1)}]
        except Exception:
            pass
    return None

def get_system_stats():
    try:
        cpu_percent_total = psutil.cpu_percent(interval=0.3)
        cpu_percent_per_core = psutil.cpu_percent(interval=0, percpu=True)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mount": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "free_gb": round(usage.free / (1024**3), 1),
                    "percent": round(usage.percent, 1),
                })
            except Exception:
                continue
        battery = psutil.sensors_battery()
        battery_info = None
        if battery:
            battery_info = {
                "percent": round(battery.percent, 1),
                "power_plugged": battery.power_plugged,
                "secsleft": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
            }
        net = _get_network_speed()
        gpu = _get_gpu_info()
        temp = _get_temperature()
        processes = []
        for proc in sorted(psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]), key=lambda p: p.info.get("cpu_percent", 0) or 0, reverse=True)[:5]:
            try:
                processes.append({
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "cpu_percent": round(proc.info["cpu_percent"] or 0, 1),
                    "memory_percent": round(proc.info["memory_percent"] or 0, 1),
                })
            except Exception:
                continue
        hostname = socket.gethostname()
        ips = []
        try:
            ips.append({"interface": "primary", "ip": socket.gethostbyname(hostname)})
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ips.append({"interface": iface, "ip": addr.address})
        except Exception:
            pass
        now = datetime.datetime.now()
        return {
            "cpu": {
                "total_percent": round(cpu_percent_total, 1),
                "per_core": [round(v, 1) for v in cpu_percent_per_core],
                "count": cpu_count,
                "freq_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
            },
            "ram": {
                "total_gb": round(mem.total / (1024**3), 1),
                "used_gb": round(mem.used / (1024**3), 1),
                "available_gb": round(mem.available / (1024**3), 1),
                "percent": round(mem.percent, 1),
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 1),
                "used_gb": round(swap.used / (1024**3), 1),
                "percent": round(swap.percent, 1),
            },
            "disks": disks,
            "battery": battery_info,
            "network": net,
            "gpu": gpu,
            "temperature": temp,
            "top_processes": processes,
            "time": now.strftime("%I:%M:%S %p"),
            "date": now.strftime("%A, %B %d, %Y"),
            "timezone": now.astimezone().tzname() or "",
            "hostname": hostname,
            "ips": ips,
            "os": f"{platform.system()} {platform.release()}",
            "os_version": platform.version(),
            "architecture": platform.machine(),
        }
    except Exception as e:
        return {"error": str(e)}

def open_app(name: str):
    name = name.lower().strip()
    if name not in APPS:
        return {"error": f"Unknown application: '{name}'"}
    entry = APPS[name]
    exe = entry.get(SYSTEM, "")
    if not exe:
        return {"error": f"No executable mapped for '{name}' on {SYSTEM}"}
    try:
        if IS_WINDOWS:
            if exe.startswith("ms-"):
                subprocess.Popen(f"start {exe}", shell=True)
            else:
                subprocess.Popen(exe, shell=True)
        elif IS_LINUX:
            subprocess.Popen([exe] if " " not in exe else ["sh", "-c", exe])
        elif IS_MAC:
            subprocess.Popen(["open", "-a", exe])
        return {"success": True, "app": name, "action": "launched"}
    except Exception as e:
        return {"error": str(e)}

def close_app(name: str):
    name_lower = name.lower().strip()
    exe = APPS.get(name_lower, {}).get(SYSTEM, name_lower)
    exe_name = os.path.splitext(exe)[0] if exe else name_lower
    try:
        killed = False
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = (proc.info["name"] or "").lower()
                if exe_name.lower() in pname or name_lower in pname:
                    proc.kill()
                    killed = True
            except Exception:
                continue
        if killed:
            return {"success": True, "app": name, "action": "terminated"}
        return {"error": f"No running process found for '{name}'"}
    except Exception as e:
        return {"error": str(e)}

def list_apps():
    try:
        processes = []
        for proc in sorted(psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]), key=lambda p: p.info.get("cpu_percent", 0) or 0, reverse=True)[:30]:
            try:
                pinfo = proc.info
                if pinfo["pid"] and pinfo["name"]:
                    processes.append({
                        "pid": pinfo["pid"],
                        "name": pinfo["name"],
                        "cpu_percent": round(pinfo["cpu_percent"] or 0, 1),
                        "memory_percent": round(pinfo["memory_percent"] or 0, 1),
                    })
            except Exception:
                continue
        return processes
    except Exception as e:
        return {"error": str(e)}

def list_files(path: str):
    try:
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}
        entries = []
        for entry in sorted(os.listdir(path), key=str.lower):
            full = os.path.join(path, entry)
            try:
                stat = os.stat(full)
                is_dir = os.path.isdir(full)
                entries.append({
                    "name": entry,
                    "type": "directory" if is_dir else "file",
                    "size_bytes": stat.st_size if not is_dir else 0,
                    "size_display": _format_size(stat.st_size) if not is_dir else "",
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception:
                continue
        return entries
    except Exception as e:
        return {"error": str(e)}

def _format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{round(size_bytes, 1)} {unit}"
        size_bytes /= 1024
    return f"{round(size_bytes, 1)} PB"

def read_file(path: str):
    try:
        if not os.path.isfile(path):
            return {"error": f"Not a file: {path}"}
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"path": path, "content": content, "size_bytes": os.path.getsize(path)}
    except Exception as e:
        return {"error": str(e)}

def create_file(path: str, content: str):
    try:
        parent = os.path.dirname(path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path, "size_bytes": os.path.getsize(path)}
    except Exception as e:
        return {"error": str(e)}

def search_files(query: str):
    try:
        results = []
        query_lower = query.lower()
        for root, dirs, files in os.walk(HOME_DIR):
            for fname in files:
                if query_lower in fname.lower():
                    full = os.path.join(root, fname)
                    try:
                        stat = os.stat(full)
                        results.append({
                            "name": fname,
                            "path": full,
                            "size_bytes": stat.st_size,
                            "size_display": _format_size(stat.st_size),
                            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        })
                    except Exception:
                        continue
                    if len(results) >= 50:
                        return results
        return results
    except Exception as e:
        return {"error": str(e)}

def delete_file(path: str, confirm: bool = False):
    if not confirm:
        return {"error": "Confirmation required. Set confirm=True to delete."}
    try:
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}
        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        else:
            os.remove(path)
        return {"success": True, "path": path, "action": "deleted"}
    except Exception as e:
        return {"error": str(e)}

def _check_code_safety(code: str):
    import ast
    code_lower = code.lower()
    blocked_imports = {"os", "sys", "subprocess", "shutil"}
    blocked_calls = {
        ("os", "system"), ("os", "popen"),
        ("subprocess", "run"), ("subprocess", "Popen"),
        ("subprocess", "call"), ("subprocess", "check_output"),
        ("subprocess", "check_call"), ("subprocess", "getoutput"),
        ("shutil", "rmtree"), ("shutil", "move"), ("shutil", "copy"),
        ("shutil", "copytree"), ("shutil", "remove"),
    }
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in blocked_imports:
                        return f"blocked import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module in blocked_imports:
                    return f"blocked import from: {node.module}"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec", "compile", "__import__"):
                        return f"blocked built-in: {node.func.id}"
                    if node.func.id == "open" and node.args:
                        if len(node.args) > 1:
                            mode_arg = node.args[1]
                            if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
                                if any(c in mode_arg.value for c in "wa+xb"):
                                    return "blocked: open with write mode"
                        else:
                            if any(isinstance(kw.arg, str) and kw.arg == "mode" for kw in node.keywords):
                                for kw in node.keywords:
                                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                                        if any(c in str(kw.value.value) for c in "wa+xb"):
                                            return "blocked: open with write mode"
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        key = (node.func.value.id, node.func.attr)
                        if key in blocked_calls:
                            return f"blocked: {'.'.join(key)}"
                        if node.func.value.id == "builtins" and node.func.attr in ("eval", "exec", "compile", "__import__", "open"):
                            return f"blocked: builtins.{node.func.attr}"
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "builtins" and node.attr in ("eval", "exec", "compile", "__import__", "open"):
                    return f"blocked: builtins.{node.attr}"
    except SyntaxError:
        pass
    if any(f" {kw}(" in code_lower for kw in ["eval", "exec", "compile", "__import__"]):
        for kw in ["eval", "exec", "compile", "__import__"]:
            if f" {kw}(" in code_lower or code_lower.startswith(f"{kw}("):
                return f"blocked built-in: {kw}"
    return None

def run_code(code: str):
    safety_violation = _check_code_safety(code)
    if safety_violation:
        return {"stdout": "", "stderr": f"SecurityError: {safety_violation}", "return_code": -1}
    tmp = None
    try:
        import ast
        ast.parse(code)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
        tmp.write(code)
        tmp.close()
        result = subprocess.run(
            [sys.executable, tmp.name],
            capture_output=True, text=True, timeout=10,
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "return_code": result.returncode}
    except SyntaxError as e:
        return {"stdout": "", "stderr": f"SyntaxError: {e}", "return_code": -1}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Execution timed out after 10 seconds", "return_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "return_code": -1}
    finally:
        if tmp and os.path.exists(tmp.name):
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

def screenshot():
    try:
        img = pyautogui.screenshot()
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        b64 = base64.b64encode(buffered.getvalue()).decode()
        return {
            "base64": b64,
            "width": img.width,
            "height": img.height,
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
