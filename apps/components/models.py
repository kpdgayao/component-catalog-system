"""Component models for the Component Catalog."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

@dataclass
class ComponentExample:
    """Example usage of a component."""
    title: str
    code: str
    description: Optional[str] = None

@dataclass
class ComponentMetadata:
    """Metadata for a component."""
    author: str
    created_at: str
    version: str
    last_updated: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

@dataclass
class Component:
    """Component model for the Component Catalog."""
    name: str
    category: str
    description: str
    props: Dict[str, str]
    examples: List[Union[Dict[str, Any], 'ComponentExample']]
    metadata: Union[Dict[str, Any], 'ComponentMetadata']
    id: Optional[str] = None
    
    def __init__(self, name: str, category: str, description: str, props: Dict[str, str],
                 examples: List[Union[Dict[str, Any], 'ComponentExample']],
                 metadata: Union[Dict[str, Any], 'ComponentMetadata'],
                 id: Optional[str] = None):
        """Initialize a component."""
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.props = props
        self.examples = [
            ex if isinstance(ex, ComponentExample)
            else ComponentExample(**ex)
            for ex in examples
        ]
        self.metadata = (
            metadata if isinstance(metadata, ComponentMetadata)
            else ComponentMetadata(**metadata)
        )

    def to_dict(self) -> Dict:
        """Convert component to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "props": self.props,
            "examples": [
                {
                    "title": ex.title,
                    "code": ex.code,
                    "description": ex.description
                }
                for ex in self.examples
            ],
            "metadata": {
                "author": self.metadata.author,
                "created_at": self.metadata.created_at,
                "version": self.metadata.version,
                "last_updated": self.metadata.last_updated,
                "tags": self.metadata.tags,
                "dependencies": self.metadata.dependencies
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Component":
        """Create component from dictionary."""
        examples = [
            ComponentExample(
                title=ex["title"],
                code=ex["code"],
                description=ex.get("description")
            )
            for ex in data["examples"]
        ]
        
        metadata = ComponentMetadata(
            author=data["metadata"]["author"],
            created_at=data["metadata"]["created_at"],
            version=data["metadata"]["version"],
            last_updated=data["metadata"].get("last_updated"),
            tags=data["metadata"].get("tags", []),
            dependencies=data["metadata"].get("dependencies", [])
        )
        
        return cls(
            id=data.get("id"),
            name=data["name"],
            category=data["category"],
            description=data["description"],
            props=data["props"],
            examples=examples,
            metadata=metadata
        )
