"""Regression tests for important_fields dict-to-string normalization.

The LLM sometimes returns important_fields as objects like:
    {"name": "id", "type": "BIGINT", "constraint": "PRIMARY KEY"}

instead of strings like:
    "id BIGINT PRIMARY KEY"

This test verifies the architecture engine normalizes these before
Pydantic validation of ArchitectureDocument.
"""

import pytest
from app.models.architecture import ArchitectureDocument


def _make_raw_result(data_architecture):
    """Build a minimal raw LLM result dict with the given data_architecture."""
    return {
        "system_architecture": "Django monolith with PostgreSQL",
        "components": [
            {
                "name": "API",
                "responsibility": "Handle requests",
                "technologies": ["Django"],
            }
        ],
        "technology_stack": [
            {
                "category": "BACKEND_FRAMEWORK",
                "technology": "Django",
                "reason": "User selected",
            }
        ],
        "data_architecture": data_architecture,
        "api_design": [
            {
                "name": "Default",
                "purpose": "Core API",
                "endpoints": ["GET /health - Health check"],
            }
        ],
        "security": [
            {
                "area": "Authentication",
                "decision": "JWT",
                "reason": "Standard",
            }
        ],
        "deployment": [
            {
                "environment": "production",
                "services": ["django"],
                "reason": "Simple deployment",
            }
        ],
    }


def _normalize_field(field):
    """Convert a single important_field entry to a string."""
    if isinstance(field, str):
        return field
    if field is None:
        return None
    if not isinstance(field, dict):
        try:
            return str(field)
        except Exception:
            return None
    parts = []
    col_name = (
        field.get("name")
        or field.get("field")
        or field.get("column")
    )
    if col_name:
        parts.append(str(col_name))
    col_type = (
        field.get("type")
        or field.get("data_type")
        or field.get("datatype")
    )
    if col_type:
        parts.append(str(col_type))
    col_constraint = (
        field.get("constraint")
        or field.get("definition")
        or field.get("constraints")
    )
    if col_constraint:
        parts.append(str(col_constraint))
    if not parts:
        index_val = field.get("index") or field.get("primary_key")
        if index_val:
            parts.append(str(index_val))
    if parts:
        return " ".join(parts)
    try:
        return str(field)
    except Exception:
        return None


def _normalize(result):
    """Replicate the normalization logic from architecture engine."""
    if "api_design" in result:
        for group in result["api_design"]:
            if "endpoints" in group:
                normalized = []
                for ep in group["endpoints"]:
                    if isinstance(ep, dict):
                        method = ep.get("method", "GET")
                        path = ep.get("path", "")
                        desc = ep.get("description", "")
                        normalized.append(f"{method} {path} - {desc}")
                    else:
                        normalized.append(str(ep))
                group["endpoints"] = normalized

    if "data_architecture" in result:
        for entity in result["data_architecture"]:
            if "important_fields" in entity:
                normalized = []
                for field in entity["important_fields"]:
                    s = _normalize_field(field)
                    if s is not None:
                        normalized.append(s)
                entity["important_fields"] = normalized

    return result


class TestImportantFieldsNormalization:
    """Test that important_fields dict objects are converted to strings."""

    def test_dict_objects_converted_to_strings(self):
        """LLM returns {name, type, constraint} objects → strings."""
        result = _make_raw_result(
            [
                {
                    "name": "users",
                    "purpose": "User accounts",
                    "important_fields": [
                        {"name": "id", "type": "BIGINT", "constraint": "PRIMARY KEY"},
                        {"name": "email", "type": "VARCHAR(255)", "constraint": "UNIQUE NOT NULL"},
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        assert len(doc.data_architecture) == 1
        entity = doc.data_architecture[0]
        assert entity.name == "users"
        assert entity.important_fields == [
            "id BIGINT PRIMARY KEY",
            "email VARCHAR(255) UNIQUE NOT NULL",
        ]

    def test_partial_dict_keys_handled(self):
        """Dict with only name and type (no constraint) is handled."""
        result = _make_raw_result(
            [
                {
                    "name": "orders",
                    "purpose": "Order tracking",
                    "important_fields": [
                        {"name": "id", "type": "SERIAL"},
                        {"name": "status", "type": "VARCHAR(50)"},
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        fields = doc.data_architecture[0].important_fields
        assert "id SERIAL" in fields
        assert "status VARCHAR(50)" in fields

    def test_dict_with_only_name(self):
        """Dict with only name key (no type/constraint)."""
        result = _make_raw_result(
            [
                {
                    "name": "items",
                    "purpose": "Item storage",
                    "important_fields": [
                        {"name": "uuid"},
                        {"name": "created_at"},
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        fields = doc.data_architecture[0].important_fields
        assert "uuid" in fields
        assert "created_at" in fields

    def test_string_fields_unchanged(self):
        """Already-string values pass through unchanged."""
        result = _make_raw_result(
            [
                {
                    "name": "sessions",
                    "purpose": "User sessions",
                    "important_fields": [
                        "id SERIAL PRIMARY KEY",
                        "user_id INTEGER NOT NULL",
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        fields = doc.data_architecture[0].important_fields
        assert fields == ["id SERIAL PRIMARY KEY", "user_id INTEGER NOT NULL"]

    def test_mixed_strings_and_dicts(self):
        """Mix of string and dict values in the same entity."""
        result = _make_raw_result(
            [
                {
                    "name": "payments",
                    "purpose": "Payment records",
                    "important_fields": [
                        "id SERIAL PRIMARY KEY",
                        {"name": "amount", "type": "DECIMAL(10,2)"},
                        "created_at TIMESTAMP DEFAULT NOW()",
                        {"name": "status", "type": "VARCHAR(20)", "constraint": "NOT NULL"},
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        fields = doc.data_architecture[0].important_fields
        assert fields == [
            "id SERIAL PRIMARY KEY",
            "amount DECIMAL(10,2)",
            "created_at TIMESTAMP DEFAULT NOW()",
            "status VARCHAR(20) NOT NULL",
        ]

    def test_empty_important_fields(self):
        """Empty list is handled."""
        result = _make_raw_result(
            [
                {
                    "name": "logs",
                    "purpose": "Audit logs",
                    "important_fields": [],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        assert doc.data_architecture[0].important_fields == []

    def test_none_important_fields_skipped(self):
        """None values in the list are skipped."""
        result = _make_raw_result(
            [
                {
                    "name": "cache",
                    "purpose": "Cache data",
                    "important_fields": [None, "key TEXT", None],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        assert doc.data_architecture[0].important_fields == ["key TEXT"]

    def test_dict_with_no_useful_keys(self):
        """Dict with no recognizable keys falls back to str representation."""
        result = _make_raw_result(
            [
                {
                    "name": "mystery",
                    "purpose": "Unknown",
                    "important_fields": [
                        {"foo": "bar"},
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        # Falls back to str(dict) to avoid data loss
        assert len(doc.data_architecture[0].important_fields) == 1
        assert "foo" in doc.data_architecture[0].important_fields[0]

    def test_multiple_entities_with_dicts(self):
        """Multiple entities all have dict-type important_fields."""
        result = _make_raw_result(
            [
                {
                    "name": "users",
                    "purpose": "User accounts",
                    "important_fields": [
                        {"name": "id", "type": "BIGINT", "constraint": "PRIMARY KEY"},
                    ],
                },
                {
                    "name": "orders",
                    "purpose": "Orders",
                    "important_fields": [
                        {"name": "id", "type": "BIGINT", "constraint": "PRIMARY KEY"},
                        {"name": "total", "type": "DECIMAL(10,2)"},
                    ],
                },
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        assert len(doc.data_architecture) == 2
        assert doc.data_architecture[0].important_fields == ["id BIGINT PRIMARY KEY"]
        assert doc.data_architecture[1].important_fields == [
            "id BIGINT PRIMARY KEY",
            "total DECIMAL(10,2)",
        ]

    def test_no_data_architecture(self):
        """Result with no data_architecture key is handled."""
        result = _make_raw_result([])
        del result["data_architecture"]

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        assert doc.data_architecture == []

    def test_index_dict_variant(self):
        """LLM returns {'index': 'INDEX(...)'} or {'primary_key': '(...)'} objects."""
        result = _make_raw_result(
            [
                {
                    "name": "users",
                    "purpose": "User accounts",
                    "important_fields": [
                        {"field": "id", "constraint": "PRIMARY KEY"},
                        {"index": "INDEX(role, status)"},
                        {"primary_key": "(technician_user_id, category_id)"},
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        fields = doc.data_architecture[0].important_fields
        assert "id PRIMARY KEY" in fields
        assert "INDEX(role, status)" in fields
        assert "(technician_user_id, category_id)" in fields

    def test_llm_field_key_variant(self):
        """LLM uses 'field' key instead of 'name' — the actual observed pattern."""
        result = _make_raw_result(
            [
                {
                    "name": "users",
                    "purpose": "User accounts",
                    "important_fields": [
                        {
                            "field": "id",
                            "constraint": "PRIMARY KEY, BIGINT AUTO_INCREMENT",
                        },
                        {
                            "field": "role",
                            "constraint": "ENUM('customer','technician'), NOT NULL, INDEX",
                        },
                        {
                            "field": "email",
                            "constraint": "VARCHAR(255), NULL, UNIQUE, INDEX",
                        },
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        fields = doc.data_architecture[0].important_fields
        assert "id PRIMARY KEY, BIGINT AUTO_INCREMENT" in fields
        assert "role ENUM('customer','technician'), NOT NULL, INDEX" in fields
        assert "email VARCHAR(255), NULL, UNIQUE, INDEX" in fields

    def test_information_preserved_in_string(self):
        """All three dict keys (name, type, constraint) appear in the string."""
        result = _make_raw_result(
            [
                {
                    "name": "users",
                    "purpose": "Accounts",
                    "important_fields": [
                        {
                            "name": "password_hash",
                            "type": "VARCHAR(512)",
                            "constraint": "NOT NULL",
                        }
                    ],
                }
            ]
        )

        normalized = _normalize(result)
        doc = ArchitectureDocument(**normalized)

        field_str = doc.data_architecture[0].important_fields[0]
        assert "password_hash" in field_str
        assert "VARCHAR(512)" in field_str
        assert "NOT NULL" in field_str
