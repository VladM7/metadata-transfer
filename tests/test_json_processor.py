import sys
import os
import pytest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from json_processor import extract_photo_metadata


def test_extract_photo_metadata_basic():
    # Minimal config and data
    config_fields = {
        "iso": {"path": "iso"},
        "shutter": {"path": "shutter"},
        "aperture": {"path": "aperture"},
        "focal_length": {"path": "focalLength"},
        "date": {"path": "date"},
        "lens": {
            "fields": {"make": {"path": "lens.make"}, "model": {"path": "lens.model"}}
        },
        "location": {
            "fields": {
                "latitude": {"path": "location.latitude"},
                "longitude": {"path": "location.longitude"},
            }
        },
        "camera": {
            "fields": {
                "make": {"path": "camera.make"},
                "model": {"path": "camera.model"},
            }
        },
    }
    json_data = {
        "iso": 400,
        "frames": [
            {
                "shutter": "1/125",
                "aperture": "8",
                "focalLength": 50,
                "date": "2025-01-01T12:00",
                "lens": {"make": "Canon", "model": "FD 50mm"},
                "location": {"latitude": 52.1, "longitude": 5.1},
                "camera": {"make": "Canon", "model": "AE-1"},
            },
            {
                "shutter": "1/60",
                "aperture": "4",
                "focalLength": 28,
                "date": "2025-01-02T13:00",
                "lens": {"make": "Nikon", "model": "28mm"},
                "location": {"latitude": 53.2, "longitude": 6.2},
                "camera": {"make": "Nikon", "model": "FM2"},
            },
        ],
    }
    result = extract_photo_metadata(json_data, config_fields)
    assert len(result) == 2
    assert result[0]["iso"] == 400
    assert result[0]["shutter"] == "1/125"
    assert result[0]["aperture"] == "8"
    assert result[0]["focal_length"] == 50
    assert result[0]["date"] == "2025-01-01T12:00"
    assert result[0]["lens"]["make"] == "Canon"
    assert result[0]["lens"]["model"] == "FD 50mm"
    assert result[0]["location"]["latitude"] == 52.1
    assert result[0]["location"]["longitude"] == 5.1
    assert result[0]["camera"]["make"] == "Canon"
    assert result[0]["camera"]["model"] == "AE-1"
    assert result[1]["iso"] == 400
    assert result[1]["shutter"] == "1/60"
    assert result[1]["aperture"] == "4"
    assert result[1]["focal_length"] == 28
    assert result[1]["date"] == "2025-01-02T13:00"
    assert result[1]["lens"]["make"] == "Nikon"
    assert result[1]["lens"]["model"] == "28mm"
    assert result[1]["location"]["latitude"] == 53.2
    assert result[1]["location"]["longitude"] == 6.2
    assert result[1]["camera"]["make"] == "Nikon"
    assert result[1]["camera"]["model"] == "FM2"


def test_extract_photo_metadata_missing_fields():
    config_fields = {
        "iso": {"path": "iso"},
        "shutter": {"path": "shutter"},
        "location": {
            "fields": {
                "latitude": {"path": "location.latitude"},
                "longitude": {"path": "location.longitude"},
            }
        },
    }
    json_data = {
        "frames": [
            {"shutter": "1/250"},
            {"aperture": "5.6", "location": {"longitude": 4.1}},
            {
                "shutter": "1/30",
                "aperture": "2.8",
                "location": {"latitude": 52.2, "longitude": 5.2},
            },
        ]
    }
    result = extract_photo_metadata(json_data, config_fields)
    assert len(result) == 3
    assert result[0]["shutter"] == "1/250"
    assert "aperture" not in result[0]
    assert "location" not in result[0] or "latitude" not in result[0].get(
        "location", {}
    )
    assert "aperture" not in result[1]
    assert result[1]["location"]["longitude"] == 4.1
    assert "latitude" not in result[1]["location"]
    assert result[2]["location"]["latitude"] == 52.2
    assert result[2]["location"]["longitude"] == 5.2
