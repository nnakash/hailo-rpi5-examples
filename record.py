#!/usr/bin/env python
from moviepy.editor import AudioFileClip
import signal
import subprocess
import time


# Load the WAV file


class Recorder:
    def start(self):
        """
        starts a recording for 60 seconds
        non blocking
        """
        print("starting recording for 60 seconds")
        self._proc = subprocess.Popen(
            "arecord -c 2 -d 60 input.wav",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("started recording for 60 seconds")

    def stop(self):
        """
        stops the recording and saves the .wav file
        """
        self._proc.send_signal(signal.SIGKILL)
        self._proc.wait()
        print("stopped recording")
        self._save()

    def _save(self):
        """
        saves the recording in format mp4
        """
        audio_clip = AudioFileClip("input.wav")
        audio_clip.write_audiofile("output.mp4", codec="aac")


if __name__ == "__main__":
    app = Recorder()

    # controlled from UI
    app.start()
    time.sleep(3) # change to 60 - sleep "forever"

    # controlled from UI
    app.stop()
