import subprocess
import os
import math

def list_video_files(directory):
    # List all .mp4 files in the specified directory
    return [f for f in os.listdir(directory) if f.endswith('.mp4')]

def get_video_duration(video_file):
    # Get the duration of the video file using ffprobe
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_file]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    duration = float(result.stdout.strip())
    return duration

def generate_contact_sheet(video_file, seconds_interval, output_file):
    interval = seconds_interval
    duration = get_video_duration(video_file)
    num_thumbnails = math.ceil(duration / interval)

    # Define the grid size based on the number of thumbnails
    cols = 5
    rows = math.ceil(num_thumbnails / cols)

    # Compose the ffmpeg command with dynamic grid layout and minimum height for thumbnails
    command = [
        'ffmpeg',
        '-i', video_file,
        '-vf', f'fps=1/{interval},scale=-1:250,drawtext=text=\'%{{pts\:hms}}\':x=10:y=10:fontsize=24:fontcolor=white@0.8,tile=layout={cols}x{rows}:padding=10',
        '-frames:v', '1',
        output_file
    ]
    subprocess.run(command, check=True)

def main():
    directory = './'
    video_files = list_video_files(directory)
    if video_files:
        for idx, file in enumerate(video_files):
            print(f"{idx + 1}: {file}")
        choice = int(input("Enter the number of the video file to process: ")) - 1
        video_file = video_files[choice]

        # Default interval is 30 seconds, but user can specify a different one
        seconds_interval = int(input("Enter the interval in seconds between each thumbnail (default 30 seconds): ") or "30")
        output_file = 'contact_sheet.jpg'

        generate_contact_sheet(video_file, seconds_interval, output_file)
        print("Contact sheet generated successfully.")
    else:
        print("No video files found in the directory.")

if __name__ == '__main__':
    main()
