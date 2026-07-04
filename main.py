#!/usr/bin/python

from core.api import get_game_path
import sys
get_game_path(sys.argv)

from ui.gui import root

root.mainloop()
