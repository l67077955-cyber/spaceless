"""Background keyboard watcher: type words without spaces, get them spaced."""

import json
import queue
import sys
import threading
import time
from pathlib import Path

from . import winfocus
from .segment import split_run
from .tracker import Tracker

DEFAULT_CONFIG = {
    "min_length": 4,
    # words to treat as known: never split, and kept whole inside a longer run
    "my_words": ["github", "localhost", "hashtag", "wifi", "youtube", "chatgpt"],
    "exclude_apps": [
        "code.exe", "devenv.exe", "idea64.exe", "pycharm64.exe", "cursor.exe",
        "windowsterminal.exe", "cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe",
    ],
    "toggle_hotkey": "<ctrl>+<alt>+s",
}
CONFIG_NAME = "spaceless.json"


def load_config():
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
    path = base / CONFIG_NAME
    config = dict(DEFAULT_CONFIG)
    if path.exists():
        config.update(json.loads(path.read_text(encoding="utf-8")))
        print(f"config: {path}")
    return config


class App:
    def __init__(self, config):
        from pynput import keyboard

        self.keyboard = keyboard
        self.config = config
        words = frozenset(w.lower() for w in config["my_words"])
        self.tracker = Tracker(lambda run: split_run(run, words), config["min_length"])
        self.exclude = {a.lower() for a in config["exclude_apps"]}
        self.typer = keyboard.Controller()
        self.jobs = queue.Queue()
        self.busy = False
        self.enabled = True
        self.modifiers = set()
        mods = keyboard.Key
        self.modifier_keys = {
            mods.ctrl, mods.ctrl_l, mods.ctrl_r, mods.alt, mods.alt_l, mods.alt_r,
            mods.alt_gr, mods.cmd, mods.cmd_l, mods.cmd_r,
        }

    def on_press(self, key, injected=False):
        if injected or self.busy:
            return
        Key = self.keyboard.Key
        if key in self.modifier_keys:
            self.modifiers.add(key)
            self.tracker.reset()
            return
        if not self.enabled or self.modifiers:
            return
        if key == Key.space:
            ch = " "
        elif key == Key.backspace:
            self.tracker.backspace()
            return
        elif key in (Key.shift, Key.shift_l, Key.shift_r, Key.caps_lock):
            return
        else:
            ch = getattr(key, "char", None)
            if not ch:
                # Enter, Tab, arrows, Home... the caret may have moved
                self.tracker.reset()
                return
        job = self.tracker.char(ch)
        if job:
            self.jobs.put(job)

    def on_release(self, key, injected=False):
        self.modifiers.discard(key)

    def on_click(self, *args):
        self.tracker.reset()

    def toggle(self):
        self.enabled = not self.enabled
        self.tracker.reset()
        print("ON" if self.enabled else "PAUSED")

    def allowed_here(self):
        try:
            if winfocus.ime_in_native_mode():
                return False
            return winfocus.foreground_app() not in self.exclude
        except OSError:
            return True

    def worker(self):
        Key = self.keyboard.Key
        while True:
            backspaces, text = self.jobs.get()
            if not self.allowed_here():
                continue
            self.busy = True
            try:
                for _ in range(backspaces):
                    self.typer.tap(Key.backspace)
                self.typer.type(text)
                # let our own synthetic keys drain before listening again
                time.sleep(0.03)
            finally:
                self.busy = False
            print(f"-> {text.rstrip()}")

    def run(self):
        from pynput import mouse

        threading.Thread(target=self.worker, daemon=True).start()
        hotkeys = self.keyboard.GlobalHotKeys({self.config["toggle_hotkey"]: self.toggle})
        clicks = mouse.Listener(on_click=self.on_click)
        hotkeys.start()
        clicks.start()
        print(f"spaceless is running. {self.config['toggle_hotkey']} pauses/resumes, Ctrl+C quits.")
        with self.keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        sample = "iwanttoknowaninputmethod"
        print(sample, "->", split_run(sample))
        if sys.platform == "win32":
            # make sure the bundled keyboard backend and window probes load
            import pynput.keyboard  # noqa: F401
            import pynput.mouse  # noqa: F401

            print("focused app:", winfocus.foreground_app() or "?")
            print("ime native mode:", winfocus.ime_in_native_mode())
        return 0 if split_run(sample) == "i want to know an input method" else 1
    try:
        App(load_config()).run()
    except KeyboardInterrupt:
        pass
    return 0
