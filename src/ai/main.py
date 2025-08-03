import asyncio
from typing import List

# Import Pydantic models from the AI module's structure
from src.ai.models.query import NLQueryRequest
from src.ai.models.db import DBConnectionParams

# Import the core processing logic from the AI module
from src.ai.services.Database_AI.orchestrator import process_natural_language_query as run_orchestrator

# SecretStr is used to handle the already-decrypted password securely within Pydantic
from pydantic import SecretStr


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
        
        NOTE: Password decryption happens in the `UserDatabaseAccess.to_dict()` method
        before the data is passed to this function.
        """
        
        # 1. Translate Flask's db_credentials into the AI module's DBConnectionParams
        connections: List[DBConnectionParams] = []
        for cred in db_credentials:
            # The password in `cred` is already decrypted.
            # We wrap it in SecretStr for secure handling within the AI module's Pydantic models.
            params = DBConnectionParams(
                id=cred['data_source_id'],
                db_type=cred['type'],
                host=cred['host'],
                port=cred['port'],
                username=cred['username'],
                password=SecretStr(cred['password']),
                database=cred['database_name'],
            )
            connections.append(params)
            
        # 2. Construct the NLQueryRequest for the AI module.
        # This now includes the connections list directly.
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
            # Package the rest as metadata for potential frontend use
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
            # If the AI orchestrator handled the error, propagate its message
            raise Exception(f"AI Processing Error: {final_response.error_message}")