#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#  _____ _____ _____ _____ 
# |   __|     |   __|  |  |
# |  |  |  |  |__   |     |
# |_____|_____|_____|__|__|
# 
#       (C) JPL 2019
#-------------------------------------------------------------------------------

import shelve
import const
import os

#-------------------------------------------------------------------------------
# These are the default values
#-------------------------------------------------------------------------------
defaultValues = [ 
    ['TIMER_STATUS', 3000],
    ['CONSOLE_PROMPT', "Gosh >>> "],
    ['CONSOLE_BACKGROUND', "#ffffff"],
    ['CONSOLE_FOREGROUND', "#000000"],
    ['CONSOLE_FONT', "Courier"],
    ['WINDOWS_CODEPAGE', "cp850"]
]

#-------------------------------------------------------------------------------
# Open config file
#-------------------------------------------------------------------------------
appDir = os.path.join(os.path.expanduser("~"), const.APP_FOLDER)
if not os.path.exists(appDir):
    os.makedirs(appDir)
db = shelve.open(os.path.join(os.path.join(appDir, const.CONFIG_FILE)))

#-------------------------------------------------------------------------------
 # Set default values if they not exists in config file
 #-------------------------------------------------------------------------------
for x in defaultValues:
   if not x[0] in db:
      db[x[0]] = x[1]

#-------------------------------------------------------------------------------
# Save config file
#-------------------------------------------------------------------------------
db.sync()
