"""Claude AI document analysis service."""
import logging
from typing import Optional
from anthropic import Anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ClaudeAnalyzer:
    """Service for analyzing documents using Claude AI."""

    def __init__(self):
        """Initialize Claude client."""
        self.client = None
        if settings.anthropic_api_key:
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    def is_available(self) -> bool:
        """Check if Claude API is configured."""
        return self.client is not None

    async def summarize(self, text: str, max_length: int = 500) -> Optional[str]:
        """
        Generate a summary of the document text.

        Args:
            text: Document text to summarize
            max_length: Target summary length in words

        Returns:
            Summary text or None if failed
        """
        if not self.is_available():
            logger.warning("Claude API not configured")
            return None

        try:
            # Truncate very long documents
            if len(text) > 100000:
                text = text[:100000] + "\n\n[Document truncated for analysis...]"

            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Please provide a concise summary of the following legal document in approximately {max_length} words. Focus on:
- Key parties involved
- Main purpose/subject matter
- Important dates or deadlines
- Key obligations or terms
- Any notable clauses or conditions

Document:
{text}"""
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return None

    async def extract_key_terms(self, text: str) -> Optional[dict]:
        """
        Extract key terms and entities from document.

        Args:
            text: Document text to analyze

        Returns:
            Dictionary of extracted information or None if failed
        """
        if not self.is_available():
            logger.warning("Claude API not configured")
            return None

        try:
            if len(text) > 100000:
                text = text[:100000]

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this legal document and extract the following information in JSON format:
{{
    "document_type": "type of legal document (contract, agreement, etc.)",
    "parties": ["list of parties involved"],
    "effective_date": "date if found or null",
    "expiration_date": "date if found or null",
    "key_terms": ["list of important terms/clauses"],
    "obligations": ["list of key obligations"],
    "monetary_values": ["any dollar amounts or fees mentioned"],
    "jurisdiction": "governing law/jurisdiction if mentioned",
    "risk_factors": ["potential risks or concerns identified"]
}}

Document:
{text}"""
                    }
                ]
            )

            # Parse JSON from response
            response_text = message.content[0].text
            # Try to extract JSON from the response
            import json
            # Find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
            return {"raw_analysis": response_text}
        except Exception as e:
            logger.error(f"Error extracting key terms: {e}")
            return None

    async def answer_question(self, text: str, question: str) -> Optional[str]:
        """
        Answer a question about the document.

        Args:
            text: Document text
            question: User's question

        Returns:
            Answer text or None if failed
        """
        if not self.is_available():
            logger.warning("Claude API not configured")
            return None

        try:
            if len(text) > 100000:
                text = text[:100000]

            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Based on the following legal document, please answer this question:

Question: {question}

Document:
{text}

Please provide a clear, accurate answer based only on the information in the document. If the answer cannot be determined from the document, say so."""
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return None

    async def analyze_risks(self, text: str) -> Optional[str]:
        """
        Analyze potential risks in the document.

        Args:
            text: Document text

        Returns:
            Risk analysis or None if failed
        """
        if not self.is_available():
            logger.warning("Claude API not configured")
            return None

        try:
            if len(text) > 100000:
                text = text[:100000]

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": f"""As a legal document analyst, review this document and identify potential risks, concerns, or areas that may need attention. Consider:

1. Unfavorable terms or conditions
2. Missing standard protections
3. Ambiguous language
4. Unusual clauses
5. Compliance concerns
6. Financial risks
7. Liability exposure

Document:
{text}

Provide a structured risk analysis with severity levels (High/Medium/Low) for each identified issue."""
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error analyzing risks: {e}")
            return None


# Singleton instance
_analyzer = None


def get_claude_analyzer() -> ClaudeAnalyzer:
    """Get Claude analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ClaudeAnalyzer()
    return _analyzer
