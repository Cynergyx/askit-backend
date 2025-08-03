import asyncio
from typing import List

from src.ai.models.query import NLQueryRequest
from src.ai.models.db import DBConnectionParams

from src.ai.services.Database_AI.orchestrator import process_natural_language_query as run_orchestrator

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
        
        connections: List[DBConnectionParams] = []
        for cred in db_credentials:
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
            
        request_payload = NLQueryRequest(
            question=user_query,
            chat_history=chat_history,
            connections=connections
        )

        final_response = await run_orchestrator(request_payload)
        
        if final_response.success:
            response_content = final_response.analysis
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
            raise Exception(f"AI Processing Error: {final_response.error_message}")