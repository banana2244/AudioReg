import argparse
from datetime import datetime
import os
import logging
import mutagen
import warnings
import tkinter as tk
from tkinter import filedialog

#NOTE: WHEN RUNNING FFMPEG EXE MUST BE LOCATED FOR NON WAV FILES TO PROCESS(in same directory as script)
with warnings.catch_warnings():
    # Silence RuntimeWarning about absence of ffmpeg
    warnings.simplefilter("ignore")
    from pydub import AudioSegment

Supported = ('.wav', '.flac', '.mp3', '.ogg', '.webm', '.mp4')


class AudioNormalizerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Audio Normalizer")

        self.dir_path = None
        self.db_value = tk.StringVar(value="-13.5")

        # Directory Selection
        self.dir_button = tk.Button(
            master, text="Select Directory", command=self.select_directory)
        self.dir_button.grid(row=0, column=0, padx=10, pady=10)

        self.dir_label = tk.Label(master, text="")
        self.dir_label.grid(row=0, column=1)

        # Decibels Entry
        self.db_label = tk.Label(master, text="Decibels:")
        self.db_label.grid(row=1, column=0, padx=10, pady=10)

        self.db_entry = tk.Entry(master, textvariable=self.db_value)
        self.db_entry.grid(row=1, column=1)

        # Normalize Button
        self.norm_button = tk.Button(
            master, text="Normalize", command=self.normalize)
        self.norm_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    def select_directory(self):
        self.dir_path = filedialog.askdirectory()
        self.dir_label.config(text=self.dir_path)

    def normalize(self):
        if self.dir_path is not None:
            #Files = [os.path.join(self.dir_path, f) for f in os.listdir(self.dir_path) if f.endswith(Supported)]
            Files = []
            for f in os.listdir(self.dir_path):
                if f.endswith(Supported):
                    Files.append(os.path.join(self.dir_path, f))
            #tk.messagebox.showinfo("Bruh", Files)
            process_files(Files, float(self.db_value.get()))

            tk.messagebox.showinfo(
                "Normalization Complete", "Audio files have been normalized.")
        else:
            tk.messagebox.showerror("Error", "Please select a directory.")



# Check if given files exist in the file system, credit to u/giannisterzopoulos :)
def _valid_files(file):
    if not os.path.isfile(file):
        msg = 'File cannot be found : {}'.format(file)
        raise argparse.ArgumentTypeError(msg)
    elif not file.endswith(Supported):
        msg = 'File format is not supported : {}'.format(file)
        raise argparse.ArgumentTypeError(msg)
    else:
        return file


# Configure logging
def get_logger(mod_name):
    log = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    return log


logger = get_logger(__name__)

#process files in target directory using gui input, files saved to directory=''
def process_files(Files, target_dbfs, directory='NORMALIZED'):
    """
    Normalize the audio files, given their paths and the decibels
    relative to full scale (dbfs). Default argument 'directory' can be overwritten.
    """
    start = datetime.now()
    Files = [os.path.abspath(f) for f in Files]
    if not os.path.exists(directory):  # Create the directory if it doesn't exist
        os.mkdir(directory)

    show_message = True
    for count, audio_file in enumerate(Files):
        try:
            audio_file = _valid_files(audio_file)
        except argparse.ArgumentTypeError as e:
            logger.error('%s , Skipping...', str(e))
            continue

        (dirname, filename) = os.path.split(audio_file)
        (shortname, extension) = os.path.splitext(filename)
        logger.info('(%s of %s) Processing file : "%s"', count + 1, len(Files), filename)

        # Extract metadata information
        try:
            tags = mutagen.File(audio_file, easy=True)
        except Exception as e:
            logger.error('%s , Skipping...', str(e))
            continue

        # Export the edited file
        try:
            song = AudioSegment.from_file(audio_file, format=extension[1:])
        except FileNotFoundError:  # Could not locate FFmpeg
            if show_message:
                logger.warning('WARNING: Could not locate FFmpeg, skipping non-wav files.')
                show_message = False
            continue
        change_in_dBFS = target_dbfs - song.dBFS
        dest_file = os.path.join(directory, filename)
        normalized_sound = song.apply_gain(change_in_dBFS)
        bitrate = '320k' if 'mp3' in extension else None
        normalized_sound.export(dest_file, format=extension[1:], bitrate=bitrate)
        # Copy metadata to new file (if the original has metadata)
        if tags:
            tags.save(dest_file)
    logger.info('Execution time : %s seconds', (datetime.now() - start).seconds)





if __name__ == '__main__':
    root = tk.Tk()
    gui = AudioNormalizerGUI(root)
    root.mainloop()
