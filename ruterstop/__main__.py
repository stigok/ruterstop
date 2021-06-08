import os
import sys

# Don't require installing this package in order to run this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ruterstop import main

main()
