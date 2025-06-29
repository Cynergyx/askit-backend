from flask import request, jsonify, g
from src.models.chat import ChatSession, ChatMessage
from src.extensions import db
from src.middleware.auth_middleware import jwt_required_with_org
from src.middleware.rbac_middleware import require_permission
from src.services.audit_service import AuditService
from src.services.schema_service import SchemaService
from src.ai.main import AICompute

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

        # 1. Save user's message
        user_message = ChatMessage(session_id=session.id, sender='user', content=user_query)
        db.session.add(user_message)

        # 2. Get user's database credentials AND enriched schemas
        db_accesses = g.current_user.database_accesses.all()
        if not db_accesses:
            return jsonify({'message': 'You do not have access to any databases to query.'}), 403

        db_credentials = []
        enriched_schemas = {}
        for access in db_accesses:
            db_credentials.append(access.to_dict())
            try:
                enriched_schemas[access.data_source_id] = SchemaService.get_enriched_schema(access.data_source_id)
            
            except Exception as e:
                # If a schema fails to load, we can decide to fail or just log and continue
                print(f"Warning: Could not load schema for data source {access.data_source_id}: {e}")
                enriched_schemas[access.data_source_id] = {"error": "Could not load schema"}


        # 3. Get chat history for context
        # We limit history to prevent overly large payloads to the AI
        chat_history = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at.desc()).limit(10).all()
        chat_history.reverse()
        
        # 4. Pass all info to the AI compute module
        try:
            ai_response_content, ai_metadata = AICompute.process_query(
                chat_id=session.id,
                user_query=user_query,
                db_credentials=db_credentials,
                enriched_schemas=enriched_schemas,
                chat_history=[msg.to_dict() for msg in chat_history]
            )
        except Exception as e:
            # Log the error and return a friendly message
            db.session.rollback()
            print(f"AI processing failed: {e}")
            return jsonify({'message': 'An error occurred while processing your request with the AI agent.'}), 500

        # 5. Save AI's response
        ai_message = ChatMessage(session_id=session.id, sender='ai', content=ai_response_content, metadata=ai_metadata)
        db.session.add(ai_message)

        # 6. Commit transaction
        db.session.commit()

        AuditService.log_action(
            user_id=g.current_user.id,
            organization_id=g.current_organization.id,
            action='CHAT_MESSAGE_POSTED',
            resource_type='chat_session',
            resource_id=session.id,
            details={'query_length': len(user_query)}
        )

        # 7. Return AI's response to the user
        return jsonify(ai_message.to_dict()), 200