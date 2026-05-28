import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect

import tools
import scheduler

class WSManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = {}
        self.all_clients: set[WebSocket] = set()
        self._stats_tasks: dict[WebSocket, asyncio.Task] = {}

    async def connect(self, ws: WebSocket, session_id: str = "default"):
        await ws.accept()
        self.all_clients.add(ws)
        if session_id not in self.connections:
            self.connections[session_id] = set()
        self.connections[session_id].add(ws)
        task = asyncio.create_task(self._send_stats(ws))
        self._stats_tasks[ws] = task

    def disconnect(self, ws: WebSocket):
        self.all_clients.discard(ws)
        for session_set in self.connections.values():
            session_set.discard(ws)
        task = self._stats_tasks.pop(ws, None)
        if task:
            task.cancel()

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.all_clients:
            try:
                await ws.send_json(data)
            except:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to(self, ws: WebSocket, data: dict):
        try:
            await ws.send_json(data)
        except:
            self.disconnect(ws)

    async def _send_stats(self, ws: WebSocket):
        while True:
            try:
                stats = tools.get_system_stats()
                await ws.send_json({"type": "stats", "data": stats})
                reminders = await scheduler.check_reminders()
                for r in reminders:
                    await ws.send_json({"type": "reminder", "data": r})
            except:
                break
            await asyncio.sleep(5)

manager = WSManager()

async def handle_ws(ws: WebSocket, session_id: str, handle_message):
    await manager.connect(ws, session_id)
    try:
        while True:
            data = await ws.receive_json()
            msg = data.get("message", "").strip()
            if msg:
                await handle_message(ws, session_id, msg)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS] Error: {e}")
    finally:
        manager.disconnect(ws)
