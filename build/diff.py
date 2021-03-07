from subprocess import run
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


REF_CMD = 'git log --diff-filter=A --format=format:"%H %aI" -- {file_path}'
SHOW_CMD = 'git show {ref}:{file_path}'


@dataclass
class Diff:
    file_path: Path
    _ref: str = None
    _author_date: str = None
    _text: str = None

    def _retrieve_file_added_commit_ref_date(self):
        if not (self._ref and self._author_date):
            cmd = REF_CMD.format(file_path=self.file_path)
            cp = run(cmd, shell=True, capture_output=True, text=True, check=True)
            self._ref, author_date = cp.stdout.split(' ', 1)
            self._author_date = datetime.fromisoformat(author_date).date().isoformat()

        return self._ref, self._author_date

    def _retrieve_text_from_ref(self, ref):
        if not self._text:
            cmd = SHOW_CMD.format(ref=ref, file_path=self.file_path)
            cp = run(cmd, shell=True, capture_output=True, text=True, check=True)
            self._text = cp.stdout

        return self._text

    def get_first_version_text(self):
        ref, _ = self._retrieve_file_added_commit_ref_date()
        text = self._retrieve_text_from_ref(ref)
        return text

    def get_update_date(self):
        _, date = self._retrieve_file_added_commit_ref_date()
        return date


if __name__ == '__main__':
    import sys
    file_path = Path(sys.argv[1])
    diff = Diff(file_path)
    text = diff.get_first_version_text()
    date = diff.get_update_date()
    print(text, date, sep='\n')