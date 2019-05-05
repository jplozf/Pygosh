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

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from mainwindow import MainWindow
import const

if __name__ == '__main__':
    # create application
    app = QApplication(sys.argv)
    app.setOrganizationName(const.ORGANIZATION_NAME)
    app.setOrganizationDomain(const.ORGANIZATION_DOMAIN)    
    app.setApplicationName(const.APPLICATION_NAME)
    
    # set icon
    icon = QIcon("16x16/Light.png")
    app.setWindowIcon(icon)    
    
    # create widget
    w = MainWindow()
    w.setWindowTitle(const.APPLICATION_NAME)
    w.show()

    # connection
    QObject.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))

    # execute application
    sys.exit(app.exec_())
