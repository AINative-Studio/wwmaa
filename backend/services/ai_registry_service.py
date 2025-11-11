"""
AI Registry Service for WWMAA Backend

Integrates with AINative AI Registry for LLM operations including
question answering, content generation, and RAG (Retrieval Augmented Generation).

Features:
- LLM-powered question answering
- Context-aware response generation
- Related query suggestions
- Response streaming support
- Model selection and routing
- Retry logic with exponential backoff
- Cost tracking and optimization

Dependencies:
- AINative AI Registry API
- US-037 implementation
"""

import logging
import time
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
from datetime import datetime
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import tiktoken
except ImportError:
    tiktoken = None
    logger.warning("tiktoken not installed. Token counting will use estimates.")

from backend.config import get_settings
from backend.services.zerodb_service import ZeroDBClient

# Configure logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class AIRegistryError(Exception):
    """Base exception for AI Registry operations"""
    pass


class AIRegistryRateLimitError(AIRegistryError):
    """Exception raised for rate limit errors"""
    pass


class TokenLimitExceededError(AIRegistryError):
    """Exception raised when token limit is exceeded"""
    pass


# Token pricing per 1K tokens (USD)
MODEL_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
}

# Token limits by model
MODEL_TOKEN_LIMITS = {
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-4o-mini": 128000,
    "gpt-3.5-turbo": 16384,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
}

# Available prompt templates
PROMPT_TEMPLATES = {
    "general": "martial_arts_general.txt",
    "technique": "technique_explanation.txt",
    "history": "history_philosophy.txt",
    "training": "training_recommendations.txt",
}


class AIRegistryService:
    """
    Service for interacting with AINative AI Registry.

    Provides methods for:
    - Question answering with context (RAG)
    - Response generation
    - Related query suggestions
    - Model selection and routing
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.ainative.studio",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize AI Registry service.

        Args:
            api_key: AINative API key (defaults to settings.AINATIVE_API_KEY or AI_REGISTRY_API_KEY)
            base_url: AINative API base URL
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries (default: 3)
        """
        # Try both API keys for backward compatibility
        self.api_key = (
            api_key or
            getattr(settings, 'AI_REGISTRY_API_KEY', None) or
            settings.AINATIVE_API_KEY
        )
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

        # Load model settings
        self.primary_model = getattr(settings, 'AI_REGISTRY_MODEL', 'gpt-4')
        self.fallback_model = getattr(settings, 'AI_REGISTRY_FALLBACK_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = getattr(settings, 'AI_REGISTRY_MAX_TOKENS', 2000)
        self.temperature = getattr(settings, 'AI_REGISTRY_TEMPERATURE', 0.7)

        if not self.api_key:
            raise AIRegistryError("AI_REGISTRY_API_KEY or AINATIVE_API_KEY is required")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Configure session with retry logic
        self.session = self._create_session(max_retries)

        # Initialize ZeroDB client for cost tracking
        try:
            self.zerodb = ZeroDBClient()
            self.cost_tracking_enabled = True
        except Exception as e:
            logger.warning(f"ZeroDB not available for cost tracking: {e}")
            self.zerodb = None
            self.cost_tracking_enabled = False

        # Load prompt templates
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self._prompt_cache = {}

        logger.info(
            f"AIRegistryService initialized with base_url: {self.base_url}, "
            f"model: {self.primary_model}, fallback: {self.fallback_model}"
        )

    def _create_session(self, max_retries: int) -> requests.Session:
        """
        Create requests session with retry logic.

        Args:
            max_retries: Maximum number of retries

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load a prompt template from file.

        Args:
            template_name: Name of the template (general, technique, history, training)

        Returns:
            Template content as string

        Raises:
            AIRegistryError: If template not found
        """
        # Check cache first
        if template_name in self._prompt_cache:
            return self._prompt_cache[template_name]

        # Validate template name
        if template_name not in PROMPT_TEMPLATES:
            raise AIRegistryError(
                f"Unknown template: {template_name}. "
                f"Available: {', '.join(PROMPT_TEMPLATES.keys())}"
            )

        # Load from file
        template_file = self.prompts_dir / PROMPT_TEMPLATES[template_name]

        if not template_file.exists():
            raise AIRegistryError(f"Template file not found: {template_file}")

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Cache the template
            self._prompt_cache[template_name] = template_content

            logger.debug(f"Loaded template: {template_name}")
            return template_content

        except Exception as e:
            raise AIRegistryError(f"Error loading template {template_name}: {str(e)}")

    def format_prompt_template(
        self,
        template_name: str,
        query: str,
        context: str = ""
    ) -> str:
        """
        Format a prompt template with query and context.

        Args:
            template_name: Name of the template to use
            query: User's question or request
            context: Additional context (optional)

        Returns:
            Formatted prompt string
        """
        template = self._load_prompt_template(template_name)

        # Replace placeholders
        formatted_prompt = template.replace("{query}", query)
        formatted_prompt = formatted_prompt.replace("{context}", context)

        return formatted_prompt

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for
            model: Model name (defaults to self.primary_model)

        Returns:
            Number of tokens
        """
        if model is None:
            model = self.primary_model

        if tiktoken is None:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

        try:
            # Get encoding for model
            if model.startswith("gpt-4"):
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif model.startswith("gpt-3.5"):
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Default to cl100k_base for other models
                encoding = tiktoken.get_encoding("cl100k_base")

            tokens = encoding.encode(text)
            return len(tokens)

        except Exception as e:
            logger.warning(f"Error counting tokens: {e}. Using estimate.")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def trim_context_to_limit(
        self,
        prompt: str,
        max_prompt_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Trim prompt to fit within token limits.

        Args:
            prompt: Prompt text to trim
            max_prompt_tokens: Maximum tokens allowed (defaults to model limit - max_tokens)
            model: Model name (defaults to self.primary_model)

        Returns:
            Trimmed prompt
        """
        if model is None:
            model = self.primary_model

        if max_prompt_tokens is None:
            model_limit = MODEL_TOKEN_LIMITS.get(model, 4096)
            max_prompt_tokens = model_limit - self.max_tokens

        current_tokens = self.count_tokens(prompt, model)

        if current_tokens <= max_prompt_tokens:
            return prompt

        logger.warning(
            f"Prompt exceeds token limit ({current_tokens} > {max_prompt_tokens}). Trimming..."
        )

        # Trim from the middle (preserve instructions and question)
        lines = prompt.split('\n')

        # Keep first 30% and last 30% of lines
        keep_start = max(1, int(len(lines) * 0.3))
        keep_end = max(1, int(len(lines) * 0.3))

        trimmed_lines = (
            lines[:keep_start] +
            ["\n[... context trimmed for length ...]\n"] +
            lines[-keep_end:]
        )

        trimmed_prompt = '\n'.join(trimmed_lines)

        # Verify it's within limits
        trimmed_tokens = self.count_tokens(trimmed_prompt, model)
        logger.info(f"Trimmed prompt from {current_tokens} to {trimmed_tokens} tokens")

        return trimmed_prompt

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name (defaults to self.primary_model)

        Returns:
            Cost in USD
        """
        if model is None:
            model = self.primary_model

        pricing = MODEL_PRICING.get(model, {"input": 0.03, "output": 0.06})

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def _track_request(
        self,
        prompt: str,
        response: str,
        model: str,
        template_name: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track AI request in ZeroDB for cost monitoring and analytics.

        Args:
            prompt: Input prompt
            response: Model response
            model: Model used
            template_name: Template used (if any)
            success: Whether request succeeded
            error: Error message if failed
            metadata: Additional metadata
        """
        if not self.cost_tracking_enabled:
            return

        try:
            input_tokens = self.count_tokens(prompt, model)
            output_tokens = self.count_tokens(response, model) if response else 0
            cost = self.calculate_cost(input_tokens, output_tokens, model)

            request_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "model": model,
                "template": template_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": cost,
                "success": success,
                "error": error,
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "response_preview": response[:200] + "..." if response and len(response) > 200 else response,
                "metadata": metadata or {}
            }

            # Store in ZeroDB
            self.zerodb.create(
                collection="ai_requests",
                data=request_data
            )

            logger.info(
                f"AI request tracked: model={model}, tokens={input_tokens + output_tokens}, "
                f"cost=${cost:.4f}, success={success}"
            )

        except Exception as e:
            logger.error(f"Error tracking AI request: {e}")

    def generate_answer(
        self,
        query: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate an answer to a query using context from vector search.

        This implements RAG (Retrieval Augmented Generation) by combining
        retrieved context with LLM generation.

        Args:
            query: User's search query
            context: List of relevant documents from vector search
            system_prompt: Optional system prompt to guide the LLM
            model: LLM model to use (default: gpt-4o-mini)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens in response (default: 1000)

        Returns:
            Dictionary containing:
            - answer: Generated markdown answer
            - model: Model used for generation
            - tokens_used: Number of tokens consumed
            - latency_ms: Generation latency

        Raises:
            AIRegistryError: If generation fails
        """
        try:
            logger.info(f"Generating answer for query: '{query[:50]}...'")

            # Build system prompt if not provided
            if not system_prompt:
                system_prompt = self._build_default_system_prompt()

            # Build context string from documents
            context_text = self._format_context(context)

            # Build user message with context
            user_message = f"""Context from martial arts database:
{context_text}

User question: {query}

Please provide a comprehensive answer based on the context above. Format your response in markdown."""

            # Prepare request payload
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Make API request
            start_time = time.time()
            url = f"{self.base_url}/v1/chat/completions"

            response = self.session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract answer from response
            answer = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

            logger.info(
                f"Answer generated successfully in {latency_ms}ms "
                f"(tokens: {tokens_used})"
            )

            # Track request for cost monitoring
            self._track_request(
                prompt=user_message,
                response=answer,
                model=model,
                template_name=None,
                success=True,
                metadata={"query": query[:100], "latency_ms": latency_ms}
            )

            return {
                "answer": answer,
                "model": model,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"AI Registry API error: {e}")
            self._track_request(
                prompt=user_message if 'user_message' in locals() else query,
                response="",
                model=model,
                success=False,
                error=str(e)
            )
            raise AIRegistryError(f"Failed to generate answer: {e}")
        except Exception as e:
            logger.error(f"Unexpected error generating answer: {e}")
            self._track_request(
                prompt=user_message if 'user_message' in locals() else query,
                response="",
                model=model,
                success=False,
                error=str(e)
            )
            raise AIRegistryError(f"Answer generation failed: {e}")

    def generate_related_queries(
        self,
        query: str,
        count: int = 3,
        model: str = "gpt-4o-mini"
    ) -> List[str]:
        """
        Generate related search queries based on the original query.

        Args:
            query: Original search query
            count: Number of related queries to generate (default: 3)
            model: LLM model to use

        Returns:
            List of related query strings

        Raises:
            AIRegistryError: If generation fails
        """
        try:
            logger.info(f"Generating {count} related queries for: '{query[:50]}...'")

            system_prompt = """You are a helpful assistant that generates related search queries.
Given a martial arts search query, generate related queries that users might also be interested in.
Return only the queries, one per line, without numbering or explanation."""

            user_message = f"""Original query: {query}

Generate {count} related martial arts search queries."""

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.8,
                "max_tokens": 200
            }

            url = f"{self.base_url}/v1/chat/completions"

            response = self.session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract and parse related queries
            content = result["choices"][0]["message"]["content"]
            related_queries = [
                q.strip()
                for q in content.strip().split('\n')
                if q.strip() and not q.strip().startswith('#')
            ][:count]

            logger.info(f"Generated {len(related_queries)} related queries")

            return related_queries

        except requests.exceptions.RequestException as e:
            logger.error(f"AI Registry API error: {e}")
            # Return empty list on error rather than failing
            logger.warning("Returning empty related queries list due to error")
            return []
        except Exception as e:
            logger.error(f"Unexpected error generating related queries: {e}")
            return []

    def _build_default_system_prompt(self) -> str:
        """
        Build default system prompt for question answering.

        Returns:
            System prompt string
        """
        return """You are a knowledgeable martial arts expert and instructor assistant for the Women's Martial Arts Association of America (WWMAA).

Your role is to:
- Provide accurate, helpful information about martial arts techniques, training, events, and resources
- Answer questions based on the provided context from the WWMAA database
- Be encouraging and supportive, especially to women and beginners in martial arts
- Cite specific events, articles, or resources when relevant
- Admit when you don't have enough information to answer fully

Format your responses in clear markdown with:
- Headings for organization
- Bullet points for lists
- Bold for emphasis on key terms
- Links to relevant resources when available

Keep answers concise but comprehensive, typically 200-400 words."""

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """
        Format context documents into a string for the LLM.

        Args:
            context: List of documents from vector search

        Returns:
            Formatted context string
        """
        if not context:
            return "No specific context available."

        formatted_parts = []

        for i, doc in enumerate(context, 1):
            data = doc.get("data", {})
            source_type = doc.get("source_collection", "document")

            # Extract relevant fields based on document type
            title = (
                data.get("title") or
                data.get("name") or
                data.get("event_name") or
                f"{source_type} {i}"
            )

            content = (
                data.get("description") or
                data.get("content") or
                data.get("summary") or
                ""
            )

            # Build formatted entry
            entry = f"""[{i}] {title} ({source_type})
{content}
"""
            formatted_parts.append(entry)

        return "\n---\n".join(formatted_parts)

    def stream_answer(
        self,
        query: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7
    ) -> Iterator[str]:
        """
        Stream an answer to a query using context from vector search.

        This is similar to generate_answer but streams the response
        for better user experience on long answers.

        Args:
            query: User's search query
            context: List of relevant documents from vector search
            system_prompt: Optional system prompt
            model: LLM model to use
            temperature: Sampling temperature

        Yields:
            Chunks of the generated answer as they arrive

        Raises:
            AIRegistryError: If streaming fails
        """
        try:
            logger.info(f"Streaming answer for query: '{query[:50]}...'")

            # Build system prompt if not provided
            if not system_prompt:
                system_prompt = self._build_default_system_prompt()

            # Build context string
            context_text = self._format_context(context)

            # Build user message
            user_message = f"""Context from martial arts database:
{context_text}

User question: {query}

Please provide a comprehensive answer based on the context above. Format your response in markdown."""

            # Prepare request payload with streaming
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "stream": True
            }

            url = f"{self.base_url}/v1/chat/completions"

            response = self.session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )

            response.raise_for_status()

            # Stream response chunks
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str.strip() == '[DONE]':
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.RequestException as e:
            logger.error(f"AI Registry streaming error: {e}")
            raise AIRegistryError(f"Failed to stream answer: {e}")
        except Exception as e:
            logger.error(f"Unexpected error streaming answer: {e}")
            raise AIRegistryError(f"Answer streaming failed: {e}")


# Global service instance (singleton pattern)
_service_instance: Optional[AIRegistryService] = None


def get_ai_registry_service() -> AIRegistryService:
    """
    Get or create the global AIRegistryService instance.

    Returns:
        AIRegistryService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = AIRegistryService()

    return _service_instance
