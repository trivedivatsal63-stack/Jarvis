import os
import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

HA_URL = os.getenv("HA_URL", "")
HA_TOKEN = os.getenv("HA_TOKEN", "")
HUE_BRIDGE_IP = os.getenv("HUE_BRIDGE_IP", "")
HUE_API_KEY = os.getenv("HUE_API_KEY", "")
KASA_IPS = os.getenv("KASA_DEVICES", "")

USEFUL_DOMAINS = {"light", "switch", "sensor", "climate", "lock", "cover", "binary_sensor"}


def _ha_configured():
    return bool(HA_URL and HA_TOKEN and REQUESTS_AVAILABLE)


def _ha_headers():
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }


def get_devices():
    if not _ha_configured():
        return {"available": False, "message": "Home Assistant not configured"}
    try:
        resp = requests.get(f"{HA_URL}/api/states", headers=_ha_headers(), timeout=10)
        resp.raise_for_status()
        all_states = resp.json()
        devices = []
        for entity in all_states:
            entity_id = entity.get("entity_id", "")
            domain = entity_id.split(".")[0] if "." in entity_id else ""
            if domain not in USEFUL_DOMAINS:
                continue
            attrs = entity.get("attributes", {})
            devices.append({
                "entity_id": entity_id,
                "state": entity.get("state", ""),
                "friendly_name": attrs.get("friendly_name", entity_id),
                "attributes": attrs,
            })
        return devices
    except requests.RequestException as e:
        return {"error": f"Failed to fetch devices: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def control_device(entity_id, action, **params):
    if not _ha_configured():
        return {"error": "Home Assistant not configured"}
    domain = entity_id.split(".")[0] if "." in entity_id else "light"
    valid_actions = {"turn_on", "turn_off", "toggle"}
    if action not in valid_actions:
        return {"error": f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"}
    try:
        service_data = {"entity_id": entity_id}
        if action == "turn_on":
            if "brightness" in params:
                service_data["brightness"] = max(0, min(255, int(params["brightness"])))
            if "temperature" in params and domain == "climate":
                service_data["temperature"] = float(params["temperature"])
            if "position" in params and domain == "cover":
                service_data["position"] = max(0, min(100, int(params["position"])))
        url = f"{HA_URL}/api/services/{domain}/{action}"
        resp = requests.post(url, headers=_ha_headers(), json=service_data, timeout=10)
        resp.raise_for_status()
        return {"success": True, "entity_id": entity_id, "action": action}
    except requests.RequestException as e:
        return {"error": f"Failed to control device: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def get_status():
    if not _ha_configured():
        return {"error": "Home Assistant not configured"}
    devices = get_devices()
    if isinstance(devices, dict) and "error" in devices:
        return devices
    grouped = {"lights": [], "switches": [], "sensors": [], "climate": []}
    for d in devices:
        domain = d["entity_id"].split(".")[0]
        entry = {"entity_id": d["entity_id"], "state": d["state"], "friendly_name": d["friendly_name"]}
        if domain == "light":
            grouped["lights"].append(entry)
        elif domain == "switch":
            grouped["switches"].append(entry)
        elif domain in ("sensor", "binary_sensor"):
            grouped["sensors"].append(entry)
        elif domain == "climate":
            grouped["climate"].append(entry)
    return grouped


def hue_lights():
    if not (HUE_BRIDGE_IP and HUE_API_KEY and REQUESTS_AVAILABLE):
        return {"available": False, "message": "Philips Hue not configured"}
    try:
        url = f"http://{HUE_BRIDGE_IP}/api/{HUE_API_KEY}/lights"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        lights = []
        for lid, info in data.items():
            state = info.get("state", {})
            lights.append({
                "id": lid,
                "name": info.get("name", f"Light {lid}"),
                "on": state.get("on", False),
                "brightness": state.get("bri"),
                "hue": state.get("hue"),
                "saturation": state.get("sat"),
            })
        return lights
    except requests.RequestException as e:
        return {"error": f"Hue connection failed: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def hue_control(light_id, turn_on=True, brightness=None):
    if not (HUE_BRIDGE_IP and HUE_API_KEY and REQUESTS_AVAILABLE):
        return {"error": "Philips Hue not configured"}
    try:
        body = {"on": turn_on}
        if brightness is not None:
            body["bri"] = max(0, min(255, int(brightness)))
        url = f"http://{HUE_BRIDGE_IP}/api/{HUE_API_KEY}/lights/{light_id}/state"
        resp = requests.put(url, json=body, timeout=5)
        resp.raise_for_status()
        return {"success": True, "light_id": light_id, "on": turn_on}
    except requests.RequestException as e:
        return {"error": f"Hue control failed: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def kasa_devices():
    if not KASA_IPS:
        return {"available": False, "message": "Kasa devices not configured"}
    try:
        from kasa import SmartPlug
        import asyncio
    except ImportError:
        return {"available": False, "message": "python-kasa library not installed"}

    ips = [ip.strip() for ip in KASA_IPS.split(",") if ip.strip()]

    async def _get_all():
        results = []
        for ip in ips:
            try:
                plug = SmartPlug(ip)
                await plug.update()
                results.append({
                    "ip": ip,
                    "alias": plug.alias,
                    "on": plug.is_on,
                    "consumption": plug.emeter_realtime.power if plug.has_emeter else None,
                })
            except Exception as e:
                results.append({"ip": ip, "error": str(e)})
        return results

    try:
        return asyncio.run(_get_all())
    except Exception as e:
        return {"error": str(e)}


def kasa_control(ip, turn_on=True):
    try:
        from kasa import SmartPlug
        import asyncio
    except ImportError:
        return {"error": "python-kasa library not installed"}

    async def _control():
        try:
            plug = SmartPlug(ip)
            await plug.update()
            if turn_on:
                await plug.turn_on()
            else:
                await plug.turn_off()
            return {"success": True, "ip": ip, "on": turn_on}
        except Exception as e:
            return {"error": str(e)}

    try:
        return asyncio.run(_control())
    except Exception as e:
        return {"error": str(e)}
