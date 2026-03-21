"""Co-change analysis — find files that historically change together."""
from collections import defaultdict
import git


def get_cochange_map(repo_path: str, max_commits: int = 200) -> dict[str, dict[str, float]]:
    """Return {file: {related_file: score}} for the whole repo."""
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        return {}

    # {file: set of commit hashes}
    file_commits: dict[str, set] = defaultdict(set)

    try:
        log = repo.git.log('--name-only', f'--max-count={max_commits}', '--format=COMMIT:%H')
    except git.GitCommandError:
        return {}

    current_commit = None
    for line in log.splitlines():
        if line.startswith('COMMIT:'):
            current_commit = line[7:]
        elif line.strip() and current_commit:
            file_commits[line.strip()].add(current_commit)

    # Build co-change scores
    files = list(file_commits.keys())
    cochange: dict[str, dict[str, float]] = defaultdict(dict)

    for i, file_a in enumerate(files):
        for file_b in files[i+1:]:
            shared = len(file_commits[file_a] & file_commits[file_b])
            if shared == 0:
                continue
            score = shared / min(len(file_commits[file_a]), len(file_commits[file_b]))
            if score >= 0.2:
                cochange[file_a][file_b] = round(score, 2)
                cochange[file_b][file_a] = round(score, 2)

    return dict(cochange)


def get_related_files(cochange_map: dict, filepath: str, top_n: int = 5) -> list[tuple[str, float]]:
    """Return top N related files for a given file, sorted by score desc."""
    related = cochange_map.get(filepath, {})
    return sorted(related.items(), key=lambda x: x[1], reverse=True)[:top_n]
