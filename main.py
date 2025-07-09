import json
import os
import piexif
from PIL import Image

from utils import shutter_speed_to_apex_rational, aperture_to_apex_rational
from json_processor import get_metadata

with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Load the images
images_path = config["frames_folder_path"]

# Load all images from the frames folder
images = []
image_file_paths = []
for image_file in sorted(os.listdir(images_path)):
    if image_file.endswith((".jpg", ".jpeg", ".TIF")):
        full_path = os.path.join(images_path, image_file)
        try:
            im = Image.open(full_path)
            images.append(im)
            image_file_paths.append(full_path)
        except Exception as e:
            print(f"[!] Warning: Could not open '{image_file}' as an image: {e}")

# Check if we have any images to process
if not images:
    raise ValueError("No images found in the specified frames folder.")

# For each image, we will modify the EXIF data


# Helper to extract field names from config
def get_field_name(field):
    return (
        config["field_mappings"][field] if field in config["field_mappings"] else field
    )


# Helper to extract nested field names from config
def get_nested_field_info(field):
    field_info = config["field_mappings"][field]
    if isinstance(field_info, dict):
        name = field_info.get("name", field)
        props = field_info.get("props", {})
        return name, props
    else:
        return field_info, None


# Get metadata list
metadata_list = get_metadata()
if not metadata_list:
    raise ValueError("No metadata found.")
# If there are more images than metadata frames, raise error
if len(images) > len(metadata_list):
    raise ValueError(
        f"There are more images ({len(images)}) than metadata frames ({len(metadata_list)}). Aborting."
    )
# If there are less images than metadata frames, it's fine; only process as many as there are images
print(
    f"Found {len(metadata_list)} valid metadata frames, processing {len(images)} images."
)
metadata_list = metadata_list[: len(images)]

for idx, (im, original_path, metadata) in enumerate(
    zip(images, image_file_paths, metadata_list)
):
    try:
        exif_bytes = im.info.get("exif", b"")
        if not exif_bytes:
            # Initialize a fresh EXIF dict if none exists
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        else:
            exif_dict = piexif.load(exif_bytes)
        exif_ifd = exif_dict["Exif"]
        zeroth_ifd = exif_dict["0th"]

        # ISO
        if "iso" in metadata:
            try:
                iso = int(metadata.get("iso", 100))
                exif_ifd[piexif.ExifIFD.ISOSpeedRatings] = iso
            except (ValueError, TypeError):
                print(
                    f"[!] Warning: ISO data not found or invalid for image {idx + 1}."
                )
        else:
            print(f"[!] Warning: ISO field missing for image {idx + 1}.")

        # Shutter
        if "shutter" in metadata:
            exif_ifd[piexif.ExifIFD.ShutterSpeedValue] = shutter_speed_to_apex_rational(
                metadata["shutter"]
            )
        else:
            print(f"[!] Warning: Shutter field missing for image {idx + 1}.")

        # Aperture
        if "aperture" in metadata:
            exif_ifd[piexif.ExifIFD.ApertureValue] = aperture_to_apex_rational(
                metadata["aperture"]
            )
        else:
            print(f"[!] Warning: Aperture field missing for image {idx + 1}.")

        # Focal Length
        if "focal_length" in metadata:
            from utils import float_to_rational

            try:
                exif_ifd[piexif.ExifIFD.FocalLength] = float_to_rational(
                    float(metadata["focal_length"])
                )
            except Exception:
                print(f"[!] Warning: Focal length invalid for image {idx + 1}.")
        else:
            print(f"[!] Warning: Focal length field missing for image {idx + 1}.")

        # Date
        if "date" in metadata:
            import re

            dt = metadata["date"]
            match = re.match(
                r"(\d{4})[-:]?(\d{2})[-:]?(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?", dt
            )
            if match:
                seconds = match.group(6) if match.group(6) is not None else "00"
                dt_exif = f"{match.group(1)}:{match.group(2)}:{match.group(3)} {match.group(4)}:{match.group(5)}:{seconds}"
            else:
                dt_exif = dt
            exif_ifd[piexif.ExifIFD.DateTimeOriginal] = dt_exif
            exif_ifd[piexif.ExifIFD.DateTimeDigitized] = dt_exif
            zeroth_ifd[piexif.ImageIFD.DateTime] = dt_exif
        else:
            print(f"[!] Warning: Date field missing for image {idx + 1}.")

        # Lens
        if "lens" in metadata:
            lens = metadata["lens"]
            lens_str = " ".join(
                str(lens.get(k, "")) for k in ["make", "model"] if lens.get(k)
            )
            if lens_str:
                if hasattr(piexif.ExifIFD, "LensModel"):
                    exif_ifd[piexif.ExifIFD.LensModel] = lens_str
                else:
                    exif_ifd[piexif.ExifIFD.UserComment] = lens_str.encode("utf-8")
        else:
            print(f"[!] Warning: Lens field missing for image {idx + 1}.")

        # Camera
        if "camera" in metadata:
            cam = metadata["camera"]
            zeroth_ifd[piexif.ImageIFD.Make] = ""
            zeroth_ifd[piexif.ImageIFD.Model] = ""
            make_val = cam.get("make")
            model_val = cam.get("model")
            if make_val is not None and isinstance(make_val, (str, int, float)):
                zeroth_ifd[piexif.ImageIFD.Make] = str(make_val)
            else:
                print(
                    f"[!] Warning: Camera make missing or invalid for image {idx + 1}."
                )
            if model_val is not None and isinstance(model_val, (str, int, float)):
                zeroth_ifd[piexif.ImageIFD.Model] = str(model_val)
            else:
                print(
                    f"[!] Warning: Camera model missing or invalid for image {idx + 1}."
                )
        else:
            print(f"[!] Warning: Camera field missing for image {idx + 1}.")

        # Description
        if "description" in metadata:
            desc = metadata["description"]
            if isinstance(desc, str):
                zeroth_ifd[piexif.ImageIFD.ImageDescription] = desc
            else:
                print(f"[!] Warning: Description is not a string for image {idx + 1}.")
        else:
            print(f"[!] Warning: Description field missing for image {idx + 1}.")

        # Location
        if "location" in metadata:
            obj = metadata["location"]
            gps_ifd = exif_dict.get("GPS", {})
            lat_val = obj.get("latitude")
            lon_val = obj.get("longitude")
            lat_ok = False
            lon_ok = False
            if lat_val is not None:
                try:
                    lat = float(lat_val)
                    gps_ifd[piexif.GPSIFD.GPSLatitudeRef] = "N" if lat >= 0 else "S"
                    abs_lat = abs(lat)
                    gps_ifd[piexif.GPSIFD.GPSLatitude] = [
                        (int(abs_lat), 1),
                        (int((abs_lat * 60) % 60), 1),
                        (int((abs_lat * 3600) % 60), 1),
                    ]
                    lat_ok = True
                except Exception:
                    print(f"[!] Warning: Latitude invalid for image {idx + 1}.")
            else:
                print(f"[!] Warning: Latitude field missing for image {idx + 1}.")
            if lon_val is not None:
                try:
                    lon = float(lon_val)
                    gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = "E" if lon >= 0 else "W"
                    abs_lon = abs(lon)
                    gps_ifd[piexif.GPSIFD.GPSLongitude] = [
                        (int(abs_lon), 1),
                        (int((abs_lon * 60) % 60), 1),
                        (int((abs_lon * 3600) % 60), 1),
                    ]
                    lon_ok = True
                except Exception:
                    print(f"[!] Warning: Longitude invalid for image {idx + 1}.")
            else:
                print(f"[!] Warning: Longitude field missing for image {idx + 1}.")
            if lat_ok and lon_ok:
                exif_dict["GPS"] = gps_ifd
            else:
                print(
                    f"[!] Warning: Skipping GPS EXIF for image {idx + 1} because latitude or longitude is missing or invalid."
                )
        else:
            print(f"[!] Warning: Location field missing for image {idx + 1}.")

        # Write back the new EXIF data
        exif_bytes = piexif.dump(exif_dict)
        # im.save(new_path, exif=exif_bytes, quality=100, subsampling=0, optimize=False)
        piexif.insert(exif_bytes, original_path, original_path)

        print(f"[OK] Processed image {idx + 1}/{len(images)}: {original_path}\n")
    except piexif._exceptions.InvalidImageDataError as e:
        print(
            f"[!] Skipping image {idx + 1}/{len(images)}: {original_path} (piexif does not support writing EXIF to this TIFF file): {e}"
        )
        continue
    except Exception as e:
        import traceback

        print(
            f"[ERROR] Error processing image {idx + 1}/{len(images)}: {type(e).__name__}: {e}"
        )
        traceback.print_exc()
        continue

input("Press any key to continue...")
