from flask import request, jsonify, g
from src.models.chat import ChatSession, ChatMessage
from src.extensions import db
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService
from src.services.schema_service import SchemaService
from src.controllers.ai_controller import AICompute
import asyncio

class ChatController:

    @staticmethod
    @jwt_required_with_org
    @require_permission('chat.create')
    def create_chat_session():
        """Creates a new chat session for the current user."""
        data = request.get_json()
        title = data.get('title')

        new_session = ChatSession(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            title=title
        )
        db.session.add(new_session)
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='CHAT_SESSION_CREATED',
            resource_type='chat_session',
            resource_id=new_session.id
        )

        return jsonify(new_session.to_dict()), 201

    @staticmethod
    @jwt_required_with_org
    @require_permission('chat.read')
    def get_user_chat_sessions():
        """Gets all chat sessions for the current user."""
        sessions = ChatSession.query.filter_by(user_id=g.current_user.id).order_by(ChatSession.created_at.desc()).all()
        return jsonify([session.to_dict() for session in sessions]), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('chat.read')
    def get_chat_history(session_id):
        """Gets all messages for a specific chat session."""
        session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first()
        if not session:
            return jsonify({'message': 'Chat session not found or access denied'}), 404
        
        return jsonify([message.to_dict() for message in session.messages]), 200

    @staticmethod
    @jwt_required_with_org
    @require_permission('chat.create')
    def post_message(session_id):
        """Posts a message to a chat, gets a response from the AI, and returns it."""
        session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first()
        if not session:
            return jsonify({'message': 'Chat session not found or access denied'}), 404
        
        data = request.get_json()
        user_query = data.get('query')
        if not user_query:
            return jsonify({'message': 'Query is required'}), 400

        user_message = ChatMessage(session_id=session.id, sender='user', content=user_query)
        db.session.add(user_message)

        db_accesses = g.current_user.database_accesses.all()
        # if not db_accesses:
        #     return jsonify({'message': 'You do not have access to any databases to query.'}), 403
        
        db_credentials = [access.to_dict() for access in db_accesses]
        
        chat_history_models = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at.desc()).limit(10).all()
        chat_history_models.reverse()
        chat_history = [msg.to_dict() for msg in chat_history_models]
        
        try:
            # Run the async AI orchestrator from our sync Flask route
            ai_response_content, ai_metadata = asyncio.run(AICompute.process_query(
                chat_id=session.id,
                user_query=user_query,
                db_credentials=db_credentials,
                enriched_schemas={}, # Pass enriched schemas if available, for now it's empty
                chat_history=chat_history
            ))
        except Exception as e:
            db.session.rollback()
            print(f"AI processing failed: {e}")
            return jsonify({'message': str(e)}), 500

        ai_message = ChatMessage(session_id=session.id, sender='ai', content=ai_response_content, ai_metadata=ai_metadata)
        db.session.add(ai_message)
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='CHAT_MESSAGE_POSTED',
            resource_type='chat_session',
            resource_id=session.id
        )
        response_message = ai_message.to_dict()
        return jsonify(response_message['content']), 200