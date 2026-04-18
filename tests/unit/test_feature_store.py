# tests/unit/test_feature_store.py
import torch
import pytest


def test_feature_version_registry():
    from ml.feature_store.schema import FEATURE_VERSIONS, FeatureSchema
    assert "v1" in FEATURE_VERSIONS
    schema = FEATURE_VERSIONS["v1"]
    assert isinstance(schema, FeatureSchema)


def test_feature_schema_validate_ok():
    from ml.feature_store.schema import FEATURE_VERSIONS
    schema = FEATURE_VERSIONS["v1"]
    tensor = torch.zeros(30, 3, 224, 224)
    errors = schema.validate(tensor)
    assert errors == []


def test_feature_schema_validate_fail():
    from ml.feature_store.schema import FEATURE_VERSIONS
    schema = FEATURE_VERSIONS["v1"]
    tensor = torch.zeros(30, 1, 224, 224)  # wrong channels
    errors = schema.validate(tensor)
    assert len(errors) > 0
