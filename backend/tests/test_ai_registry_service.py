"""
Tests for AI Registry Service (US-037)

Tests all features of the AI Registry integration including:
- Prompt template loading and formatting
- LLM request/response handling
- Token counting and context management
- Cost tracking
- Streaming responses
- Fallback logic
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import json

from backend.services.ai_registry_service import (
    AIRegistryService,
    AIRegistryError,
    AIRegistryRateLimitError,
    TokenLimitExceededError,
    MODEL_PRICING,
    MODEL_TOKEN_LIMITS,
    PROMPT_TEMPLATES,
    get_ai_registry_service
)


class TestAIRegistryServiceInit:
    """Test AI Registry service initialization."""

    def test_init_with_default_settings(self):
        """Test initialization with default settings."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            service = AIRegistryService()

            assert service.api_key is not None
            assert service.base_url == "https://api.ainative.studio"
            assert service.timeout == 30
            assert service.primary_model is not None
            assert service.fallback_model is not None

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            service = AIRegistryService(
                api_key="test-key",
                base_url="https://custom.api.com",
                timeout=60
            )

            assert service.api_key == "test-key"
            assert service.base_url == "https://custom.api.com"
            assert service.timeout == 60

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises error."""
        with patch('backend.services.ai_registry_service.settings') as mock_settings:
            mock_settings.AI_REGISTRY_API_KEY = None
            mock_settings.AINATIVE_API_KEY = None

            with pytest.raises(AIRegistryError, match="API_KEY is required"):
                AIRegistryService()

    def test_init_creates_prompt_cache(self):
        """Test that initialization creates empty prompt cache."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            service = AIRegistryService()

            assert isinstance(service._prompt_cache, dict)
            assert len(service._prompt_cache) == 0


class TestPromptTemplateLoading:
    """Test prompt template loading functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            return AIRegistryService()

    def test_load_prompt_template_general(self, service):
        """Test loading general martial arts template."""
        template = service._load_prompt_template("general")

        assert template is not None
        assert "{query}" in template
        assert "{context}" in template
        assert "martial arts" in template.lower()

    def test_load_prompt_template_technique(self, service):
        """Test loading technique explanation template."""
        template = service._load_prompt_template("technique")

        assert template is not None
        assert "{query}" in template
        assert "technique" in template.lower()

    def test_load_prompt_template_history(self, service):
        """Test loading history and philosophy template."""
        template = service._load_prompt_template("history")

        assert template is not None
        assert "{query}" in template
        assert "history" in template.lower() or "philosophy" in template.lower()

    def test_load_prompt_template_training(self, service):
        """Test loading training recommendations template."""
        template = service._load_prompt_template("training")

        assert template is not None
        assert "{query}" in template
        assert "training" in template.lower()

    def test_load_prompt_template_caching(self, service):
        """Test that templates are cached after first load."""
        # Load template twice
        template1 = service._load_prompt_template("general")
        template2 = service._load_prompt_template("general")

        # Should be the same instance (cached)
        assert template1 == template2
        assert "general" in service._prompt_cache

    def test_load_invalid_template_raises_error(self, service):
        """Test that loading invalid template raises error."""
        with pytest.raises(AIRegistryError, match="Unknown template"):
            service._load_prompt_template("invalid_template")

    def test_load_template_file_not_found(self, service):
        """Test error when template file doesn't exist."""
        service.prompts_dir = Path("/nonexistent/path")

        with pytest.raises(AIRegistryError, match="Template file not found"):
            service._load_prompt_template("general")

    def test_format_prompt_template(self, service):
        """Test formatting prompt template with query and context."""
        formatted = service.format_prompt_template(
            template_name="general",
            query="What is karate?",
            context="Karate is a martial art from Japan."
        )

        assert "What is karate?" in formatted
        assert "Karate is a martial art from Japan." in formatted
        assert "{query}" not in formatted
        assert "{context}" not in formatted


class TestTokenCounting:
    """Test token counting functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            return AIRegistryService()

    def test_count_tokens_simple_text(self, service):
        """Test counting tokens in simple text."""
        text = "Hello, world!"
        tokens = service.count_tokens(text)

        assert tokens > 0
        assert tokens < 100

    def test_count_tokens_long_text(self, service):
        """Test counting tokens in longer text."""
        text = "This is a longer piece of text. " * 100
        tokens = service.count_tokens(text)

        assert tokens > 100

    def test_count_tokens_with_different_models(self, service):
        """Test token counting with different model encodings."""
        text = "Test text for token counting"

        tokens_gpt4 = service.count_tokens(text, model="gpt-4")
        tokens_gpt35 = service.count_tokens(text, model="gpt-3.5-turbo")

        # Should be similar but might differ slightly
        assert abs(tokens_gpt4 - tokens_gpt35) < 5

    @patch('backend.services.ai_registry_service.tiktoken', None)
    def test_count_tokens_fallback_without_tiktoken(self, service):
        """Test that token counting falls back to estimation without tiktoken."""
        text = "Hello, world!"
        tokens = service.count_tokens(text)

        # Fallback estimate: 1 token ≈ 4 characters
        expected = len(text) // 4
        assert tokens == expected


class TestContextTrimming:
    """Test context trimming to fit token limits."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            return AIRegistryService()

    def test_trim_context_within_limit(self, service):
        """Test that short prompts are not trimmed."""
        short_prompt = "Short prompt that fits"
        trimmed = service.trim_context_to_limit(short_prompt, max_prompt_tokens=1000)

        assert trimmed == short_prompt

    def test_trim_context_exceeds_limit(self, service):
        """Test that long prompts are trimmed."""
        long_prompt = "Line\n" * 1000
        trimmed = service.trim_context_to_limit(long_prompt, max_prompt_tokens=100)

        assert len(trimmed) < len(long_prompt)
        assert "context trimmed" in trimmed.lower()

    def test_trim_context_preserves_start_and_end(self, service):
        """Test that trimming preserves start and end of prompt."""
        lines = [f"Line {i}" for i in range(100)]
        prompt = "\n".join(lines)

        trimmed = service.trim_context_to_limit(prompt, max_prompt_tokens=50)

        # Should preserve first and last lines
        assert "Line 0" in trimmed
        assert "Line 99" in trimmed


class TestCostCalculation:
    """Test cost calculation functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            return AIRegistryService()

    def test_calculate_cost_gpt4(self, service):
        """Test cost calculation for GPT-4."""
        cost = service.calculate_cost(1000, 500, model="gpt-4")

        # 1000 input tokens * $0.03/1K + 500 output tokens * $0.06/1K
        expected = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06
        assert abs(cost - expected) < 0.001

    def test_calculate_cost_gpt35(self, service):
        """Test cost calculation for GPT-3.5."""
        cost = service.calculate_cost(1000, 500, model="gpt-3.5-turbo")

        # Lower cost than GPT-4
        assert cost < 0.01

    def test_calculate_cost_zero_tokens(self, service):
        """Test cost calculation with zero tokens."""
        cost = service.calculate_cost(0, 0)

        assert cost == 0.0

    def test_calculate_cost_uses_default_model(self, service):
        """Test that cost calculation uses default model when not specified."""
        cost = service.calculate_cost(1000, 500)

        assert cost > 0


class TestCostTracking:
    """Test cost tracking in ZeroDB."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        mock_zerodb = Mock()
        with patch('backend.services.ai_registry_service.ZeroDBClient', return_value=mock_zerodb):
            service = AIRegistryService()
            service.zerodb = mock_zerodb
            service.cost_tracking_enabled = True
            return service

    def test_track_request_success(self, service):
        """Test tracking successful request."""
        service._track_request(
            prompt="Test prompt",
            response="Test response",
            model="gpt-4",
            template_name="general",
            success=True
        )

        # Should call zerodb.create
        service.zerodb.create.assert_called_once()
        call_args = service.zerodb.create.call_args

        assert call_args[1]["collection"] == "ai_requests"
        data = call_args[1]["data"]
        assert data["model"] == "gpt-4"
        assert data["template"] == "general"
        assert data["success"] is True
        assert data["cost_usd"] > 0

    def test_track_request_failure(self, service):
        """Test tracking failed request."""
        service._track_request(
            prompt="Test prompt",
            response="",
            model="gpt-4",
            success=False,
            error="API timeout"
        )

        service.zerodb.create.assert_called_once()
        call_args = service.zerodb.create.call_args

        data = call_args[1]["data"]
        assert data["success"] is False
        assert data["error"] == "API timeout"

    def test_track_request_disabled(self):
        """Test that tracking is skipped when disabled."""
        mock_zerodb = Mock()
        with patch('backend.services.ai_registry_service.ZeroDBClient', return_value=mock_zerodb):
            service = AIRegistryService()
            service.cost_tracking_enabled = False

            service._track_request(
                prompt="Test",
                response="Test",
                model="gpt-4",
                success=True
            )

            # Should not call zerodb
            mock_zerodb.create.assert_not_called()


class TestGenerateAnswer:
    """Test generate_answer functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            service = AIRegistryService()
            service.cost_tracking_enabled = False  # Disable for simpler testing
            return service

    @patch('backend.services.ai_registry_service.requests.Session')
    def test_generate_answer_success(self, mock_session_class, service):
        """Test successful answer generation."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Test answer"}
            }],
            "usage": {"total_tokens": 150}
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        service.session = mock_session

        result = service.generate_answer(
            query="What is karate?",
            context=[{"data": {"title": "Karate", "description": "A martial art"}}]
        )

        assert result["answer"] == "Test answer"
        assert result["tokens_used"] == 150
        assert result["model"] == "gpt-4o-mini"
        assert "latency_ms" in result

    @patch('backend.services.ai_registry_service.requests.Session')
    def test_generate_answer_api_error(self, mock_session_class, service):
        """Test error handling when API fails."""
        mock_session = Mock()
        mock_session.post.side_effect = Exception("API Error")
        mock_session_class.return_value = mock_session
        service.session = mock_session

        with pytest.raises(AIRegistryError, match="Answer generation failed"):
            service.generate_answer(
                query="Test query",
                context=[]
            )

    @patch('backend.services.ai_registry_service.requests.Session')
    def test_generate_answer_with_custom_model(self, mock_session_class, service):
        """Test answer generation with custom model."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Answer"}}],
            "usage": {"total_tokens": 100}
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        service.session = mock_session

        result = service.generate_answer(
            query="Test",
            context=[],
            model="gpt-4"
        )

        assert result["model"] == "gpt-4"


class TestStreamAnswer:
    """Test stream_answer functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            return AIRegistryService()

    @patch('backend.services.ai_registry_service.requests.Session')
    def test_stream_answer_success(self, mock_session_class, service):
        """Test successful streaming response."""
        # Mock streaming response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        # Simulate SSE stream
        stream_data = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            b'data: {"choices":[{"delta":{"content":" world"}}]}\n',
            b'data: [DONE]\n'
        ]
        mock_response.iter_lines.return_value = stream_data

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        service.session = mock_session

        # Collect streamed chunks
        chunks = list(service.stream_answer(
            query="Test query",
            context=[]
        ))

        assert len(chunks) == 2
        assert chunks[0] == "Hello"
        assert chunks[1] == " world"

    @patch('backend.services.ai_registry_service.requests.Session')
    def test_stream_answer_error(self, mock_session_class, service):
        """Test error handling in streaming."""
        mock_session = Mock()
        mock_session.post.side_effect = Exception("Streaming error")
        mock_session_class.return_value = mock_session
        service.session = mock_session

        with pytest.raises(AIRegistryError, match="Answer streaming failed"):
            list(service.stream_answer(query="Test", context=[]))


class TestGenerateRelatedQueries:
    """Test generate_related_queries functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            return AIRegistryService()

    @patch('backend.services.ai_registry_service.requests.Session')
    def test_generate_related_queries_success(self, mock_session_class, service):
        """Test successful related query generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Query 1\nQuery 2\nQuery 3"}
            }]
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        service.session = mock_session

        queries = service.generate_related_queries(
            query="What is karate?",
            count=3
        )

        assert len(queries) == 3
        assert queries[0] == "Query 1"
        assert queries[1] == "Query 2"
        assert queries[2] == "Query 3"

    @patch('backend.services.ai_registry_service.requests.Session')
    def test_generate_related_queries_error_returns_empty(self, mock_session_class, service):
        """Test that errors return empty list instead of raising."""
        mock_session = Mock()
        mock_session.post.side_effect = Exception("API Error")
        mock_session_class.return_value = mock_session
        service.session = mock_session

        queries = service.generate_related_queries(query="Test")

        assert queries == []


class TestSingletonPattern:
    """Test singleton pattern for service instance."""

    def test_get_ai_registry_service_returns_singleton(self):
        """Test that get_ai_registry_service returns same instance."""
        with patch('backend.services.ai_registry_service.ZeroDBClient'):
            service1 = get_ai_registry_service()
            service2 = get_ai_registry_service()

            assert service1 is service2


class TestModelPricingAndLimits:
    """Test model pricing and token limits constants."""

    def test_model_pricing_structure(self):
        """Test that model pricing has correct structure."""
        for model, pricing in MODEL_PRICING.items():
            assert "input" in pricing
            assert "output" in pricing
            assert pricing["input"] > 0
            assert pricing["output"] > 0

    def test_model_token_limits_structure(self):
        """Test that token limits are defined."""
        for model, limit in MODEL_TOKEN_LIMITS.items():
            assert limit > 0
            assert isinstance(limit, int)

    def test_prompt_templates_defined(self):
        """Test that all required templates are defined."""
        required_templates = ["general", "technique", "history", "training"]

        for template in required_templates:
            assert template in PROMPT_TEMPLATES
            assert PROMPT_TEMPLATES[template].endswith(".txt")
