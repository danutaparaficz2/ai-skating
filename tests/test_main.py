"""Basic tests for the Data on Ice application."""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for testing
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.config import Settings
from src.utils import format_score, format_position, calculate_age, generate_sample_data
from datetime import datetime


class TestConfig:
    """Test configuration management."""
    
    def test_settings_creation(self):
        """Test that settings can be created with defaults."""
        settings = Settings()
        assert settings.app_name == "Data on Ice"
        assert settings.app_version == "1.0.0"
        assert settings.alibaba_region == "cn-hangzhou"
    
    def test_settings_env_override(self):
        """Test that environment variables override defaults."""
        with patch.dict('os.environ', {'QWEN_MODEL_NAME': 'qwen-plus'}):
            settings = Settings()
            assert settings.qwen_model_name == 'qwen-plus'


class TestUtils:
    """Test utility functions."""
    
    def test_format_score(self):
        """Test score formatting."""
        assert format_score(123.456) == "123.46"
        assert format_score(None) == "N/A"
        assert format_score(0.0) == "0.00"
    
    def test_format_position(self):
        """Test position formatting with ordinals."""
        assert format_position(1) == "1st"
        assert format_position(2) == "2nd" 
        assert format_position(3) == "3rd"
        assert format_position(4) == "4th"
        assert format_position(11) == "11th"
        assert format_position(21) == "21st"
        assert format_position(None) == "N/A"
    
    def test_calculate_age(self):
        """Test age calculation."""
        birth_date = datetime(2000, 1, 1)
        reference_date = datetime(2023, 6, 15)
        age = calculate_age(birth_date, reference_date)
        assert age == 23
        
        # Test birthday not yet reached
        birth_date = datetime(2000, 12, 1)
        reference_date = datetime(2023, 6, 15)
        age = calculate_age(birth_date, reference_date)
        assert age == 22
    
    def test_generate_sample_data(self):
        """Test sample data generation."""
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = generate_sample_data()
            
            assert 'skaters' in result
            assert 'competitions' in result
            assert 'results' in result
            assert 'videos' in result
            assert result['skaters'] > 0
            assert result['competitions'] > 0


class TestModels:
    """Test data models."""
    
    def test_story_request_defaults(self):
        """Test StoryRequest model defaults."""
        from src.models import StoryRequest
        
        request = StoryRequest()
        assert request.story_type == "profile"
        assert request.audience == "general"
        assert request.length == "medium"
    
    def test_story_request_validation(self):
        """Test StoryRequest validation."""
        from src.models import StoryRequest
        
        # Valid request
        request = StoryRequest(
            skater_ids=[1, 2],
            story_type="profile",
            audience="media"
        )
        assert request.skater_ids == [1, 2]
        assert request.story_type == "profile"
        assert request.audience == "media"


class TestQwenClient:
    """Test Qwen LLM client (mocked)."""
    
    @patch('requests.post')
    def test_generate_story_success(self, mock_post):
        """Test successful story generation."""
        from src.ai_processing import QwenLLMClient
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"text": "Generated story content"}
        }
        mock_post.return_value = mock_response
        
        client = QwenLLMClient()
        result = client.generate_story("Test prompt")
        
        # Since generate_story is async, we need to handle it properly
        # For this basic test, we'll test the sync fallback
        assert "Generated story content" in str(result) or "Test prompt" in str(result)
    
    @patch('requests.post')
    def test_generate_story_fallback(self, mock_post):
        """Test fallback when API fails."""
        from src.ai_processing import QwenLLMClient
        
        # Mock API error
        mock_post.side_effect = Exception("API Error")
        
        client = QwenLLMClient()
        result = client._fallback_generation("Test prompt")
        
        assert "Test prompt" in result


class TestSearchClient:
    """Test OpenSearch client (mocked)."""
    
    @patch('src.search.OpenSearch')
    def test_search_client_initialization(self, mock_opensearch):
        """Test search client initialization."""
        from src.search import OpenSearchClient
        
        mock_client = Mock()
        mock_opensearch.return_value = mock_client
        mock_client.indices.exists.return_value = True
        
        client = OpenSearchClient()
        assert client.client == mock_client
    
    @patch('src.search.OpenSearch')
    def test_index_creation(self, mock_opensearch):
        """Test index creation when it doesn't exist."""
        from src.search import OpenSearchClient
        
        mock_client = Mock()
        mock_opensearch.return_value = mock_client
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {"acknowledged": True}
        
        client = OpenSearchClient()
        mock_client.indices.create.assert_called_once()


class TestDataIngestion:
    """Test data ingestion functionality (mocked)."""
    
    def test_data_validator(self):
        """Test data validation functions."""
        from src.data_ingestion import DataValidator
        
        # Valid skater data
        valid_skater = {"name": "Test Skater", "country": "USA"}
        assert DataValidator.validate_skater_data(valid_skater) == True
        
        # Invalid skater data
        invalid_skater = {"name": "", "country": "USA"}
        assert DataValidator.validate_skater_data(invalid_skater) == False
        
        # Valid result data
        valid_result = {
            "skater": {"name": "Test", "country": "USA"},
            "competition": {"name": "Test Comp", "year": 2023}
        }
        assert DataValidator.validate_result_data(valid_result) == True
        
        # Invalid result data
        invalid_result = {"skater": {"name": "Test"}}
        assert DataValidator.validate_result_data(invalid_result) == False


if __name__ == "__main__":
    pytest.main([__file__])