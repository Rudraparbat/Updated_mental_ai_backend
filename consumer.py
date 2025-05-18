from fastapi import FastAPI , WebSocket
from ai.ai import *
from collections import defaultdict


class ConnectionManager :
  def __init__(self):
      self.active_user : dict[str, list[WebSocket]] = defaultdict(list)

  async def connect(self , user : dict ,  websocket : WebSocket) :
      self.chat_room_id = f"AIBOT{user.get("username")}{user.get("id")}"
      self.psychologist = Psychologist(self.chat_room_id)
      self.active_user[self.chat_room_id].append(websocket)

  async def disconnect(self , websocket : WebSocket) :
      self.psychologist.Delete_user_data()
      self.active_user[self.chat_room_id].remove(websocket)

  async def broadcast(self ,  message : str) :
      for connections in self.active_user[self.chat_room_id] :
          ai_answer = await self.psychologist.ask(message)
          try:
            await connections.send_text(ai_answer)
          except Exception as e:
            print("Failed to send message:", e)