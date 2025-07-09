# metadata-transfer

A Python script to transfer metadata from JSON files to images using the `piexif` and `Pillow` libraries. Currently supports transferring metadata stored in JSON files to JPEG images, but more formats (such as PNG and TIFF) will be added in the future.

## Idea

When I started doing film photography, I wanted to keep track of my settings for each photo for future reference (to see what different settings I should've used, or to remember what film I used for each photo, etc.). So I started writing down the settings on paper, but it was inconvenient. Then I found this amazing app called _[Exif Notes](https://play.google.com/store/apps/details?id=com.tommihirvonen.exifnotes&hl=en-US)_ (Android) that allows to easily input the settings and automatically fills in the location and the date. Then, all the data can be easily exported to a JSON file. However, I wanted to have the metadata directly in the image files for when I was editing them in Darktable or just browsing them, so I wrote this script to transfer it from the JSON files to the actual film scans.

The configuration file supports the JSON files exported by _Exif Notes_ by default, but it can be easily adapted to work with other JSON structures as well. Check the [Configuration](#configuration) section for more details.

## Download

You can download the latest version of the script from the [releases page](https://github.com/VladM7/metadata-transfer/releases). For now, the only supported platform is Windows. You can also build it from source if you want to run it on Linux or macOS, but I haven't tested it on those platforms yet.

## Configuration

A configuration file named `config.json` is already included in the repository. It is used for specifying the source directory containing the images and the destination directory where the modified images will be saved.

First make sure to change the `input_json_file` and `frames_folder_path` fields in the `config.json` file to point to the correct directories on your system. The `input_json_file` should point to the JSON file containing the metadata, and the `frames_folder_path` should point to the folder containing the images you want to modify. Both absolute paths and relative paths are supported.

```json
{
  "input_json_file": "path/to/input.json",
  "frames_folder_path": "path/to/frames/folder",
  "field_mappings": {
    // field mappings go here
  }
}
```

The `field_mappings` section allows you to specify how JSON fields map to EXIF tags. You can add or modify mappings as needed. It also supports nested fields.

### Examples:

If the input JSON file has a structure like this (for one of the frames):

```json
{
  "iso": 100,
  "shutter_speed": "1/125",
  "location": {
    "city": "Amsterdam",
    "coordinates": {
      "latitude": "40.7128",
      "longitude": "-74.0060"
    }
  }
  // other fields
}
```

You can map it to EXIF tags like this (in the `config.json` file):

```json
{
  "field_mappings": {
    "iso": { "path": "iso" },
    "shutter": { "path": "shutter_speed" },
    "location": {
      "fields": {
        "latitude": { "path": "location.coordinates.latitude" },
        "longitude": { "path": "location.coordinates.longitude" }
      }
    }
    // other mappings
  }
}
```

The `path` attribute is used for specifying the name of the attribute in the input JSON file (because, for example, the shutter speed may sometimes appear as "shutter", "shutter_speed", or even "shutter speed"). This way, the script can handle different naming conventions. The dots indicate nested fields in the JSON structure.

### Supported Fields

Currently only the fields present in the `field_mappings` section will be transferred to the images:

- ISO
- camera make and model
- shutter speed
- aperture
- focal length
- lens make and model
- date and time
- latitude and longitude
- description

The ISO field is mapped to the `Exif.Photo.ISOSpeedRatings` tag, the camera make and model to `Exif.Image.Make` and `Exif.Image.Model`, and so on. The latitude and longitude are stored in the GPS tags (`GPSInfo.GPSLatitude` and `GPSInfo.GPSLongitude`).

The ISO and camera parameters can be specified either only once or multiple times in the JSON file, and the script will handle both cases. If the ISO is specified multiple times, the last value will be used.

Additional fields present in the JSON files will be ignored (such as `city` in the example above). In the future the script may be extended to support more fields, but for now it is focused on the most commonly used metadata fields.

For now I opted for a safer, but more manual approach in which the user has to specify the field mappings in the configuration file, but in the future I may add a feature to automatically detect the fields in the JSON files and create a default mapping based on that (probably using AI).

## Other Remarks

- by default, the images are processed in the alphabetical order of their filenames (first frame in the input file corresponds to the first image in the folder, second frame to the second image, and so on).
- the script will modify the original images by adding the metadata to them, so make sure to back them up first if you want to keep the original files unchanged; there will be no modifications to the actual content of the images, only the metadata will be added.
- the other metadata parameters (such as `title`, `comments`, etc.) will not be overwritten, only the ones specified in the configuration file will be added or updated.

## Contributing

Pull requests, issues, ideas and suggestions are welcome!

## License

[MIT License](./LICENSE)

## Acknowledgments

This project uses the following libraries:

- [piexif](https://github.com/hMatoba/Piexif)
- [Pillow](https://github.com/python-pillow/Pillow)

And once again shoutout to the [Exif Notes](https://play.google.com/store/apps/details?id=com.tommihirvonen.exifnotes&hl=en-US) app for inspiring this project!
