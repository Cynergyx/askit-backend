from src.prompts.query_prompt import get_query_prompt
from src.utils.llm_configuration import LLMConfig
from src.utils.exceptions import LLMNotConfiguredError

import logging
import json
from typing import List, Dict, Any



logger = logging.getLogger(__name__)

class SummaryGenerator:

    # This method generates insights and visualizations based on the query result.
    async def analyze(self, model: LLMConfig, original_question: str, query_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Generate the detailed analysis using the LLM for deep interpretation
        detailed_analysis = await self._generate_detailed_analysis(model, original_question, query_result)

        # If the analysis is a dict, use it directly; else, return as string with a warning
        if isinstance(detailed_analysis, dict):
            return detailed_analysis
        else:
            logger.warning("LLM analysis did not return structured JSON. Returning as string.")
            return detailed_analysis


    # This method generates a detailed analysis of the query result using the Gemini LLM.
    async def _generate_detailed_analysis(self, model: LLMConfig, question: str, data: List[Dict[str, Any]]):
        num_rows = len(data)
        if num_rows == 0:
            return "Based on the available data, I could not find any information to answer your question. The query returned no results."
        
        preview_limit = num_rows if num_rows < 5000 else 5000  # Allow a larger preview for analysis
        data_preview_str = json.dumps(data[:preview_limit], indent=2, default=str)
        prompt = get_query_prompt(question, data_preview_str)

        try:
            if not model:
                logger.error("LLM for query generator is not configured.")
                raise LLMNotConfiguredError("LLM for query generator is not configured.")
            response = model.generate_response(prompt)
            return response
        
        except Exception as e:
            logger.error(f"Failed to generate detailed analysis from Gemini: {e}")
            return f"The query to support your analysis returned {num_rows} result(s). A detailed analysis could not be generated at this time."

