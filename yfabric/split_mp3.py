import subprocess


def ms_to_hhmmss(ms):
    seconds = ms // 1000
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hrs:02}:{mins:02}:{secs:02}"


input_file = "audio.mp3"
timestamps_file = "cuts.txt"
output_template = "part_{}.mp3"


def split_audio(input_file, timestamps_file):
    with open(timestamps_file, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        parts = line.strip().split()
        if not parts:
            continue  # Skip empty lines
        start_ms = int(parts[0])
        start = ms_to_hhmmss(start_ms)
        output_file = output_template.format(i)

        if len(parts) == 2:
            end_ms = int(parts[1])
            end = ms_to_hhmmss(end_ms)
            cmd = [
                "ffmpeg",
                "-i", input_file,
                "-ss", start,
                "-to", end,
                "-c", "copy",
                output_file
            ]
            print(f"Creating {output_file} from {start} to {end}...")
        else:
            cmd = [
                "ffmpeg",
                "-i", input_file,
                "-ss", start,
                "-c", "copy",
                output_file
            ]
            print(f"Creating {output_file} from {start} to end of file...")

        subprocess.run(cmd)


if __name__ == "__main__":
    split_audio(input_file, timestamps_file)

