#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ╔══════════════════════════════════════════════╗
# ║ SCRIPT  : Orie.py                            ║
# ║ AUTHOR  : SwiftGlitxh                        ║
# ║ VERSION : 1.7.0                              ║
# ║ LICENSE : MIT                                ║
# ║ ABOUT   : File organizer                     ║
# ╚══════════════════════════════════════════════╝

import argparse
import getpass
import os
import shlex
import shutil
import time
from pathlib import Path

from rich import box
from rich.color import Color, ColorParseError
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

try:
	import readline  # Linux/macOS built in; on Windows: pip install pyreadline3
except ImportError:
	readline = None

console = Console()

# ---------- theme ----------
HOST = "orie"  # shown after the @ in the prompt

THEME = {
	"main": "bright_green",       # brackets, titles, borders (set by --color)
	"dim": "dim bright_green",    # secondary text (derived from main)
	"path": "bold white",         # current folder in the prompt
	"root": "red",                # prompt color when running as root
	"error": "bold red",
	"warn": "yellow",
}

# friendly names -> Rich colors (anything else is passed to Rich as-is)
COLOR_ALIASES = {
	"green": "bright_green",
	"red": "bright_red",
	"blue": "bright_blue",
	"cyan": "bright_cyan",
	"yellow": "bright_yellow",
	"magenta": "bright_magenta",
	"purple": "medium_purple1",
	"orange": "orange1",
	"pink": "hot_pink",
	"white": "bright_white",
}


def apply_color(value):
	"""Set the theme color. Returns True if the color was valid."""
	value = value.strip().lower()
	value = COLOR_ALIASES.get(value, value)

	try:
		Color.parse(value)
	except ColorParseError:
		return False

	THEME["main"] = value
	THEME["dim"] = f"dim {value}"
	return True


def get_username():
	try:
		return getpass.getuser()
	except Exception:
		return "user"


def is_root():
	return hasattr(os, "geteuid") and os.geteuid() == 0


class Cleaner:
	def __init__(self, verbose=False):
		self.verbose = verbose
		self.user = get_username()
		self.previous = Path.cwd()  # for "cd -"
		self.matches = []

		self.commands = {
			"ls": (self.ls, "list files            ls [-a] [path]"),
			"cd": (self.cd, "change folder         cd <path> | cd .. | cd ~ | cd -"),
			"pwd": (self.pwd, "show current folder   pwd"),
			"cat": (self.cat, "show a text file      cat <file>"),
			"mkdir": (self.mkdir, "make a folder         mkdir [-p] <name>"),
			"touch": (self.touch, "make an empty file    touch <name>"),
			"cp": (self.cp, "copy                  cp [-r] <source> <dest>"),
			"mv": (self.mv, "move or rename        mv <source> <dest>"),
			"rm": (self.rm, "delete (asks first)   rm <name> | rm -r <folder>"),
			"clean": (self.clean, "pac-man cleaning      clean"),
			"color": (self.color, "change theme color    color <name | #hex>"),
			"clear": (self.clear, "clear the screen      clear"),
			"help": (self.help, "show this list        help"),
		}

	# ---------- tab completion ----------

	def setup_completion(self):
		if readline is None:
			return

		readline.set_completer_delims(" \t\n")  # only split words on whitespace
		readline.set_completer(self.complete)

		# macOS ships libedit, which uses a different bind syntax
		if "libedit" in (readline.__doc__ or ""):
			readline.parse_and_bind("bind ^I rl_complete")
		else:
			readline.parse_and_bind("tab: complete")

	def complete(self, text, state):
		if state == 0:
			buffer = readline.get_line_buffer()
			before = buffer[:readline.get_begidx()].split()

			if not before:
				names = list(self.commands) + ["exit", "quit"]
				self.matches = [n + " " for n in sorted(names) if n.startswith(text)]
			elif before[0].lower() == "color":
				self.matches = [c for c in sorted(COLOR_ALIASES) if c.startswith(text)]
			else:
				self.matches = self.path_matches(before[0].lower(), text)

		return self.matches[state] if state < len(self.matches) else None

	def path_matches(self, command, text):
		raw = text.replace("\\ ", " ")  # undo space escaping

		if raw == "~":
			return ["~/"]

		cut = max(raw.rfind("/"), raw.rfind(os.sep))
		prefix, partial = raw[:cut + 1], raw[cut + 1:]
		directory = os.path.expanduser(prefix) or "."

		try:
			entries = sorted(os.listdir(directory))
		except OSError:
			return []

		dirs_only = command == "cd"
		matches = []

		for name in entries:
			if not name.startswith(partial):
				continue
			if name.startswith(".") and not partial.startswith("."):
				continue  # hide dotfiles unless you type a dot

			is_dir = os.path.isdir(os.path.join(directory, name))
			if dirs_only and not is_dir:
				continue

			match = prefix + name
			if os.name != "nt":
				match = match.replace(" ", "\\ ")
			if is_dir:
				match += "/"
			matches.append(match)

		return matches

	# ---------- helpers ----------

	def error(self, message):
		console.print(Text.assemble(("[-] ", THEME["error"]), str(message)))

	def good(self, message):
		console.print(Text.assemble(("[+] ", f"bold {THEME['main']}"), str(message)))

	def info(self, message):
		if self.verbose:
			console.print(Text.assemble(("[*] ", THEME["dim"]), (message, "dim")))

	def make_table(self, title, **kwargs):
		return Table(
			title=Text(str(title), style=f"bold {THEME['main']}"),
			box=box.SQUARE,
			border_style=THEME["dim"],
			header_style=f"bold {THEME['main']}",
			**kwargs,
		)

	def resolve(self, raw):
		return Path(raw).expanduser()

	def split_flags(self, args):
		"""Split ['-la', 'folder'] into ('la', ['folder'])."""
		flags = "".join(a[1:] for a in args if a.startswith("-") and len(a) > 1)
		names = [a for a in args if not (a.startswith("-") and len(a) > 1)]
		return flags, names

	def short_cwd(self):
		cwd = str(Path.cwd())
		home = str(Path.home())
		if cwd == home:
			return "~"
		if cwd.startswith(home + os.sep):
			return "~" + cwd[len(home):]
		return cwd

	def parse(self, raw):
		"""Split a command line into parts, keeping Windows backslashes intact."""
		if os.name == "nt":
			return [p.strip("\"'") for p in shlex.split(raw, posix=False)]
		return shlex.split(raw)

	# ---------- prompt ----------

	def show_prompt_header(self):
		color = THEME["root"] if is_root() else THEME["main"]

		line = Text()
		line.append("┌──[", style=color)
		line.append(self.user, style=f"bold {color}")
		line.append("@", style=THEME["dim"])
		line.append(HOST, style=f"bold {color}")
		line.append("]─[", style=color)
		line.append(self.short_cwd(), style=THEME["path"])
		line.append("]", style=color)
		console.print(line)

		symbol = "# " if is_root() else "$ "
		return Text.assemble(("└──╼ ", color), (symbol, f"bold {color}"))

	# ---------- commands ----------

	def ls(self, args):
		flags, names = self.split_flags(args)
		show_hidden = "a" in flags
		target = self.resolve(names[0]) if names else Path.cwd()

		if not target.exists():
			return self.error(f"{target} does not exist")
		if target.is_file():
			console.print(Text(target.name, style=THEME["main"]))
			return

		table = self.make_table(target.resolve())
		table.add_column("Name", style=THEME["main"])
		table.add_column("Type", style=THEME["dim"])
		table.add_column("Size", justify="right", style=THEME["dim"])

		for item in sorted(target.iterdir()):
			if item.name.startswith(".") and not show_hidden:
				continue
			if item.is_dir():
				kind, size = ":file_folder: Folder", ""
			else:
				kind, size = ":page_facing_up: File", f"{item.stat().st_size:,} B"
			table.add_row(Text(item.name), kind, size)

		console.print(table)

	def cd(self, args):
		flags, names = self.split_flags(args)

		# "cd -" would be treated as a flag, so check for it first
		if args and args[0] == "-":
			target = self.previous
		elif not names or names[0] == "~":
			target = Path.home()
		else:
			target = self.resolve(names[0])

		if not target.is_dir():
			return self.error(f"{target} is not a folder")

		self.previous = Path.cwd()
		os.chdir(target)
		self.info(f"now in {Path.cwd()}")

	def pwd(self, args):
		console.print(Text(str(Path.cwd()), style=THEME["main"]))

	def cat(self, args):
		flags, names = self.split_flags(args)
		if not names:
			return self.error("usage: cat <file>")

		for name in names:
			target = self.resolve(name)
			if not target.is_file():
				self.error(f"{target} is not a file")
				continue

			try:
				content = target.read_text(encoding="utf-8")
			except UnicodeDecodeError:
				self.error(f"{target} looks like a binary file")
				continue

			console.print(Text(content, style=THEME["main"]))

	def mkdir(self, args):
		flags, names = self.split_flags(args)
		if not names:
			return self.error("usage: mkdir [-p] <name>")

		for name in names:
			self.resolve(name).mkdir(parents=True, exist_ok=True)
			self.info(f"created folder {name}")

	def touch(self, args):
		flags, names = self.split_flags(args)
		if not names:
			return self.error("usage: touch <name>")

		for name in names:
			self.resolve(name).touch()
			self.info(f"touched {name}")

	def cp(self, args):
		flags, names = self.split_flags(args)
		if len(names) != 2:
			return self.error("usage: cp [-r] <source> <dest>")

		source, dest = self.resolve(names[0]), self.resolve(names[1])
		if not source.exists():
			return self.error(f"{source} does not exist")

		if source.is_dir():
			target = dest / source.name if dest.is_dir() else dest
			shutil.copytree(source, target)
		else:
			shutil.copy2(source, dest)
		self.info(f"copied {source} -> {dest}")

	def mv(self, args):
		flags, names = self.split_flags(args)
		if len(names) != 2:
			return self.error("usage: mv <source> <dest>")

		source, dest = self.resolve(names[0]), self.resolve(names[1])
		if not source.exists():
			return self.error(f"{source} does not exist")

		shutil.move(str(source), str(dest))
		self.info(f"moved {source} -> {dest}")

	def rm(self, args):
		flags, names = self.split_flags(args)
		recursive = "r" in flags or "R" in flags

		if not names:
			return self.error("usage: rm <name> | rm -r <folder>")

		for name in names:
			target = self.resolve(name)
			if not target.exists():
				self.error(f"{target} does not exist")
				continue
			if target.is_dir() and not recursive:
				self.error(f"{target} is a folder, use rm -r")
				continue

			question = Text.assemble("🗑️  Delete ", (str(target), "bold red"), "?")
			if not Confirm.ask(question, default=False):
				console.print(Text("[!] Skipped", style=THEME["warn"]))
				continue

			if target.is_dir():
				shutil.rmtree(target)
			else:
				target.unlink()
			self.info(f"deleted {target}")

	def color(self, args):
		if not args:
			console.print(Text.assemble(("Current color: ", THEME["dim"]), (THEME["main"].replace("dim ", ""), f"bold {THEME['main']}")))
			console.print(Text("Try: " + ", ".join(sorted(COLOR_ALIASES)) + ", or a hex like #ff00aa", style=THEME["dim"]))
			return

		if apply_color(args[0]):
			self.good(f"color changed to {args[0]}")
		else:
			self.error(f"'{args[0]}' is not a valid color")

	def clear(self, args):
		console.clear()

	def help(self, args):
		table = self.make_table("Commands", show_header=False)
		for name, (_, description) in self.commands.items():
			table.add_row(Text(name, style=f"bold {THEME['main']}"), Text(description, style=THEME["dim"]))
		table.add_row(
			Text("exit", style=f"bold {THEME['main']}"),
			Text("quit the program      exit | quit", style=THEME["dim"]),
		)
		console.print(table)

	# ---------- pac-man cleaning ----------

	def pacman_frame(self, pos, total, step):
		pac = "ᗧ" if step % 2 == 0 else "●"  # mouth open / closed
		return Text.assemble(
			" " * (pos * 2),
			(pac, "bold yellow"),
			" ",
			("· " * (total - pos - 1), THEME["dim"]),
			("ᗣ", "bold red"),
		)

	def clean(self, args):
		self.ls([])

		items = sorted(Path.cwd().iterdir())
		if not items:
			console.print(Text("[!] Nothing to clean.", style=THEME["warn"]))
			return

		total = min(len(items), 30)

		with Live(console=console, refresh_per_second=20) as live:
			for step in range(total):
				live.update(self.pacman_frame(step, total, step))

				start = step * len(items) // total
				end = (step + 1) * len(items) // total
				for item in items[start:end]:
					# real cleaning logic would go here (move, sort, delete...)
					if self.verbose:
						size = item.stat().st_size if item.is_file() else 0
						live.console.print(Text.assemble(
							("[*] ate ", "yellow"),
							(item.name, "bold"),
							(f"  ({size} bytes)", "dim"),
						))

				time.sleep(0.15)

		self.good(f"cleaned {len(items)} items")

	# ---------- main loop ----------

	def chat(self):
		self.setup_completion()

		console.print(Panel.fit(
			"\n:robot: hello\n:broom: I can clean your files\n:file_folder: Let's get to cleaning!\n:question: Type help for commands",
			title="💾 ORIE :: FILE CLEANER\n",
			border_style=THEME["main"],
			style=THEME["main"],
			padding=(1, 4),
		))

		self.good(f"session opened as {self.user}@{HOST}")
		if self.verbose:
			self.good("verbose mode on")
		if readline is None:
			console.print(Text("[!] Tab completion off. Windows users: pip install pyreadline3", style=THEME["warn"]))

		while True:
			prompt = self.show_prompt_header()

			try:
				raw = console.input(prompt)
			except (EOFError, KeyboardInterrupt):
				console.print("\n:wave: Bye!")
				break

			try:
				parts = self.parse(raw)
			except ValueError as e:
				self.error(e)
				continue

			if not parts:
				continue

			name, args = parts[0].lower(), parts[1:]

			if name in ("exit", "quit"):
				console.print(":wave: Bye!")
				break

			if name not in self.commands:
				self.error(f"unknown command: {name}")
				continue

			try:
				self.commands[name][0](args)
			except (OSError, shutil.Error) as e:
				self.error(e)


def main():
	parser = argparse.ArgumentParser(description="Orie the organizer")
	parser.add_argument("-v", "--verbose", action="store_true", help="show what each command does")
	parser.add_argument(
		"--color",
		default="green",
		metavar="COLOR",
		help="theme color: a name (red, cyan, orange, pink...) or hex like #ff00aa (default: green)",
	)
	args = parser.parse_args()

	if not apply_color(args.color):
		parser.error(f"invalid color: {args.color}")

	Cleaner(verbose=args.verbose).chat()


if __name__ == "__main__":
	main()
