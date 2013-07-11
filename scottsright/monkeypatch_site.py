""""""
import sys

def resetquit(builtins):
    """Redefine builtins 'quit' and 'exit' not so close stdin

    """
    def __call__(self, code=None):
        raise SystemExit(code)
    __call__.__name__ = 'FakeQuitCall'
    builtins.quit.__class__.__call__ = __call__

if 'site' in sys.modules:
    resetquit(sys.modules['__builtin__'])
