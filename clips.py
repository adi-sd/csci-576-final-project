import os
import random
from moviepy.video.io.VideoFileClip import VideoFileClip


def extract_random_clips(
    video_path, output_folder, notes_file, num_clips=2, min_duration=20, max_duration=40
):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Open a text file for notes
    with open(notes_file, "w") as notes:
        # List all video files in the specified path
        video_files = [
            f for f in os.listdir(video_path) if f.endswith((".mp4", ".avi", ".mkv"))
        ]

        for video_file in video_files:
            # Construct the full path to the video file
            video_file_path = os.path.join(video_path, video_file)

            # Generate random start times for the clips
            start_times = [
                random.uniform(
                    0, VideoFileClip(video_file_path).duration - max_duration
                )
                for _ in range(num_clips)
            ]

            for i, start_time in enumerate(start_times):
                # Randomly select a duration between min_duration and max_duration
                duration = random.uniform(min_duration, max_duration)

                # Create VideoFileClip object
                video_clip = VideoFileClip(video_file_path).subclip(
                    start_time, start_time + duration
                )

                # Save the clip to the output folder
                output_filename = f"{os.path.splitext(video_file)[0]}_clip{i + 1}.mp4"
                output_path = os.path.join(output_folder, output_filename)
                video_clip.write_videofile(
                    output_path, codec="libx264", audio_codec="aac"
                )

                # Write notes to the text file
                notes.write(f"Video: {video_file}, Clip {i + 1}\n")
                notes.write(f"  Start Frame: {int(start_time * video_clip.fps)}\n")
                notes.write(f"  Start Time: {start_time:.2f} seconds\n\n")


if __name__ == "__main__":
    # Provide the path to your video library, output folder, and notes file
    video_library_path = "/Users/adi.s.d/Downloads/drive-download-20231207T012008Z-001"
    output_folder_path = (
        "/Users/adi.s.d/Downloads/drive-download-20231207T012008Z-001/clips"
    )
    notes_file_path = (
        "/Users/adi.s.d/Downloads/drive-download-20231207T012008Z-001/notes.txt"
    )

    # Specify the number of clips and duration range
    num_clips_per_video = 2
    min_clip_duration = 20
    max_clip_duration = 40

    # Call the function to extract random clips and generate notes
    extract_random_clips(
        video_library_path,
        output_folder_path,
        notes_file_path,
        num_clips_per_video,
        min_clip_duration,
        max_clip_duration,
    )
