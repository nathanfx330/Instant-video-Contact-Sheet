# Instant Video Contact Sheet (IVCS)

**Instant Video Contact Sheet (IVCS)** is a Python script that quickly generates a grid of video thumbnails from a video file at user-defined intervals. This tool allows you to create a visual summary of key frames from a video, which is perfect for content creators, video editors, or anyone looking for a quick overview of video content.

## Requirements

This script uses the following Python libraries:
- `subprocess` (Built-in Python library)
- `os` (Built-in Python library)
- `math` (Built-in Python library)

### External Dependencies

In addition to Python libraries, **ffmpeg** and **ffprobe** must be installed on your system. These tools are used for extracting video duration and generating thumbnails.

- **ffmpeg**: A complete, cross-platform solution to record, convert, and stream audio and video.
- **ffprobe**: A multimedia stream analyzer that is bundled with ffmpeg.

## Installation

### Step 1: Install Python Dependencies
Since the script only relies on built-in Python libraries, no additional Python packages need to be installed. However, make sure you have Python 3.x installed.

### Step 2: Install ffmpeg and ffprobe

#### For Ubuntu/Debian:
```bash
sudo apt-get install ffmpeg
```

#### For macOS (using Homebrew):
```bash
brew install ffmpeg
```

#### For Windows:
- Download the latest version of ffmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html).
- Follow the installation instructions for Windows.

Ensure that `ffmpeg` and `ffprobe` are accessible in your system's PATH so that the script can use them.

## Usage

1. Clone this repository or download the script to your local machine.
2. Place your video files (in `.mp4` format) in the same directory as the script.
3. Run the script:

```bash
python IVCS.py
```

4. Follow the on-screen prompts:
    - Select the video file you want to process.
    - Enter the interval in seconds between each thumbnail (default is 30 seconds).
    - The script will generate a contact sheet named `video_name_contact_sheet.jpg` containing the thumbnails.

## Welcome to Instant Video Contact Sheet (IVCS)! 

Place your video in the IVCP folder and run IVCS.py.

    If only one video is found, the process will begin automatically.

    If two or more videos are found, you will be prompted to select which one to use.

Contact sheet generated successfully: example_video_contact_sheet.jpg



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
