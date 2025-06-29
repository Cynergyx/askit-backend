import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICompute:
    @staticmethod
    def process_query(chat_id: str, user_query: str, db_credentials: list, enriched_schemas: dict, chat_history: list):
        """
        Receives all necessary information to process a user's query.
        
        Args:
            chat_id: The unique ID of the conversation.
            user_query: The user's latest question.
            db_credentials: A list of dictionaries with connection details.
            enriched_schemas: A dictionary where keys are data_source_ids and values
                              are the detailed, annotated schemas for those sources.
            chat_history: A list of previous messages for context.
            
        Returns:
            A tuple of (response_text, metadata_dict).
        """
        
        logger.info("--- AI COMPUTE CALLED ---")
        logger.info(f"Chat ID: {chat_id}")
        logger.info(f"User Query: {user_query}")
        logger.info(f"Received {len(db_credentials)} DB credentials.")
        logger.info(f"Received {len(enriched_schemas)} enriched schemas.")

        # Log the schema for verification (can be verbose)
        logger.info(f"Enriched Schemas Received: {json.dumps(enriched_schemas, indent=2)}")

        # Your actual AI logic now has much richer context
        # Example: Find a table or column description to help understand the query
        first_ds_id = db_credentials[0]['data_source_id']
        first_schema = enriched_schemas.get(first_ds_id, {})
        
        mock_response_text = f"Using the enriched schema for your databases, I have an answer to '{user_query}'."
        mock_metadata = {
            "sql_query_executed": "SELECT customer_name, order_total FROM sales WHERE sale_date > '2023-01-01';",
            "reasoning": "Used the 'sales' table, which is described as 'Contains all customer order information'.",
            "schema_used": first_schema,
            "confidence_score": 0.98
        }
        
        return mock_response_text, mock_metadata