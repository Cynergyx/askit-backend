import asyncio
from typing import List, Dict
from pydantic import SecretStr

# Import Pydantic models from the AI module's structure
from src.ai.models.query import NLQueryRequest
from src.ai.models.db import DBConnectionParams

# Import the core processing logic from the AI module
from src.ai.services.Database_AI.orchestrator import process_natural_language_query as run_orchestrator
from src.utils.security import DataEncryption
from flask import current_app

class AICompute:
    """
    This class is the primary interface between the main Flask application
    and the asynchronous AI query processing module.
    """
    
    @staticmethod
    async def process_query(chat_id: str, user_query: str, db_credentials: list, enriched_schemas: dict, chat_history: list):
        """
        Translates Flask app data into the Pydantic models required by the AI orchestrator,
        runs the orchestrator, and returns the result.
        
        Args:
            chat_id (str): The unique ID of the conversation.
            user_query (str): The user's latest question.
            db_credentials (list): A list of dictionaries with connection details from UserDatabaseAccess.
            enriched_schemas (dict): A dictionary of detailed, annotated schemas for the accessible databases.
            chat_history (list): A list of previous messages in the conversation for context.
            
        Returns:
            A tuple of (response_text, metadata_dict).
        """
        
        # 1. Translate Flask's db_credentials into the AI module's DBConnectionParams
        connections: List[DBConnectionParams] = []
        for cred in db_credentials:
            # The password in cred is already decrypted by the model's to_dict() method.
            # We must pass it as a SecretStr to the Pydantic model.
            params = DBConnectionParams(
                id=cred['data_source_id'],
                db_type=cred['type'],
                host=cred['host'],
                port=cred['port'],
                username=cred['username'],
                password=SecretStr(cred['password']),
                database=cred['database_name'],
                # We can add enriched schema here if the AI model supports it directly
                # For now, the orchestrator accepts schemas separately.
            )
            connections.append(params)
            
        # 2. Construct the FullQueryRequest for the AI module
        # Note: We are adapting to the AI module's expectation. It gets schema from the DB connection.
        # The `enriched_schemas` from our main app can be used in a future version to augment the prompt.
        request_payload = NLQueryRequest(
            question=user_query,
            chat_history=chat_history,
            connections=connections
        )

        # 3. Run the asynchronous orchestrator
        final_response = await run_orchestrator(request_payload)
        
        # 4. Process the response
        if final_response.success:
            # Extract the main text analysis for the chat content
            response_content = final_response.analysis
            # Package the rest as metadata
            metadata = {
                "response_type": final_response.response_type,
                "generated_query": final_response.generated_query,
                "execution_time_ms": final_response.execution_time_ms,
                "data": final_response.data,
                "visualization": final_response.visualization,
                "table_desc": final_response.table_desc
            }
            return response_content, metadata
        else:
            # If the AI orchestrator handled the error, propagate it
            raise Exception(f"AI Processing Error: {final_response.error_message}")