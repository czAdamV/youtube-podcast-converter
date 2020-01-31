import ffmpeg
import subprocess


def transcode(input, encoder, bitrate):
    # Inspired by https://github.com/kkroening/ffmpeg-python/issues/156
    args = (
        ffmpeg
        .input('pipe:')
        .audio
        .output('pipe:', format=encoder, audio_bitrate=bitrate)
        .global_args('-hide_banner')
        .global_args('-loglevel', 'error')
        .compile()
    )

    completed = subprocess.run(args, input=input, capture_output=True)

    if not completed.returncode == 0:
        stderr = completed.stderr.decode()

        pipe = 'pipe:: '
        if stderr.startswith(pipe):
            stderr = stderr[len(pipe):]

        raise RuntimeError(
            stderr.strip()
        )

    return completed.stdout
