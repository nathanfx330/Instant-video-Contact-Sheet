#!/usr/bin/env python3

import subprocess
import os
import math
import sys
import argparse
import shlex  # For safely quoting arguments in printed commands

# --- Constants ---
DEFAULT_INTERVAL = 30
DEFAULT_COLUMNS = 5
DEFAULT_THUMBNAIL_HEIGHT = 250
DEFAULT_VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
FFMPEG_COMMAND = 'ffmpeg'
FFPROBE_COMMAND = 'ffprobe'

# --- Helper Functions ---

def find_command(cmd_name):
    """Check if a command exists in the system PATH."""
    from shutil import which
    if which(cmd_name) is None:
        print(f"Error: Command '{cmd_name}' not found.", file=sys.stderr)
        print(f"Please ensure '{cmd_name}' (part of FFmpeg) is installed and in your system's PATH.", file=sys.stderr)
        return False
    return True

def list_video_files(directory, extensions):
    """List video files with specified extensions in the directory."""
    try:
        files = os.listdir(directory)
        video_files = [
            f for f in files
            if os.path.isfile(os.path.join(directory, f)) and
               os.path.splitext(f)[1].lower() in extensions
        ]
        return sorted(video_files) # Sort for consistent ordering
    except FileNotFoundError:
        print(f"Error: Directory not found: '{directory}'", file=sys.stderr)
        return None
    except PermissionError:
         print(f"Error: Permission denied for directory: '{directory}'", file=sys.stderr)
         return None

def get_video_duration(video_file):
    """Get the duration of the video file using ffprobe."""
    cmd = [
        FFPROBE_COMMAND,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_file
    ]
    try:
        # Use check=True to automatically raise CalledProcessError on non-zero exit
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, check=True, encoding='utf-8')
        duration_str = result.stdout.strip()
        if not duration_str:
             print(f"Warning: ffprobe returned empty duration for '{video_file}'. Assuming 0.", file=sys.stderr)
             return 0.0
        duration = float(duration_str)
        if duration < 0:
             print(f"Warning: ffprobe returned negative duration ({duration}s) for '{video_file}'. Using 0.", file=sys.stderr)
             return 0.0
        return duration
    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe on '{video_file}':", file=sys.stderr)
        # shlex.join is available in Python 3.8+, provide fallback for older versions
        try:
             cmd_str = shlex.join(cmd)
        except AttributeError:
             cmd_str = ' '.join(shlex.quote(arg) for arg in cmd)
        print(f"  Command: {cmd_str}", file=sys.stderr)
        print(f"  Stderr: {e.stderr.strip()}", file=sys.stderr)
        return None
    except ValueError as e:
        print(f"Error parsing ffprobe duration output for '{video_file}': {e}", file=sys.stderr)
        print(f"  ffprobe stdout: '{result.stdout.strip()}'", file=sys.stderr)
        return None
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred while getting duration for '{video_file}': {e}", file=sys.stderr)
        return None

def generate_contact_sheet(video_file, seconds_interval, output_file, cols, thumb_height):
    """Generates the contact sheet using ffmpeg."""
    print(f"Processing '{os.path.basename(video_file)}'...")

    duration = get_video_duration(video_file)
    if duration is None:
        return False # Error already printed by get_video_duration

    if duration == 0:
        print(f"Video '{os.path.basename(video_file)}' has zero duration. Skipping.", file=sys.stderr)
        return False # Cannot generate sheet for zero-duration video

    # Ensure interval is positive
    if seconds_interval <= 0:
        print("Error: Interval must be a positive number.", file=sys.stderr)
        return False

    num_thumbnails = math.ceil(duration / seconds_interval)
    if num_thumbnails == 0:
        print(f"Warning: Calculated 0 thumbnails for '{os.path.basename(video_file)}' (duration={duration:.2f}s, interval={seconds_interval}s). Skipping.", file=sys.stderr)
        # Or potentially create a single frame? For now, skip.
        return False

    rows = math.ceil(num_thumbnails / cols)

    # Compose the complex ffmpeg filtergraph
    # fps=1/interval: Select one frame every 'interval' seconds
    # scale=-1:thumb_height: Scale width proportionally to fixed height
    # drawtext: Add timestamp (HH:MM:SS)
    # tile: Arrange frames in a grid with padding
    vf_filter = (
        f"fps=1/{seconds_interval},"
        f"scale=-1:{thumb_height},"
        f"drawtext=text='%{{pts\:hms}}':x=10:y=10:fontsize=24:fontcolor=white@0.8:box=1:boxcolor=black@0.5:boxborderw=5,"
        f"tile=layout={cols}x{rows}:padding=10:margin=10" # Added margin
    )

    command = [
        FFMPEG_COMMAND,
        '-loglevel', 'warning', # Show warnings and errors, hide info
        '-i', video_file,
        '-vf', vf_filter,
        '-frames:v', '1',   # Output only one image (the tiled sheet)
        '-q:v', '3',       # Quality scale for VBR JPEGs (1=best, 31=worst, 2-5 is good)
        '-y',              # Overwrite output file without asking
        output_file
    ]

    print(f"Generating contact sheet ({cols}x{rows} grid, {num_thumbnails} thumbnails)...")
    # Print the command safely quoted for debugging if needed
    try:
        cmd_str = shlex.join(command)
    except AttributeError:
        cmd_str = ' '.join(shlex.quote(arg) for arg in command)
    # print(f"  Running command: {cmd_str}") # Uncomment for debugging

    try:
        subprocess.run(command, stderr=subprocess.PIPE, text=True, check=True, encoding='utf-8')
        print(f"Successfully generated contact sheet: '{output_file}'")
        return True # Indicate success
    except subprocess.CalledProcessError as e:
        print(f"\nError running ffmpeg:", file=sys.stderr)
        print(f"  Command: {cmd_str}", file=sys.stderr)
        print(f"  Stderr: {e.stderr.strip()}", file=sys.stderr)
        # Attempt to remove potentially incomplete output file
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                print(f"Removed incomplete output file '{output_file}'.")
            except OSError as remove_err:
                print(f"Warning: Could not remove incomplete file '{output_file}': {remove_err}", file=sys.stderr)
        return False
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred during ffmpeg execution: {e}", file=sys.stderr)
        return False


# --- Main Execution ---

def main():
    # --- Check Dependencies ---
    if not find_command(FFPROBE_COMMAND) or not find_command(FFMPEG_COMMAND):
        sys.exit(1)

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Generate a contact sheet (thumbnail grid) from a video file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Show defaults in help
    )
    parser.add_argument(
        'video_file',
        nargs='?', # Make it optional if we use interactive mode later
        help="Path to the video file to process. If omitted, scans the current directory."
    )
    parser.add_argument(
        '-d', '--dir',
        default='.',
        help="Directory to scan for video files if 'video_file' argument is omitted."
    )
    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=DEFAULT_INTERVAL,
        help="Interval in seconds between thumbnails."
    )
    parser.add_argument(
        '-o', '--output',
        help="Output filename for the contact sheet. "
             "If omitted, defaults to '<video_filename>_contact.jpg' in the video's directory."
    )
    parser.add_argument(
        '-c', '--columns',
        type=int,
        default=DEFAULT_COLUMNS,
        help="Number of columns in the thumbnail grid."
    )
    parser.add_argument(
        '-H', '--height',
        type=int,
        default=DEFAULT_THUMBNAIL_HEIGHT,
        help="Height of each thumbnail in pixels."
    )
    parser.add_argument(
        '-e', '--ext',
        action='append', # Use action='append' to collect multiple extensions
        default=[], # Start with empty, will add defaults later if needed
        help=f"Video file extensions to look for (can be specified multiple times). Default: {' '.join(DEFAULT_VIDEO_EXTENSIONS)}"
    )
    parser.add_argument(
        '-ni', '--non-interactive',
        action='store_true',
        help="Do not prompt for video selection if multiple files are found (requires 'video_file' argument)."
    )

    args = parser.parse_args()

    # --- Validate Arguments ---
    if args.interval <= 0:
        parser.error("Interval must be a positive integer.")
    if args.columns <= 0:
        parser.error("Number of columns must be a positive integer.")
    if args.height <= 0:
        parser.error("Thumbnail height must be a positive integer.")

    # Process extensions: use default if none provided via -e
    video_extensions = [ext.lower() if ext.startswith('.') else '.' + ext.lower()
                        for ext in args.ext] if args.ext else DEFAULT_VIDEO_EXTENSIONS

    # --- Select Video File ---
    target_video_file = None
    video_directory = args.dir # Default directory

    if args.video_file:
        # Specific file provided
        if not os.path.isfile(args.video_file):
            print(f"Error: Specified video file not found: '{args.video_file}'", file=sys.stderr)
            sys.exit(1)
        target_video_file = args.video_file
        video_directory = os.path.dirname(target_video_file) or '.' # Get directory from file path
    else:
        # No specific file, scan directory
        print(f"Scanning directory '{os.path.abspath(args.dir)}' for video files ({', '.join(video_extensions)})...")
        video_files = list_video_files(args.dir, video_extensions)

        if video_files is None: # Error occurred during listing
            sys.exit(1)
        if not video_files:
            print(f"No video files with extensions ({', '.join(video_extensions)}) found in '{os.path.abspath(args.dir)}'.")
            sys.exit(0)

        if len(video_files) == 1:
            print(f"Found one video file: {video_files[0]}")
            target_video_file = os.path.join(args.dir, video_files[0])
        elif args.non_interactive:
             print(f"Error: Multiple video files found in '{os.path.abspath(args.dir)}' but running in non-interactive mode.", file=sys.stderr)
             print("Please specify a single video file using the 'video_file' argument.", file=sys.stderr)
             sys.exit(1)
        else:
            # Interactive selection
            print("\nFound multiple video files:")
            for idx, file in enumerate(video_files):
                print(f"  {idx + 1}: {file}")

            choice = -1
            while choice < 0 or choice >= len(video_files):
                try:
                    choice_str = input(f"Enter the number of the video file to process (1-{len(video_files)}): ")
                    choice_num = int(choice_str)
                    if 1 <= choice_num <= len(video_files):
                        choice = choice_num - 1
                    else:
                        print("Invalid choice. Please enter a number from the list.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except EOFError: # Handle Ctrl+D
                    print("\nOperation cancelled by user.")
                    sys.exit(1)

            target_video_file = os.path.join(args.dir, video_files[choice])

    # --- Determine Output File ---
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(os.path.basename(target_video_file))[0]
        # Place output in the *same directory* as the input video
        output_file = os.path.join(video_directory, f"{base_name}_contact.jpg")

    # Ensure output directory exists (useful if args.output specifies a path)
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.isdir(output_dir):
        try:
            print(f"Creating output directory: '{output_dir}'")
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(f"Error: Could not create output directory '{output_dir}': {e}", file=sys.stderr)
            sys.exit(1)


    # --- Generate Sheet ---
    success = generate_contact_sheet(
        video_file=target_video_file,
        seconds_interval=args.interval,
        output_file=output_file,
        cols=args.columns,
        thumb_height=args.height
    )

    if success:
        print("\nDone.")
        sys.exit(0)
    else:
        print("\nContact sheet generation failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
