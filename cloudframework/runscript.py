from core import core
import sys,os

# init core
core.init(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));
core.dispatchTerminalApp(sys.argv[1]);
