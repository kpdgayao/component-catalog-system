"""Tests for Component Catalog."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import json

from apps.components.models import Component, ComponentMetadata, ComponentExample
from apps.components.validators import ComponentValidator
from apps.components.utils import ComponentUtils

class TestComponent:
    """Test component model functionality."""
    
    def test_component_creation(self, sample_component_data):
        """Test component creation."""
        component = Component(
            name=sample_component_data["name"],
            category=sample_component_data["category"],
            description=sample_component_data["description"],
            props=sample_component_data["props"],
            examples=sample_component_data["examples"],
            metadata=sample_component_data["metadata"]
        )
        
        assert component.name == "TestButton"
        assert component.category == "Buttons"
        assert len(component.examples) > 0
    
    def test_component_validation(self, sample_component_data):
        """Test component validation."""
        # Test valid component
        assert ComponentValidator.validate_component(sample_component_data)
        
        # Test invalid component
        invalid_data = sample_component_data.copy()
        invalid_data.pop("name")
        assert not ComponentValidator.validate_component(invalid_data)
    
    def test_component_serialization(self, sample_component_data):
        """Test component serialization."""
        component = Component(**sample_component_data)
        serialized = component.to_dict()
        
        assert isinstance(serialized, dict)
        assert serialized["name"] == component.name
        assert "metadata" in serialized
    
    def test_component_examples(self, sample_component_data):
        """Test component examples."""
        component = Component(**sample_component_data)
        example = component.examples[0]
        
        assert example.title == "Basic Usage"
        assert "<TestButton" in example.code

class TestComponentMetadata:
    """Test component metadata functionality."""
    
    def test_metadata_creation(self, sample_component_data):
        """Test metadata creation."""
        metadata = ComponentMetadata(**sample_component_data["metadata"])
        
        assert metadata.author == "Test Author"
        assert metadata.version == "1.0.0"
        assert isinstance(metadata.created_at, str)
    
    def test_metadata_validation(self):
        """Test metadata validation."""
        valid_metadata = {
            "author": "Test Author",
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        assert ComponentValidator.validate_metadata(valid_metadata)
        
        invalid_metadata = valid_metadata.copy()
        invalid_metadata.pop("author")
        assert not ComponentValidator.validate_metadata(invalid_metadata)

class TestComponentUtils:
    """Test component utility functions."""
    
    def test_generate_component_id(self):
        """Test component ID generation."""
        component_id = ComponentUtils.generate_component_id("TestButton")
        assert isinstance(component_id, str)
        assert len(component_id) > 0
    
    def test_parse_props(self):
        """Test props parsing."""
        props_str = '{"label": "string", "onClick": "function"}'
        parsed = ComponentUtils.parse_props(props_str)
        
        assert isinstance(parsed, dict)
        assert "label" in parsed
        assert parsed["label"] == "string"
    
    def test_validate_example_code(self):
        """Test example code validation."""
        valid_code = "<TestButton label='Click Me' />"
        assert ComponentUtils.validate_example_code(valid_code)
        
        invalid_code = "<TestButton label='Click Me'"
        assert not ComponentUtils.validate_example_code(invalid_code)

@pytest.mark.asyncio
class TestComponentDatabase:
    """Test component database operations."""
    
    async def test_component_creation(self, mock_supabase, sample_component_data):
        """Test creating a new component."""
        mock_supabase.table("components")._data = sample_component_data
        result = await mock_supabase.table("components").insert(sample_component_data).execute()
        assert result.data[0] == sample_component_data

    async def test_component_update(self, mock_supabase, sample_component_data):
        """Test updating a component."""
        updated_data = sample_component_data.copy()
        updated_data["description"] = "Updated description"
        
        mock_supabase.table("components")._data = updated_data
        result = await mock_supabase.table("components").update(updated_data).execute()
        assert result.data[0] == updated_data

    async def test_component_search(self, mock_supabase):
        """Test component search functionality."""
        search_results = [
            {"name": "TestButton", "category": "Buttons"},
            {"name": "TestInput", "category": "Inputs"}
        ]
        
        mock_supabase.table("components")._data = search_results[0]
        result = await mock_supabase.table("components").select("*").ilike("name", "%Test%").execute()
        assert result.data[0] == search_results[0]

class TestComponentValidation:
    """Test component validation functions."""
    
    def test_name_validation(self):
        """Test component name validation."""
        assert ComponentValidator.validate_name("TestButton")
        assert not ComponentValidator.validate_name("test-button")  # Invalid format
        assert not ComponentValidator.validate_name("")  # Empty name
    
    def test_category_validation(self):
        """Test category validation."""
        assert ComponentValidator.validate_category("Buttons")
        assert ComponentValidator.validate_category("Forms")
        assert not ComponentValidator.validate_category("")  # Empty category
    
    def test_props_validation(self):
        """Test props validation."""
        valid_props = {
            "label": "string",
            "onClick": "function",
            "disabled": "boolean"
        }
        assert ComponentValidator.validate_props(valid_props)
        
        invalid_props = {
            "label": "invalid_type",
            "onClick": "function"
        }
        assert not ComponentValidator.validate_props(invalid_props)
    
    def test_example_validation(self):
        """Test example validation."""
        valid_example = {
            "title": "Basic Usage",
            "code": "<TestButton label='Click Me' />"
        }
        assert ComponentValidator.validate_example(valid_example)
        
        invalid_example = {
            "title": "",  # Empty title
            "code": "<TestButton label='Click Me' />"
        }
        assert not ComponentValidator.validate_example(invalid_example)
