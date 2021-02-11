import os
import sys
import logging

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
sys.path.append(sources)


logging.basicConfig(level=logging.INFO)