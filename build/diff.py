from subprocess import run
from pathlib import Path


REF_CMD = 'git log --diff-filter=A --format=format:%H -- {file_path}'
SHOW_CMD = 'git show {ref}:{file_path}'


def get_file_added_commit_ref(file_path: Path):
    cmd = REF_CMD.format(file_path=file_path)
    cp = run(cmd, shell=True, capture_output=True, text=True, check=True)
    return cp.stdout


def retrieve_text_from_ref(ref, file_path: Path):
    cmd = SHOW_CMD.format(ref=ref, file_path=file_path)
    cp = run(cmd, shell=True, capture_output=True, text=True, check=True)
    text = cp.stdout
    return text


def retrieve_first_version_text(file_path: Path):
    ref = get_file_added_commit_ref(file_path)
    text = retrieve_text_from_ref(ref, file_path)
    return text


if __name__ == '__main__':
    import sys
    file_path = Path(sys.argv[1])
    text = retrieve_first_version_text(file_path)
    print(text)