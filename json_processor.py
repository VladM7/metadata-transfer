import json

# --- Utility to walk the JSON recursively ---


def get_by_path(data, path):
    """Get a value from nested dict/list using dot-separated path."""
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
        if current is None:
            return None
    return current


def find_frames(data):
    """Recursively find a list of frames (dicts with relevant fields)."""
    if isinstance(data, list):
        if all(isinstance(f, dict) for f in data):
            has_metadata = any(
                any(k in frame for k in ["shutter", "aperture", "lens"])
                for frame in data
            )
            if has_metadata:
                return data
        for item in data:
            result = find_frames(item)
            if result:
                return result
    elif isinstance(data, dict):
        for value in data.values():
            result = find_frames(value)
            if result:
                return result
    return None


# --- Main processing ---


def extract_photo_metadata(json_data, config_fields):
    # iso is global, but fallback to per-frame if not found
    iso_cfg = config_fields.get("iso", {})
    iso_path = iso_cfg.get("path") if isinstance(iso_cfg, dict) else iso_cfg
    frames = find_frames(json_data)

    if not frames:
        raise ValueError("No valid frames with required fields found.")

    output = []
    for idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue
        # Try global iso first, then per-frame
        iso = get_by_path(json_data, iso_path) if iso_path else None
        if iso is None:
            iso = get_by_path(frame, iso_path) if iso_path else None
        frame_data = {"iso": iso}
        has_any = False
        for field, mapping in config_fields.items():
            if field == "iso":
                continue  # already handled
            # For camera, try global first, then per-frame
            if field == "camera" and isinstance(mapping, dict) and "fields" in mapping:
                obj = {}
                for prop_key, prop_cfg in mapping["fields"].items():
                    prop_path = (
                        prop_cfg.get("path") if isinstance(prop_cfg, dict) else prop_cfg
                    )
                    # Try global first
                    val = get_by_path(json_data, prop_path)
                    # If not found, try per-frame
                    if val is None:
                        val = get_by_path(frame, prop_path)
                    if val is not None:
                        obj[prop_key] = val
                if obj:
                    frame_data[field] = obj
                    has_any = True
            elif isinstance(mapping, dict) and "fields" in mapping:
                # Nested object (e.g., lens, location)
                obj = {}
                for prop_key, prop_cfg in mapping["fields"].items():
                    prop_path = (
                        prop_cfg.get("path") if isinstance(prop_cfg, dict) else prop_cfg
                    )
                    val = get_by_path(frame, prop_path)
                    if val is not None:
                        obj[prop_key] = val
                if obj:
                    frame_data[field] = obj
                    has_any = True
            else:
                # Simple field
                path = mapping.get("path") if isinstance(mapping, dict) else mapping
                val = get_by_path(frame, path)
                if val is not None:
                    frame_data[field] = val
                    has_any = True
        if has_any:
            output.append(frame_data)

    return output


def get_metadata():
    # --- Load and run ---
    with open("config.json", "r") as c:
        params = json.load(c)

    with open(params["input_json_file"], "r") as f:
        data = json.load(f)

    config_fields = params.get("field_mappings", {})

    try:
        metadata = extract_photo_metadata(data, config_fields)
        return metadata
    except Exception as e:
        print(f"[ERROR] Error: {e}")
