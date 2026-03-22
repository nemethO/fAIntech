from flask import Blueprint

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Routes to implement:
# GET  /chat        - Chat page with AI assistant
# POST /chat/send   - Send message, get AI response (RAG pipeline)
# GET  /chat/history - Load chat history
