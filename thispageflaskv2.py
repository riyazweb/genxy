from flask import Flask, render_template, request, redirect, url_for
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, ImageClip
from moviepy.video.fx.all import resize
import moviepy.editor as mp
from pyngrok import ngrok
import os
import yt_dlp

# Set your ngrok authtoken
NGROK_AUTHTOKEN = "2e5HfihdTLSWD2nmcoXXDzjxib9_7TVpQakJDni6zHKDv4ag7"
ngrok.set_auth_token(NGROK_AUTHTOKEN)
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_link = request.form['video_link']
        tiktok = request.form['tiktok']
        start_time = int(request.form['start_time'])
        starts = int(request.form['starts'])
        # Process video
        process_video(video_link, start_time, starts, tiktok)

        return redirect(url_for('index'))

    return render_template('index.html')


def process_video(video_link, start_time, starts, tiktok):
    file_name = "videox.webm"

    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"{file_name} has been deleted.")
    else:
        print(f"{file_name} does not exist.")

    # Download video
    filename = "videox"

    if video_link:
        download_video(video_link, filename)
    elif tiktok:
        from tiktok_downloader import snaptik
        video_url = tiktok
        downloaded_video = snaptik(video_url)
        if downloaded_video:
            downloaded_video[0].download('videox.mp4')
            print("Video downloaded successfully.")
        else:
            print("No videos found.")
    else:
        print("No valid video source provided.")
        return

    # Set the dimensions of the video
    VIDEO_WIDTH = 720
    VIDEO_HEIGHT = 1280

    # Load the video
    if os.path.isfile(f'{filename}.webm'):
        video_clip = VideoFileClip(f'{filename}.webm')
    elif os.path.isfile(f'{filename}.mp4'):
        video_clip = VideoFileClip(f'{filename}.mp4')
    else:
        print("Video file not found.")
        return

    video_duration = video_clip.duration
    segment_duration = 59  # Change to 30 seconds

    # Process the video in 30-second segments
    for i in range(0, int(video_duration) - start_time, segment_duration):
        start = i + start_time
        end = min(start + segment_duration, video_duration)
        video_segment = video_clip.subclip(start, end)

        # Resize the segment clip
        if video_link:
            resized_clip = resize(video_segment, width=1000)
        else:
            resized_clip = video_segment

        # Create a blank clip with the target dimensions
        background_clip = ColorClip((VIDEO_WIDTH, VIDEO_HEIGHT), color=[
                                    0, 0, 0], duration=resized_clip.duration)

        # Place the resized video clip at the center of the blank clip
        x_pos = (VIDEO_WIDTH - resized_clip.w) / 2
        y_pos = (VIDEO_HEIGHT - resized_clip.h) / 2
        video_clip_centered = CompositeVideoClip(
            [background_clip, resized_clip.set_pos((x_pos, y_pos))])

        # Load the images and resize them to fit the video width
        if starts == 1:
            cat_image = ImageClip("layers/topx.png")
        elif starts == 2:
            cat_image = ImageClip("layers/topx2.png")
        elif starts == 3:
            cat_image = ImageClip("layers/topx3.png")
        elif starts == 4:
            cat_image = ImageClip("layers/topx4.png")
        elif starts == 5:
            cat_image = ImageClip("layers/topx5.png")
        cat_image_resized = cat_image.resize(width=VIDEO_WIDTH)

        # Set the position of the image clips
        cat_clip = cat_image_resized.set_duration(video_segment.duration)
        cat_clip = cat_clip.set_pos((0, 0))

        # Combine the image clips and video clip
        final_clip = CompositeVideoClip([video_clip_centered, cat_clip])

        # Set the audio
        final_clip = final_clip.set_audio(video_segment.audio)

        # Save the final video file
        output_folder = 'xexports'
        os.makedirs(output_folder, exist_ok=True)
        output_filename = os.path.join(
            output_folder, f'output_{i//segment_duration + 1}.mp4')

        # Check if the file already exists
        if os.path.isfile(output_filename):
            # If it does, add a number to the filename to create a unique name
            basename, extension = os.path.splitext(output_filename)
            i = 1
            while os.path.isfile(f"{basename}_{i}{extension}"):
                i += 1
            output_filename = f"{basename}_{i}{extension}"

        final_clip.write_videofile(
            output_filename, codec="libx264", preset="ultrafast")

    video_clip.close()


def download_video(video_link, filename):
    ydl_opts = {
        'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        'outtmpl': f'{filename}.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_link])


if __name__ == '__main__':
    # Start ngrok tunnel
    public_url = ngrok.connect(**{"addr": 5000})
    print('Public URL:', public_url)

    # Run Flask app
    app.run(host='localhost', port=5000)
