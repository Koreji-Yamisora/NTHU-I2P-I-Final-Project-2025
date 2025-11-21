import sys
from importlib import import_module


from src.core.engine import Engine

if __name__ == "__main__":
    engine = Engine()
    engine.run()
