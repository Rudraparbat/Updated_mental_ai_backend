from collections import defaultdict
from fastapi import FastAPI , HTTPException , Depends , File , Form , UploadFile , Request , Response , WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse 
from db.models import *
from db.database import *
from sqlalchemy.orm import Session
from pydantic import BaseModel , Field
import random
import auth
from middlewares import *
from uuid import UUID
from ai.ai import *
from ai.ai_mind import *
from consumer import *
from middlewares.http_middlewares import *
from middlewares.websocket_middleware import *
from fastapi.middleware.cors import CORSMiddleware

# Creating The App
app = FastAPI()
# include router
app.include_router(auth.router)


# set the origins
allow_origin = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://mental-health-bot-eight.vercel.app/"
]
# include middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(RateLimiterMiddleware)

# bind the engine 
Base.metadata.create_all(bind = engine)

# start Db session

def get_db() :
    try :
        # Initializing db session
        db = Sessions()
        yield db
    finally :
        # Close The db session
        db.close()

# We are using pydantic for data vallidaTIon



@app.get('/')
async def index(request : Request , db : Session = Depends(get_db) ) :
    response = {
        "user data" : request.state.user,
        "user ip address" : request.state.ip_address, 
        "message" : "user Data for that user" 
    }
    return response



# binding connections
manager = ConnectionManager()

  
html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>WebSocket Chat</title>
  <link rel="stylesheet" href="style.css">
</head>
<style>
body {
  background: #121212;
  color: #f0f0f0;
  font-family: Arial, sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  margin: 0;
}

.chat-container {
  width: 400px;
  background: #1e1e1e;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.chat-header {
  background: #333;
  padding: 10px;
  font-size: 18px;
  text-align: center;
}

.chat-box {
  height: 300px;
  overflow-y: auto;
  padding: 10px;
  border-top: 1px solid #333;
  border-bottom: 1px solid #333;
}

.chat-box div {
  margin-bottom: 10px;
}

.input-area {
  display: flex;
  border-top: 1px solid #333;
}

#messageInput {
  flex: 1;
  padding: 10px;
  border: none;
  outline: none;
  background: #2a2a2a;
  color: #fff;
}

button {
  padding: 10px 15px;
  background: #ffb300;
  color: #000;
  border: none;
  cursor: pointer;
}

</style>
<body>
  <div class="chat-container">
    <div class="chat-header">WebSocket Chat</div>
    <div id="chat-box" class="chat-box"></div>
    <div class="input-area">
      <input type="text" id="messageInput" placeholder="Type a message...">
      <button onclick="sendMessage()">Send</button>
    </div>
  </div>

  <script>
  // Replace this with your actual WebSocket endpoint
  let ids = 1233333333
  console.log(ids)
const socket = new WebSocket(`wss://menatl-bot-service.onrender.com/ws/chat/`);

const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("messageInput");

socket.onopen = () => {
  appendMessage("✅ Connected to server");
};

socket.onmessage = (event) => {
  appendMessage("📩 Server: " + event.data);
};

socket.onclose = () => {
  appendMessage("❌ Disconnected from server");
};

socket.onerror = (error) => {
  console.error("WebSocket error:", error);
  appendMessage("⚠️ WebSocket error");
};

function sendMessage() {
  const message = messageInput.value.trim();
  if (message) {
    socket.send(message);
    appendMessage("📤 You: " + message);
    messageInput.value = "";
  }
}

function appendMessage(msg) {
  const msgDiv = document.createElement("div");
  msgDiv.textContent = msg;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}
</script>
</body>
</html>
"""

@app.get("/chatpage/") 
async def htmlview() :
    return HTMLResponse(html)


# webcoket api endpoint
@app.websocket("/ws/chat/") 
@websocket_auth
async def websocketendpoint(websocket : WebSocket) :
    # accept the wesocket conn
    await websocket.accept() 
    print("socket binded user is",websocket.state.user)
    await manager.connect(websocket.state.user , websocket)
    try :
        while True :
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect :
        await manager.disconnect(websocket)
