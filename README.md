# spaceless

Type English without pressing space. spaceless puts the spaces back.

```
you type:   iwanttoknowaninputmethod␣
you get:    i want to know an input method␣
```

It runs in the background on Windows and works in any app: chat, browser, Word.
When you press **space** or punctuation (`. , ! ? ; :`), it looks at the letters
you just typed. If they are several words run together, it erases them and types
them again with spaces.

## Install

**Windows exe:** download `spaceless.exe` from
[Releases](../../releases/latest) and double-click it. A console window shows
what it rewrites; close the window to quit.

> The exe is not code-signed, so Windows SmartScreen may warn you the first
> time ("More info" → "Run anyway"). Some antivirus tools flag any program that
> reads the keyboard; the full source is here if you prefer to run it yourself.

**From source (Python 3.9+):**

```
pip install git+https://github.com/l67077955-cyber/spaceless
spaceless
```

To start it with Windows, put a shortcut to `spaceless.exe` in the Startup
folder (Win+R → `shell:startup`).

## Usage

- Type a few words with no spaces, then press space or punctuation.
- **Ctrl+Alt+S** pauses or resumes.
- Single words are never touched: `hello`, `nowhere`, `therapist` stay as typed.
- Typos inside a sentence stay where they are, but the rest still gets split:
  `cnayouinventaappandpostonmygithb` → `cna you invent a app and post on my githb`.
- A run that is mostly unknown letters is left alone.
- `camelCase` runs are left alone (they look like code).

It switches itself off:

- in terminals and code editors (see `exclude_apps` below);
- while a Chinese/Japanese/Korean IME is in its native mode. Switch the IME to
  English mode (usually Shift) and spaceless works again.

## Settings

Put a `spaceless.json` next to `spaceless.exe` (or in the folder you run
`spaceless` from). Every key is optional:

```json
{
  "min_length": 4,
  "my_words": ["github", "localhost", "kubernetes"],
  "exclude_apps": ["code.exe", "windowsterminal.exe", "cmd.exe"],
  "toggle_hotkey": "<ctrl>+<alt>+s"
}
```

| key | meaning |
|---|---|
| `min_length` | shortest run of letters it will try to split |
| `my_words` | words it does not know or splits wrongly (`github` → `git hub`). They are never split and are kept whole inside longer runs. This replaces the default list. |
| `exclude_apps` | exe names where spaceless does nothing. This replaces the default list. |
| `toggle_hotkey` | pause/resume hotkey, in [pynput format](https://pynput.readthedocs.io/en/latest/keyboard.html#global-hotkeys) |

## How it works

- A keyboard hook ([pynput](https://github.com/moses-palmer/pynput)) remembers
  the letters typed since the last space, punctuation, Enter, arrow key or mouse
  click.
- On space or punctuation the run is split with a dynamic-programming search
  over the 30,000 most common English words, ranked by frequency (word list from
  [wordninja](https://github.com/keredson/wordninja)). Long runs may keep a few
  unknown chunks such as names and typos, as long as at least 70% of the letters
  are real words.
- If the split has two or more words, spaceless sends backspaces and types the
  spaced text.

## Limits

- Enter does not trigger a split (the message would already be sent). End with
  space or punctuation first.
- It can only see what you type, so after clicking somewhere or using the arrow
  keys it starts fresh.
- Splits are frequency guesses and are sometimes wrong (`whatsupbro` →
  `what sup bro`). Add words to `my_words` to fix the ones you hit.
- Apostrophes are not added: `idontknow` → `i dont know`.

## Development

```
pip install -e . pytest
pytest
python -m spaceless --selftest
```

The `build` workflow tests on Windows, builds `spaceless.exe` with PyInstaller,
and attaches it to a GitHub release when a `v*` tag is pushed.

## License

MIT
