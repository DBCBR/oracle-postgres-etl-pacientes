from pathlib import Path
import sys

# Wrapper to import module from src (underscore name)
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
import robo_consultor  # executes the module

if __name__ == '__main__':
    pass