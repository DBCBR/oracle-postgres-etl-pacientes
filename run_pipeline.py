from pathlib import Path
import sys

# Wrapper to import and run src/run_pipeline.py
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from run_pipeline import main

if __name__ == '__main__':
    main()
