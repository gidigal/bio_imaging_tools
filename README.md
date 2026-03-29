# bio_imaging_tools
tools to support reasearch using microscope images

## Calibration file
The `--calibration_file` argument expects a JSON file with the following fields:
| Field          | Type   | Required | Description                               |
|----------------|--------|----------|-------------------------------------------|
| `time_step`    | string | ✅       | interval in seconds between frames        |
| `pixel_size_um`| string | ✅       | the size of pixel in micrometers          |
| `mag`          | string | ✅       | the value of mag knob in Nikon microscope |
