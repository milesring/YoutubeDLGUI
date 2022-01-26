from __future__ import unicode_literals
from re import L
from tkinter.constants import HORIZONTAL
import yt_dlp
import tkinter as tk
from tkinter import ttk
import threading
import os.path

class YTLog:
    def debug(self, msg):
        # For compatability with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

class YTDL(threading.Thread):
    url: str
    ydl_opts: dict[str, any]
    dl_complete: bool
    filename: str

    def check_conv_complete(self):
        if not self.dl_complete:
            return False
        file_split = os.path.splitext(self.filename)
        new_file = ".".join((file_split[0], "mp3"))
        if os.path.exists(new_file) and not os.path.exists(self.filename):
            print("Conversion complete.")
            return True
        return False

    def event_hook(self, d):
        if d['status'] == 'finished':
            self.filename = d['filename']
            self.dl_complete = True
            print("Done downloading, now converting...")

    def download_youtube(self):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download(self.url)

    def set_ydl_opts(self):
        return {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'writethumbnail': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
                },
                {
                'key': 'EmbedThumbnail',
                }
            ],
            'logger': YTLog(),
            'progress_hooks': [self.event_hook]
        }

    def get_status(self):
        pass
    
    def run(self):
        self.dl_complete = False
        self.download_youtube()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YoutubeDL")
        self.geometry("640x480")
        self.resizable(0,0)
        self.create_window()
    
    def create_window(self):
        self.label = tk.Label(text="Youtube URLS(seperate with commas)")
        self.text_box = tk.Text()
        self.label.pack()
        self.text_box.pack()
        self.button = tk.Button(text ="Download", command = self.handle_download)
        self.button.pack()
        self.progress = ttk.Progressbar(self, orient=HORIZONTAL,length=100,mode='determinate')
        self.progress.pack()

    def handle_download(self):
        urls = self.text_box.get("1.0", "end")
        
        seperatedURLs = [x.strip() for x in urls.split(",") if x != ""]

        self.button["state"] = tk.DISABLED
        self.progress["value"] = 0
        threads = []
        for url in seperatedURLs:
            ytdl = YTDL()
            ytdl.url = url
            ytdl.ydl_opts = ytdl.set_ydl_opts()
            threads.append(ytdl)
        [t.start() for t in threads]
        self.schedule_check(threads)
        
    def schedule_check(self, threads):
        self.after(1000, self.check_if_done, threads)

    def check_if_done(self, threads: list[YTDL]):
        # If the thread has finished, re-enable the button and show a message.
        complete = True
        progress_value = 0
        new_check_scheduled = False
        for t in threads:
            conversion_complete = t.check_conv_complete()
            if t.dl_complete:
                progress_value += 100/len(threads)/2
            if conversion_complete:
                progress_value += 100/len(threads)/2

            if not conversion_complete and not new_check_scheduled:
                complete = False
                new_check_scheduled = True
                self.schedule_check(threads)
        self.progress['value'] = progress_value
                
        if complete:
            self.progress["value"] = 100
            self.label["text"] = f"{len(threads)} File(s) successfully downloaded!"
            self.button["state"] = tk.NORMAL 

app = App()
app.mainloop()