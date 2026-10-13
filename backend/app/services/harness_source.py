"""Child program for the lab. It cannot import the application."""

HARNESS = r"""
import builtins
import sys

ALLOWED = {
    "math",
    "random",
    "statistics",
    "itertools",
    "functools",
    "collections",
    "dataclasses",
    "typing",
}

try:
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (512_000, 512_000))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    except (ValueError, OSError):
        pass
except Exception:
    pass


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".")[0]
    if level or root not in ALLOWED:
        raise ImportError("import not allowed: " + name)
    return builtins.__import__(name, globals, locals, fromlist, level)


class GridWorld:
    def __init__(self):
        self.goal = (3, 3)
        self.pos = (0, 0)

    def reset(self):
        self.pos = (0, 0)
        return self.pos

    def step(self, action):
        x, y = self.pos
        if action == 0:
            y = max(0, y - 1)
        elif action == 1:
            x = min(3, x + 1)
        elif action == 2:
            y = min(3, y + 1)
        elif action == 3:
            x = max(0, x - 1)
        else:
            raise ValueError("action must be 0, 1, 2, or 3")
        self.pos = (x, y)
        reward = 1.0 if self.pos == self.goal else -0.04
        done = self.pos == self.goal
        return self.pos, reward, done


names = [
    "print", "range", "len", "int", "float", "str", "bool", "list", "dict", "set", "tuple",
    "sum", "min", "max", "abs", "enumerate", "zip", "map", "filter", "sorted", "reversed",
    "round", "isinstance", "issubclass", "Exception", "ValueError", "TypeError",
    "StopIteration", "RuntimeError", "AssertionError", "KeyError", "IndexError", "iter",
    "next", "any", "all", "pow", "divmod", "repr", "slice", "object", "super", "property",
    "staticmethod", "classmethod", "__build_class__",
]
safe_builtins = {name: getattr(builtins, name) for name in names}
safe_builtins["__import__"] = safe_import
source = open(sys.argv[1], encoding="utf-8").read()
sandbox_globals = {"__builtins__": safe_builtins, "__name__": "student", "GridWorld": GridWorld}
exec(compile(source, "student.py", "exec"), sandbox_globals, sandbox_globals)
"""
