import os
import cv2
import easyocr
from datetime import timedelta

# === CONFIG ===
VIDEO_DIR = "./videos"  # Path to your folder containing .mp4 files
FRAME_SKIP = 5
CROP_BOTTOM_RATIO = 1/3

# === OCR SETUP ===
reader = easyocr.Reader(['ch_sim', 'en'])

# === UTIL ===
def to_vtt_time(frame, fps):
    seconds = frame / fps
    td = timedelta(seconds=seconds)
    total = str(td)
    if '.' not in total:
        total += '.000'
    else:
        total = total[:-3] + total[-3:]  # ensure 3 decimal places
    return total.replace(',', '.')

def process_video(video_path):
    print(f"📽️ Processing: {video_path}")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_vtt = os.path.join(os.path.dirname(video_path), f"{base_name}.vtt")

    prev_text = ""
    start_frame = None
    subtitles = []
    frame_num = 0
    srt_index = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % FRAME_SKIP == 0:
            h, w, _ = frame.shape
            cropped = frame[int(h * (1 - CROP_BOTTOM_RATIO)):, :]

            result = reader.readtext(cropped, detail=0)
            current_text = ''.join(result).strip()

            if current_text != prev_text:
                if prev_text and start_frame is not None:
                    start = to_vtt_time(start_frame, fps)
                    end = to_vtt_time(frame_num - 1, fps)
                    subtitles.append((srt_index, start, end, prev_text))
                    srt_index += 1

                prev_text = current_text
                start_frame = frame_num

        frame_num += 1

    if prev_text and start_frame is not None:
        start = to_vtt_time(start_frame, fps)
        end = to_vtt_time(frame_num - 1, fps)
        subtitles.append((srt_index, start, end, prev_text))

    cap.release()

    # Write .vtt
    with open(output_vtt, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for _, start, end, text in subtitles:
            f.write(f"{start} --> {end}\n{text}\n\n")

    print(f"✅ Saved: {output_vtt}")

# === MAIN LOOP ===
if __name__ == "__main__":
    for filename in os.listdir(VIDEO_DIR):
        if filename.lower().endswith(".mp4"):
            full_path = os.path.join(VIDEO_DIR, filename)
            process_video(full_path)
