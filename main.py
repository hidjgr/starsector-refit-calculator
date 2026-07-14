#!/usr/bin/python

from core.api import get_game_path
import sys
get_game_path(sys.argv)

import ui.gui

ui.gui.root.mainloop()
