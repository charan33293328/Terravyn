from typing import List, Dict
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        # Maps device_id to a list of active websocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, device_id: int):
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = []
        self.active_connections[device_id].append(websocket)

    def disconnect(self, websocket: WebSocket, device_id: int):
        if device_id in self.active_connections:
            if websocket in self.active_connections[device_id]:
                self.active_connections[device_id].remove(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_device(self, device_id: int, message: dict):
        if device_id in self.active_connections:
            message_str = json.dumps(message, default=str)
            # Iterate over a copy to handle disconnections during broadcast
            for connection in self.active_connections[device_id][:]:
                try:
                    await connection.send_text(message_str)
                except Exception:
                    self.disconnect(connection, device_id)

manager = ConnectionManager()
