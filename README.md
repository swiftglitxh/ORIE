<div align="center">

<img width="1280" height="640" alt="image" src="https://github.com/user-attachments/assets/89c047ec-b306-4dc0-914e-b368ee0820b8" />


**`> a terminal file manager with a hacker shell, tab completion and a Pac-Man cleaning animation`**

![Python](https://img.shields.io/badge/python-3.8%2B-00ff41?style=for-the-badge&logo=python&logoColor=black&labelColor=0d1117)
![Version](https://img.shields.io/badge/version-1.7.0-00ff41?style=for-the-badge&labelColor=0d1117)
![License](https://img.shields.io/badge/license-MIT-00ff41?style=for-the-badge&labelColor=0d1117)
![Built with Rich](https://img.shields.io/badge/built%20with-rich-00ff41?style=for-the-badge&labelColor=0d1117)

</div>

---

<!-- Add a screenshot: save it as assets/screenshot.png and uncomment the line below
![screenshot](assets/screenshot.png)
-->

## `[ 00 ]` BOOT SEQUENCE

```text
[+] session opened as swift@orie
[+] tab completion online
[*] type help for commands

┌──[swift@orie]─[~/Documents]
└──╼ $ ls
```

**Orie** is a small interactive shell for browsing and tidying your files. It has a Kali/Parrot-style two-line prompt that shows your real username, familiar Linux commands, tab completion, a recolorable theme, and a Pac-Man that eats through your folder when you run `clean`.

---

## `[ 01 ]` FEATURES

```text
[+] hacker-style prompt with your username and current folder
[+] common Linux commands: ls, cd, cat, cp, mv, rm, mkdir, touch ...
[+] Linux-style flags: ls -a, rm -rf, mkdir -p, cp -r
[+] tab completion for commands, files and folders
[+] command history with the up/down arrows
[+] recolorable theme via --color or the color command
[+] verbose mode that logs everything a command does
[+] pac-man cleaning animation
[+] root detection: the prompt turns red and ends in # when run as root
[+] confirmation before every delete
```

---

## `[ 02 ]` INSTALL

```bash
git clone https://github.com/SwiftGlitxh/FileCleaner.git
cd FileCleaner
pip install rich
```

**Windows only**, for tab completion and command history:

```bash
pip install pyreadline3
```

Without it the program still runs, it just prints a notice that tab completion is off.

**Requirements:** Python 3.8+ and [Rich](https://github.com/Textualize/rich).

---

## `[ 03 ]` USAGE

```bash
python FileCleaner.py                       # default green theme
python FileCleaner.py -v                    # verbose mode
python FileCleaner.py --color=cyan          # change the theme color
python FileCleaner.py --color="#ff00aa"     # hex color (quote it)
python FileCleaner.py --color red -v        # combine flags
```

### Options

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | log what each command does with `[*]` lines |
| `--color COLOR` | theme color: a name, any Rich color, or a hex code (default `green`) |
| `-h`, `--help` | show the argument help |

### Colors

Friendly names: `green` `red` `blue` `cyan` `yellow` `magenta` `purple` `orange` `pink` `white`

Anything else is passed to Rich, so `spring_green1`, `#ff00aa` and `rgb(255,0,100)` all work. Hex colors need a truecolor terminal, and Rich falls back to the closest 256-color shade if yours doesn't have one.

You can also change the color while the program is running:

```text
┌──[swift@orie]─[~]
└──╼ $ color purple
[+] color changed to purple
```

---

## `[ 04 ]` COMMANDS

| Command | What it does | Example |
|---------|--------------|---------|
| `ls` | list files in a table with sizes | `ls`, `ls -a`, `ls ~/Downloads` |
| `cd` | change folder | `cd ..`, `cd ~`, `cd -` |
| `pwd` | show the current folder | `pwd` |
| `cat` | print a text file | `cat notes.txt` |
| `mkdir` | create a folder | `mkdir -p a/b/c` |
| `touch` | create an empty file | `touch todo.txt` |
| `cp` | copy a file or folder | `cp a.txt backup/` |
| `mv` | move or rename | `mv old.txt new.txt` |
| `rm` | delete, asks first | `rm file.txt`, `rm -rf folder` |
| `clean` | pac-man cleaning animation | `clean` |
| `color` | change the theme color | `color orange` |
| `clear` | clear the screen | `clear` |
| `help` | list all commands | `help` |
| `exit` / `quit` | leave the program | `exit` |

Names with spaces work if you quote them or escape them: `cd "My Folder"` or `cd My\ Folder`.

### Tab completion

```text
cl<TAB>        ->  clean
cd Doc<TAB>    ->  cd Documents/
cat no<TAB>    ->  cat notes.txt
color pu<TAB>  ->  color purple
```

`cd` only suggests folders, and hidden files only appear once you type a dot. Press Tab twice to list all matches.

---

## `[ 05 ]` THE PAC-MAN CLEANER

```text
ᗧ · · · · · · · · · ᗣ
```

Run `clean` and Pac-Man eats his way across the screen while the folder is processed. With `-v`, every file gets logged as it is eaten:

```text
[*] ate report.pdf  (48213 bytes)
[*] ate notes.txt  (1204 bytes)
[+] cleaned 12 items
```

> **Heads up:** right now `clean` is the animation plus a placeholder in the code where your own sorting or cleanup logic goes. It doesn't move or delete anything yet. See `clean()` in `FileCleaner.py`.

If `ᗧ` and `ᗣ` show up as empty boxes in your terminal font, swap them for `:yellow_circle:` and `:ghost:` in `pacman_frame()`.

---

## `[ 06 ]` SAFETY

```text
[!] rm deletes permanently. There is no recycle bin.
[!] rm always asks for confirmation and defaults to NO.
[!] folders need rm -r, even with confirmation.
[!] test on a throwaway folder before pointing it at anything important.
```

---

## `[ 07 ]` THEME REFERENCE

All colors live in one `THEME` dictionary at the top of the script, so restyling takes seconds:

```python
HOST = "orie"                 # text after the @ in the prompt

THEME = {
    "main": "bright_green",   # brackets, titles, borders  (set by --color)
    "dim": "dim bright_green",# secondary text             (derived from main)
    "path": "bold white",     # current folder in the prompt
    "root": "red",            # prompt color when running as root
    "error": "bold red",
    "warn": "yellow",
}
```

Message prefixes follow the usual convention:

```text
[+] success      [-] error      [*] info      [!] warning
```

---

## `[ 08 ]` ROADMAP

```text
[ ] sort files into folders by type (images, docs, archives ...)
[ ] find and remove duplicate files
[ ] dry-run mode that previews what clean would do
[ ] clean files older than N days
[ ] undo / trash instead of permanent delete
[ ] config file for saved theme and host name
```

---

## `[ 09 ]` TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: rich` | `pip install rich` |
| Tab does nothing on Windows | `pip install pyreadline3` |
| `㉿`, `╼`, `ᗧ` or `ᗣ` show as boxes | use a font with wider Unicode coverage (a Nerd Font works well) |
| Emoji misalign the table | emoji are two columns wide, so some terminals draw them badly |
| Windows path loses backslashes | already handled, but quote paths with spaces: `cd "C:\My Files"` |
| Colors look wrong | use a modern terminal such as Windows Terminal, iTerm2, GNOME Terminal or Konsole |

---

## `[ 10 ]` LICENSE

MIT. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

```
[ built by SwiftGlitxh ]   [ powered by rich ]   [ stay curious ]
```

</div>
