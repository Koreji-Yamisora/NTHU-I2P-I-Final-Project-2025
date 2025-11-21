import sys
from importlib import import_module

before = set(sys.modules)


from src.core.engine import Engine

if __name__ == "__main__":
    engine = Engine()
    engine.run()
after = set(sys.modules)

loaded = list(after - before)
for name in loaded:
    print(name)
