"""Chay SA tren dataset MKP bang mot lenh ngan.

Vi du (chay tu thu muc goc repo):
    python run_sa.py mknapcb4 1
    python run_sa.py mknapcb4 all -t 10 -s 7
    python run_sa.py --list
"""

import sys

from run_algo import main


if __name__ == "__main__":
    sys.exit(main("simulated_annealing"))
