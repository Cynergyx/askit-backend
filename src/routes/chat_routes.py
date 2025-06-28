from flask import Blueprint
from src.controllers.chat_controller import ChatController

chat_bp = Blueprint('chat', __name__)

# Manage chat sessions
chat_bp.add_url_rule('/sessions', 'create_chat_session', ChatController.create_chat_session, methods=['POST'])
chat_bp.add_url_rule('/sessions', 'get_user_chat_sessions', ChatController.get_user_chat_sessions, methods=['GET'])

# Interact with a specific chat session
chat_bp.add_url_rule('/sessions/<session_id>/messages', 'get_chat_history', ChatController.get_chat_history, methods=['GET'])
chat_bp.add_url_rule('/sessions/<session_id>/messages', 'post_message', ChatController.post_message, methods=['POST'])