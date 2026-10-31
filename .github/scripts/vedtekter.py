#!/usr/bin/env python3
"""Archive, render and check the statutes in "styrende dokumenter/vedtekter".

    vedtekter.py build [--dry-run]   archive the current PDF and render a new one where the LaTeX source has changed
    vedtekter.py check               check that the metadata of the current PDFs matches their file names

Requires pikepdf, and latexmk with pdflatex for rendering.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pikepdf

ROOT = Path(__file__).resolve().parents[2]
VEDTEKTER = ROOT / "styrende dokumenter" / "vedtekter"
GJELDENDE = VEDTEKTER / "gjeldende"
KILDE = VEDTEKTER / "kilde"
UTGAATTE = VEDTEKTER / "utgåtte"

AUTHOR = "UiO Gaming"
OSLO = ZoneInfo("Europe/Oslo")


@dataclass(frozen=True)
class Language:
    code: str
    name: str
    date_format: str
    front_page_date: str
    front_page_date_format: str

    @property
    def source(self):
        return KILDE / self.code

    @property
    def archive(self):
        return UTGAATTE / self.code

    def format(self, d):
        return d.strftime(self.date_format)

    def parse(self, s):
        return datetime.strptime(s, self.date_format).date()

    def current_name(self, start):
        return f"{self.name} ({self.format(start)} - ).pdf"

    def archived_name(self, number, start, end):
        return f"{number:02d} - {self.name} ({self.format(start)} - {self.format(end)}).pdf"

    def current(self):
        """The current PDF and its start date."""
        pattern = re.compile(rf"{re.escape(self.name)} \((.+) - \)\.pdf")
        matches = [(p, m) for p in GJELDENDE.glob("*.pdf") if (m := pattern.fullmatch(p.name))]
        if len(matches) != 1:
            sys.exit(f"Expected exactly one current PDF for '{self.name}' in {GJELDENDE}, found {len(matches)}")
        path, match = matches[0]
        return path, self.parse(match.group(1))

    def archived(self):
        """Number and start date of every archived PDF."""
        pattern = re.compile(rf"(\d+) - {re.escape(self.name)} \((.+) - (.+)\)\.pdf")
        return {
            int(m.group(1)): self.parse(m.group(2))
            for p in self.archive.glob("*.pdf")
            if (m := pattern.fullmatch(p.name))
        }

    def source_date(self):
        """The date on the front page of the LaTeX source."""
        text = (self.source / "front_page.tex").read_text(encoding="utf-8")
        match = re.search(self.front_page_date, text)
        if not match:
            sys.exit(f"Could not find the date in {self.source / 'front_page.tex'}")
        return datetime.strptime(match.group(1), self.front_page_date_format).date()


NORWEGIAN = Language(
    code="no",
    name="Vedtekter UiO Gaming",
    date_format="%d.%m.%Y",
    front_page_date=r"Sist revidert:\s*\\\\\s*(\d{2}\.\d{2}\.\d{4})",
    front_page_date_format="%d.%m.%Y",
)
ENGLISH = Language(
    code="en",
    name="Statutes UiO Gaming",
    date_format="%Y-%m-%d",
    front_page_date=r"Last changed:\s*\\\\\s*([A-Z][a-z]+ \d{1,2}, \d{4})",
    front_page_date_format="%B %d, %Y",
)


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=check)


def relative(path):
    return str(path.relative_to(ROOT))


def source_changed(language, current):
    """Whether the LaTeX source has changed since the current PDF was last committed."""
    last = git("log", "-1", "--format=%H", "--", relative(current)).stdout.strip()
    if not last:
        return True
    git("update-index", "-q", "--refresh", check=False)
    return git("diff", "--quiet", last, "--", relative(language.source), check=False).returncode != 0


def midnight(d):
    return datetime(d.year, d.month, d.day, tzinfo=OSLO)


def pdf_date(d):
    dt = midnight(d)
    minutes = int(dt.utcoffset().total_seconds()) // 60
    sign = "+" if minutes >= 0 else "-"
    hours, minutes = divmod(abs(minutes), 60)
    return f"D:{dt:%Y%m%d%H%M%S}{sign}{hours:02d}'{minutes:02d}'"


def parse_pdf_date(s):
    match = re.fullmatch(r"D:(\d{14})(?:(Z)|([+-])(\d{2})'(\d{2})'?)?", s)
    if not match:
        return None
    dt = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    if match.group(3):
        offset = timedelta(hours=int(match.group(4)), minutes=int(match.group(5)))
        dt = dt.replace(tzinfo=timezone(offset if match.group(3) == "+" else -offset))
    else:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(OSLO).date()


def title(path):
    return re.sub(r"^\d+ - ", "", path.stem)


def write_metadata(source, target, start):
    """Replace all metadata of the PDF with the standard metadata for the statutes."""
    with pikepdf.open(source, allow_overwriting_input=True) as pdf:
        if "/Metadata" in pdf.Root:
            del pdf.Root.Metadata
        pdf.docinfo = pdf.make_indirect(
            pikepdf.Dictionary(
                Title=pikepdf.String(title(target)),
                Subject=pikepdf.String(""),
                Keywords=pikepdf.String(""),
                Author=pikepdf.String(AUTHOR),
                Creator=pikepdf.String(""),
                Producer=pikepdf.String(""),
                CreationDate=pikepdf.String(pdf_date(start)),
                ModDate=pikepdf.String(pdf_date(start)),
                Trapped=pikepdf.Name("/False"),
            )
        )
        pdf.save(target, deterministic_id=True)


def render(language, start, target):
    with tempfile.TemporaryDirectory() as out:
        env = dict(os.environ, SOURCE_DATE_EPOCH=str(int(midnight(start).timestamp())), FORCE_SOURCE_DATE="1")
        result = subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", f"-outdir={out}", "main.tex"],
            cwd=language.source,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout, result.stderr, sep="\n", file=sys.stderr)
            sys.exit(f"{language.code}: LaTeX failed")
        write_metadata(Path(out) / "main.pdf", target, start)


def build_language(language, dry_run, norwegian):
    """Archive and render one language.

    `norwegian` maps the number of every Norwegian version to its start date, with the current version as None.
    It is updated with what was done to the Norwegian statutes. Returns a description of what was done, or None.
    """
    current, current_start = language.current()
    if not source_changed(language, current):
        print(f"{language.code}: the source has not changed since {current.name} was committed")
        return None

    new_start = language.source_date()
    if new_start < current_start:
        sys.exit(f"{language.code}: the front page date {new_start} is older than the current statutes ({current_start})")
    if language is not NORWEGIAN and new_start not in norwegian.values():
        sys.exit(f"{language.code}: the front page date {new_start} does not match any Norwegian version")

    target = GJELDENDE / language.current_name(new_start)
    if new_start == current_start:
        if not dry_run:
            render(language, new_start, target)
        return f"Re-rendered `{target.name}` without a new date"

    if language is NORWEGIAN:
        number = max((n for n in norwegian if n is not None), default=0) + 1
        norwegian[number] = current_start
        norwegian[None] = new_start
    else:
        number = next((n for n, s in norwegian.items() if n is not None and s == current_start), None)
        if number is None:
            sys.exit(f"{language.code}: no archived Norwegian version starts at {current_start}")
    archived = language.archive / language.archived_name(number, current_start, new_start)
    if not dry_run:
        with tempfile.TemporaryDirectory() as out:
            rendered = Path(out) / target.name
            render(language, new_start, rendered)
            git("mv", relative(current), relative(archived))
            write_metadata(archived, archived, current_start)
            shutil.move(rendered, target)
    return f"Archived `{current.name}` as `{archived.name}` and rendered `{target.name}`"


def build(dry_run):
    norwegian = {**NORWEGIAN.archived(), None: NORWEGIAN.current()[1]}
    summaries = []
    for language in (NORWEGIAN, ENGLISH):
        summary = build_language(language, dry_run, norwegian)
        if summary:
            print(f"{language.code}: {'(dry run) ' if dry_run else ''}{summary}")
            summaries.append(summary)

    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write("summary<<EOF\n" + "\n".join(f"- {s}" for s in summaries) + "\nEOF\n")


def check():
    errors = []
    for language in (NORWEGIAN, ENGLISH):
        path, start = language.current()
        with pikepdf.open(path) as pdf:
            info = pdf.docinfo
            if str(info.get("/Title", "")) != title(path):
                errors.append(f"{path.name}: the title is '{info.get('/Title')}'")
            if str(info.get("/Author", "")) != AUTHOR:
                errors.append(f"{path.name}: the author is '{info.get('/Author')}'")
            for key in ("/Creator", "/Producer"):
                if str(info.get(key, "")):
                    errors.append(f"{path.name}: {key[1:]} is '{info[key]}'")
            for key in ("/CreationDate", "/ModDate"):
                if parse_pdf_date(str(info.get(key, ""))) != start:
                    errors.append(f"{path.name}: {key[1:]} is '{info.get(key)}', expected {start}")
            if "/Metadata" in pdf.Root:
                errors.append(f"{path.name}: has XMP metadata")
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        sys.exit(1)
    print("The metadata of the current statutes is correct")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build", help="archive and render the statutes where the source has changed")
    build_parser.add_argument("--dry-run", action="store_true", help="print what would be done without doing it")
    commands.add_parser("check", help="check the metadata of the current statutes")
    args = parser.parse_args()

    if args.command == "build":
        build(args.dry_run)
    else:
        check()


if __name__ == "__main__":
    main()
