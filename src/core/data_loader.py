"""Doc file bai toan MKP theo dinh dang OR-Library.
Ho tro 2 dinh dang:
- mknap1 / mknapcb*: K, (n m opt, profits, weights, caps) * K
- mknap2 (van hoc): cac block 'problem TEN.DAT' voi thu tu
  m n, profits, caps, weights, opt (co comment // va dau +)
"""
import re
from pathlib import Path
import numpy as np
from src.core.config import DATA_DIR, REFERENCE_FILE
from src.core.model import MKPProblem

# Block van hoc trong mknap2: dong 'problem TEN.DAT'
_LITERATURE_BLOCK = re.compile(r"\n\s*problem\s+([A-Za-z0-9_.]+)\s*\n")
# Dòng z_ref trong mkcbres: '5.100-00    24381'
_REFERENCE_LINE = re.compile(r"^(\d+)\.(\d+)-(\d+)\s+(\d+)")

_problem_cache: dict = {}
_reference_cache: dict = None

def _load_references() -> dict:
    """Doc bang z_ref tu mkcbres.txt (chi table Best Feasible, khong doc LP)."""
    path = DATA_DIR / REFERENCE_FILE
    if not path.exists():
        return {}
    head = path.read_text().split("LP optimal")[0]
    refs = {}
    for line in head.splitlines():
        match = _REFERENCE_LINE.match(line.strip())
        if match:
            m, n, index, value = map(int, match.groups())
            refs[(m, n, index)] = float(value)
    return refs

def _references() -> dict:
    global _reference_cache
    if _reference_cache is None:
        _reference_cache = _load_references()
    return _reference_cache

def _attach_reference(problem: MKPProblem, index0: int) -> None:
    """Gan z_ref tu mkcbres neu file khong co (mknapcb ghi 0 = khong co)."""
    if problem.z_ref is None:
        problem.z_ref = _references().get((problem.m, problem.n, index0))

class _Numbers:
    """Doc sequential so tu list, bao loi neu thieu du lieu."""
    def __init__(self, values, source: str):
        self.values = values
        self.source = source
        self.position = 0
    def take(self, count: int) -> list:
        if self.position + count > len(self.values):
            raise ValueError(f"{self.source} bi thieu du lieu")
        chunk = self.values[self.position : self.position + count]
        self.position += count
        return chunk
    def finish(self) -> None:
        if self.position != len(self.values):
            raise ValueError(
                f"{self.source} con {len(self.values) - self.position} so du thua"
            )

def _parse_standard(path: Path) -> list:
    """mknap1 / mknapcb*: format OR-Library chuan."""
    try:
        numbers = [float(t) for t in path.read_text().split()]
    except ValueError:
        raise ValueError(f"{path.name} co dinh dang khong doc duoc") from None

    reader = _Numbers(numbers, path.name)
    problem_count = int(reader.take(1)[0])
    problems = []
    for index in range(1, problem_count + 1):
        n, m, optimum = reader.take(3)
        n, m = int(n), int(m)
        profits = np.array(reader.take(n))
        weights = np.array(reader.take(m * n)).reshape(m, n)
        capacities = np.array(reader.take(m))
        # Gia tri toi uu bang 0 nghia la file khong co
        z_ref = optimum if optimum > 0 else None
        problem = MKPProblem(
            name=f"{path.stem}_{index:02d}",
            n=n,
            m=m,
            profits=profits,
            weights=weights,
            capacities=capacities,
            z_ref=z_ref,
        )
        _attach_reference(problem, index - 1)
        problems.append(problem)
    reader.finish()
    return problems

def _parse_literature(path: Path) -> list:
    """mknap2: cac block 'problem TEN.DAT', co comment // va dau +."""
    text = path.read_text()
    parts = _LITERATURE_BLOCK.split(text)
    problems = []
    for i in range(1, len(parts), 2):
        instance = parts[i]
        body = re.sub(r"//.*", " ", parts[i + 1])
        body = re.sub(r"[+]", " ", body)
        try:
            numbers = [float(t) for t in body.split()]
        except ValueError:
            raise ValueError(
                f"{path.name} block {instance} co dinh dang khong doc duoc"
            ) from None
        reader = _Numbers(numbers, f"{path.name}:{instance}")
        # Header: so knapsack (m), so object (n)
        m, n = (int(v) for v in reader.take(2))
        profits = np.array(reader.take(n))
        capacities = np.array(reader.take(m))
        weights = np.array(reader.take(m * n)).reshape(m, n)
        optimum = reader.take(1)[0]
        reader.finish()
        problems.append(
            MKPProblem(
                name=Path(instance).stem,
                n=n,
                m=m,
                profits=profits,
                weights=weights,
                capacities=capacities,
                z_ref=optimum if optimum > 0 else None,
            )
        )
    if not problems:
        raise ValueError(f"{path.name} khong co block 'problem' nao")
    return problems

def load_problems(file_path) -> list:
    """Doc mot file, tra ve danh sach MKPProblem.
    Ten bai: mknap1/mknapcb -> <ten_file>_<k hai chu so>;
    mknap2 -> ten instance (SENTO1, WEING1, ...).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)
    if _LITERATURE_BLOCK.search(path.read_text()):
        return _parse_literature(path)
    return _parse_standard(path)

def get_problem(file_name: str, problem_number: int) -> MKPProblem:
    """Lay dung mot bai trong data/mknap. problem_number tinh tu 1."""
    if file_name not in _problem_cache:
        _problem_cache[file_name] = load_problems(DATA_DIR / file_name)
    problems = _problem_cache[file_name]
    if not 1 <= problem_number <= len(problems):
        raise ValueError(
            f"{file_name} chi co {len(problems)} bai, khong co bai {problem_number}"
        )
    return problems[problem_number - 1]
