"""
Module for interacting with OpenAI-compatible APIs (OpenAI, Groq, Ollama).
Includes the LLMClient class for sentiment analysis, summarization, and verdict generation.
"""
import json
import logging
import time
import re
from typing import Dict, List, Optional
from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError

logger = logging.getLogger(__name__)

class LLMClient:
    """
    A client for interfacing with OpenAI-compatible LLMs.
    
    Provides methods for analyzing individual review chunks and consolidating findings
    into a final product verdict. Implements exponential backoff for robust API interaction.
    """
    def __init__(self, api_key: str, base_url: str, model: str, max_retries: int = 3, initial_backoff: float = 2.0):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        
        self.system_prompt = (
            "You are a professional product review analyst. "
            "Analyze the following review and respond ONLY with a valid JSON object. "
            "The JSON must have exactly two keys: 'sentiment' and 'summary'. "
            "'sentiment' should be one of: 'Positive', 'Negative', or 'Neutral'. "
            "'summary' should be a concise 1-2 sentence summary of the review content."
        )

    def _call_api(self, text: str) -> str:
        """Calls the OpenAI API with exponential backoff on retryable errors."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Review content: \"\"\"{text}\"\"\""}
        ]
        
        backoff = self.initial_backoff
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=300
                )
                return response.choices[0].message.content
            except (RateLimitError, APIConnectionError) as e:
                if attempt == self.max_retries:
                    logger.error(f"Max retries reached. Error: {e}")
                    raise
                logger.warning(f"Retryable error: {e}. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2
            except APIStatusError as e:
                if e.status_code >= 500:
                    if attempt == self.max_retries:
                        logger.error(f"Server error {e.status_code}. Max retries reached.")
                        raise
                    logger.warning(f"Server error {e.status_code}. Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    # Non-retryable error (e.g. 401, 400)
                    logger.error(f"Non-retryable API error: {e.status_code} - {e.message}")
                    raise
        
        raise RuntimeError("API call failed after all retries.")

    def _parse_llm_response(self, content: str) -> Dict[str, str]:
        """Parses the JSON response from the LLM."""
        try:
            # Strip markdown formatting if present
            cleaned_content = re.sub(r'```json|```', '', content).strip()
            return json.loads(cleaned_content)
        except (json.JSONDecodeError, NameError) as e:
            # NameError might occur if 're' is not imported, but it's handled properly here
            import re
            cleaned_content = re.sub(r'```json|```', '', content).strip()
            try:
                return json.loads(cleaned_content)
            except Exception as e2:
                logger.warning(f"Failed to parse LLM response as JSON: {content[:300]}")
                return {
                    "sentiment": "Unknown",
                    "summary": content[:200] + "..." if len(content) > 200 else content
                }

    def analyze(self, chunks: List[str]) -> Dict[str, str]:
        """Analyzes multiple chunks and combines them if necessary."""
        if not chunks:
            return {"sentiment": "Unknown", "summary": "No content to analyze."}
        
        if len(chunks) == 1:
            raw_response = self._call_api(chunks[0])
            return self._parse_llm_response(raw_response)
        
        # Multiple chunks: analyze each then combine
        summaries = []
        sentiments = []
        for chunk in chunks:
            res = self._parse_llm_response(self._call_api(chunk))
            summaries.append(res.get("summary", ""))
            sentiments.append(res.get("sentiment", "Neutral"))
            
        # Combine summaries and make a final call
        combined_summaries = ". ".join(summaries)
        final_prompt = f"Combine these partial summaries into one coherent overall summary and sentiment: {combined_summaries}"
        
        try:
            # Reuse _call_api for final combination
            raw_final = self._call_api(final_prompt)
            return self._parse_llm_response(raw_final)
        except Exception as e:
            logger.error(f"Failed combining summaries: {e}")
            # Fallback: simple merge
            from collections import Counter
            most_common_sentiment = Counter(sentiments).most_common(1)[0][0]
            return {
                "sentiment": most_common_sentiment,
                "summary": combined_summaries[:500] + "..." if len(combined_summaries) > 500 else combined_summaries
            }

    def generate_final_verdict(self, reviews: List[object]) -> Dict[str, str]:
        """Generates a final overall product verdict based on all analyzed reviews."""
        if not reviews:
            return {"overall_sentiment": "Unknown", "verdict": "No reviews to analyze.", "recommendation": "Unknown"}
        
        # Compile all review data
        review_summaries = []
        recommendations = []
        for review in reviews:
            rec = getattr(review, 'recommended', 'Unknown')
            reason = getattr(review, 'recommendation_reason', '')
            if rec and rec != "Unknown":
                recommendations.append(f"- {rec}: {reason}")
            if hasattr(review, 'summary') and review.summary:
                review_summaries.append(review.summary)
        
        summaries_text = "\n".join(review_summaries)
        recommendations_text = "\n".join(recommendations) if recommendations else "No individual recommendations available."
        
        final_verdict_prompt = (
            f"Based on the following {len(reviews)} review summaries and individual recommendations, "
            f"provide a final overall product verdict including: (1) overall product quality assessment, "
            f"(2) key strengths, (3) key weaknesses, and (4) final recommendation (Yes/No) for potential buyers. "
            f"Respond ONLY with a valid JSON object with these exact keys: 'overall_sentiment', 'strengths', 'weaknesses', 'verdict', 'recommendation'. "
            f"\n\nReview Summaries:\n{summaries_text}\n\nIndividual Recommendations:\n{recommendations_text}"
        )
        
        try:
            raw_response = self._call_api(final_verdict_prompt)
            result = self._parse_llm_response(raw_response)
            # Ensure all keys exist
            return {
                "overall_sentiment": result.get("overall_sentiment", "Unknown"),
                "strengths": result.get("strengths", "Not determined"),
                "weaknesses": result.get("weaknesses", "Not determined"),
                "verdict": result.get("verdict", "Analysis complete."),
                "recommendation": result.get("recommendation", "Unknown")
            }
        except Exception as e:
            logger.error(f"Failed to generate final verdict: {e}")
            return {
                "overall_sentiment": "Unknown",
                "strengths": "Failed to generate verdict",
                "weaknesses": "Failed to generate verdict",
                "verdict": f"Error generating final verdict: {str(e)}",
                "recommendation": "Unknown"
            }
