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
from PyQt4 import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from subprocess import Popen, PIPE, STDOUT
import time
from datetime import datetime
import pickle
import os, platform, sys, socket, zipfile
import xml.etree.ElementTree as ET

import settings
import const
import commandsUI as cUI
import syntax

#-------------------------------------------------------------------------------
# resource_path()
# Define function to import external files when using PyInstaller.
#-------------------------------------------------------------------------------
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#-------------------------------------------------------------------------------
# Class MainWindow
#-------------------------------------------------------------------------------
class MainWindow ( QMainWindow ):
    """MainWindow inherits QMainWindow"""
    appDir = ""
    aCommands = []
    iCommands = 0
    CurrentOS = platform.system()
    CurrentDrive = os.path.splitdrive(os.path.realpath(__file__))[0]
    CurrentDir = os.path.splitdrive(os.path.dirname(os.path.realpath(__file__)))[1]

#-------------------------------------------------------------------------------
# __init__()
#-------------------------------------------------------------------------------
    def __init__ ( self, parent = None ):
        QMainWindow.__init__( self, parent )
        uic.loadUi('mainwindow.ui', self)
        self.action_Quit.triggered.connect(self.close)
        self.btnEnter.clicked.connect(self.runCommand)
        self.txtCommand.installEventFilter(self)
        
        self.appDir = os.path.join(os.path.expanduser("~"), const.APP_FOLDER)
        if not os.path.exists(self.appDir):
            os.makedirs(self.appDir)

        self.restoreSettings()
        self.btnSaveSettings.clicked.connect(self.backupSettings)
        self.btnCancelSettings.clicked.connect(self.cancelSettings)
        self.lblConsoleBackgroundColor.mouseReleaseEvent = self.colorBackgroundPicker
        self.lblConsoleForegroundColor.mouseReleaseEvent = self.colorForegroundPicker
        self.lblConsoleFont.mouseReleaseEvent = self.fontPicker
        
        self.txtConsoleOut.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
        self.txtConsoleOut.setReadOnly(True)
        
        self.lblConsoleBackgroundColor.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
        self.lblConsoleForegroundColor.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
        self.lblConsoleBackgroundColor.setText(settings.db['CONSOLE_BACKGROUND'])
        self.lblConsoleForegroundColor.setText(settings.db['CONSOLE_FOREGROUND'])
        self.lblConsoleFont.setText(settings.db['CONSOLE_FONT'])

        self.lblTime = QLabel("0.000 ms")
        self.lblTime.setFrameShape(QFrame.Panel)
        self.lblTime.setFrameShadow(QFrame.Sunken)
        self.lblTime.setLineWidth(1)
        self.lblTime.setFont(QFont('Courier', 10))

        self.lblRC = QLabel("RC=0")
        self.lblRC.setFrameShape(QFrame.Panel)
        self.lblRC.setFrameShadow(QFrame.Sunken)
        self.lblRC.setLineWidth(1)
        self.lblRC.setFont(QFont('Courier', 10))

        self.lblLED = QLabel()
        self.lblLED.setPixmap(QPixmap("led_green.png"))
        
        self.btnBookmark.mousePressEvent = self.addBookmark

        self.lblCDR = QLabel(self.CurrentDrive)
        self.lblCDR.setFrameShape(QFrame.Panel)
        self.lblCDR.setFrameShadow(QFrame.Sunken)
        self.lblCDR.setLineWidth(1)
        self.lblCDR.setFont(QFont('Courier', 10))
        
        self.lblPWD = QLabel(self.CurrentDir)
        self.lblPWD.setFrameShape(QFrame.Panel)
        self.lblPWD.setFrameShadow(QFrame.Sunken)
        self.lblPWD.setLineWidth(1)
        self.lblPWD.setFont(QFont('Courier', 10))
        
        self.cbxCommands.activated[str].connect(self.commandsClicked)
        self.populateCommandsList()
        
        self.btnSaveXML.clicked.connect(self.saveXML)
        self.btnExportXML.clicked.connect(self.exportXML)
        self.btnImportXML.clicked.connect(self.importXML)
        self.dirtyFlag = False
        highlight = syntax.PythonHighlighter(self.txtEditXML.document())
        with open(os.path.join(self.appDir, const.COMMANDS_FILE)) as xmlFile:
            self.txtEditXML.setPlainText(str(xmlFile.read()))
        self.txtEditXML.textChanged.connect(self.changedText)
        self.txtEditXML.cursorPositionChanged.connect(self.cursorPosition)
        self.txtEditXML.setTabStopWidth(self.txtEditXML.fontMetrics().width(' ') * 3)
        self.cursorPosition()
        
        self.setHelpText()
        
        self.statusBar.addPermanentWidget(self.lblCDR)
        self.statusBar.addPermanentWidget(self.lblPWD)
        self.statusBar.addPermanentWidget(self.lblTime)
        self.statusBar.addPermanentWidget(self.lblRC)
        self.statusBar.addPermanentWidget(self.lblLED)
        self.repaint()
        self.colLabel = self.lblRC.palette().button().color();        
        self.statusBar.showMessage("Welcome", settings.db['TIMER_STATUS'])
        self.flagBusy = False
        self.txtCommand.setFocus()
        self.tabWidget.setCurrentIndex(0)

#-------------------------------------------------------------------------------
# keyPressEvent()
#-------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_F1:
            self.tabWidget.setCurrentIndex(3)
        if key == Qt.Key_F5:
            self.txtCommand.setText("")
            self.tabWidget.setCurrentIndex(0)
            self.myCommandsUI.reset()
            self.txtCommand.setFocus()
        elif key == Qt.Key_F3:
            self.runCommand()
        elif key == Qt.Key_F10:
            self.close()

#-------------------------------------------------------------------------------
# setHelpText()
#-------------------------------------------------------------------------------
    def setHelpText(self):
        infoHost = "<center><table cellpadding='0' cellspacing='5'>"

        infoHost = infoHost + "<tr bgcolor='#6992c2'><td colspan = 2><center><b>" + const.APPLICATION_NAME + "</b></center></td></tr>"

        infoHost = infoHost + "<tr><td colspan = 2><center><i>" + const.BLAHBLAH_01 + "</i></center></td></tr>"
        infoHost = infoHost + "<tr><td colspan = 2><center><i>" + const.BLAHBLAH_02 + "</i></center></td></tr>"
        infoHost = infoHost + "<tr><td colspan = 2><center><i>" + const.BLAHBLAH_03 + "</i></center></td></tr>"
        infoHost = infoHost + "<tr><td colspan = 2>&nbsp;</td></tr>"
        
        infoHost = infoHost + "<tr><td><b>Author</b></td><td>" + const.AUTHOR + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Copyright</b></td><td>" + const.COPYRIGHT + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>License</b></td><td>" + const.LICENSE + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Version</b></td><td>" + const.VERSION + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Email</b></td><td>" + const.EMAIL + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Organization Name</b></td><td>" + const.ORGANIZATION_NAME + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Organization Domain</b></td><td>" + const.ORGANIZATION_DOMAIN + "</td></tr>"        
        infoHost = infoHost + "<tr><td colspan = 2>&nbsp;</td></tr>"
        
        infoHost = infoHost + "<tr bgcolor='#6992c2'><td colspan = 2><center><b>Host</b></center></td></tr>"
        
        infoHost = infoHost + "<tr><td><b>Hostname</b></td><td>" + socket.gethostname() + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Machine</b></td><td>" + platform.machine() + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Version</b></td><td>" + platform.version() + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Platform</b></td><td>" + platform.platform() + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>System</b></td><td>" + platform.system() + "</td></tr>"
        infoHost = infoHost + "<tr><td><b>Processor</b></td><td>" + platform.processor() + "</td></tr>"
        infoHost = infoHost + "<tr><td colspan = 2>&nbsp;</td></tr>"
        infoHost = infoHost + "<tr><td><b>Python version</b></td><td>" + sys.version + "</td></tr>"
        infoHost = infoHost + "<tr><td colspan = 2>&nbsp;</td></tr>"       
        
        infoHost = infoHost + "<tr bgcolor='#6992c2'><td colspan = 2><center><b>Interface</b></center></td></tr>"        
        
        infoHost = infoHost + "<tr><td><b>F1</b></td><td>Show this help page</td></tr>"
        infoHost = infoHost + "<tr><td><b>F3</b></td><td>Run the command</td></tr>"
        infoHost = infoHost + "<tr><td><b>F5</b></td><td>Show the console page and clear the command line</td></tr>"
        infoHost = infoHost + "<tr><td><b>F10</b></td><td>Exit the program</td></tr>"
        
        infoHost = infoHost + "</table></center>"

        self.txtHelp.setText(infoHost)

#-------------------------------------------------------------------------------
# commandsClicked()
#-------------------------------------------------------------------------------
    def commandsClicked(self, text):
        self.statusBar.showMessage(self.cbxCommands.currentText(), settings.db['TIMER_STATUS'])
        self.myCommandsUI = cUI.CommandsUI(os.path.join(self.appDir, const.COMMANDS_FILE), self.cbxCommands.currentText(), self)
    
#-------------------------------------------------------------------------------
# __del__()
#-------------------------------------------------------------------------------
    def __del__ ( self ):
        self.ui = None

#-------------------------------------------------------------------------------
# fontPicker()
#-------------------------------------------------------------------------------
    def fontPicker(self, event):
        font, ok = QFontDialog.getFont()
        if ok:
            self.lblConsoleFont.setText(font.family()+ " " + str(font.pointSize()))
            self.lblConsoleFont.setFont(QFont(font.family(), font.pointSize()))
            self.txtConsoleOut.setFont(QFont(font.family(), font.pointSize()))

#-------------------------------------------------------------------------------
# colorBackgroundPicker()
#-------------------------------------------------------------------------------
    def colorBackgroundPicker(self, event):
        color = QColorDialog.getColor()
        settings.db['CONSOLE_BACKGROUND'] = color.name()
        self.lblConsoleBackgroundColor.setText(settings.db['CONSOLE_BACKGROUND'])
        self.txtConsoleOut.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
        self.lblConsoleForegroundColor.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
        self.lblConsoleBackgroundColor.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
    
#-------------------------------------------------------------------------------
# colorForegroundPicker()
#-------------------------------------------------------------------------------
    def colorForegroundPicker(self, event):
        color = QColorDialog.getColor()
        settings.db['CONSOLE_FOREGROUND'] = color.name()
        self.lblConsoleForegroundColor.setText(settings.db['CONSOLE_FOREGROUND'])
        self.txtConsoleOut.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
        self.lblConsoleForegroundColor.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))
        self.lblConsoleBackgroundColor.setStyleSheet("QWidget { background-color: %s; color: %s}" % (settings.db['CONSOLE_BACKGROUND'], settings.db['CONSOLE_FOREGROUND']))

#-------------------------------------------------------------------------------
# saveXML()
#-------------------------------------------------------------------------------
    def saveXML(self):
        with open(os.path.join(self.appDir, const.COMMANDS_FILE), 'w') as xmlFile:
            xmlFile.write(str(self.txtEditXML.toPlainText()))
        self.dirtyFlag = False
        self.lblDirtyFlag.setText("")
        self.populateCommandsList()
        self.statusBar.showMessage("XML file saved", settings.db['TIMER_STATUS'])

#-------------------------------------------------------------------------------
# exportXML()
#-------------------------------------------------------------------------------
    def exportXML(self):
        name = "%s_%s_%s.zip" % (const.APPLICATION_NAME, socket.gethostname(), datetime.today().strftime("%Y%m%d%H%M%S")) 
        target = str(QFileDialog.getExistingDirectory(self, "Select target directory"))
        if target != "":
            zf = zipfile.ZipFile(os.path.join(target, name), "w", zipfile.ZIP_DEFLATED)
            zf.write(os.path.join(self.appDir, const.COMMANDS_FILE), const.COMMANDS_FILE)
            zf.close()
            self.statusBar.showMessage("File exported as %s to %s" % (name, target), settings.db['TIMER_STATUS'])
        else:
            self.statusBar.showMessage("Export cancelled", settings.db['TIMER_STATUS'])
    
#-------------------------------------------------------------------------------
# importXML()
#-------------------------------------------------------------------------------
    def importXML(self):
        pass
    
#-------------------------------------------------------------------------------
# changedText()
#-------------------------------------------------------------------------------
    def changedText(self):
        self.dirtyFlag = True
        self.lblDirtyFlag.setText("*modified*")
    
#-------------------------------------------------------------------------------
# cursorPosition()
#-------------------------------------------------------------------------------
    def cursorPosition(self):
        line = self.txtEditXML.textCursor().blockNumber() + 1
        col = self.txtEditXML.textCursor().columnNumber() + 1
        self.lblLineCursor.setText("Line : %d" % line)
        self.lblColumnCursor.setText("Column : %d" % col)
        
#-------------------------------------------------------------------------------
# cancelSettings()
#-------------------------------------------------------------------------------
    def cancelSettings(self):
        self.txtTimerStatus.setText(str(settings.db['TIMER_STATUS']))
        self.txtConsolePrompt.setText(settings.db['CONSOLE_PROMPT'])
        self.txtWindowsCodePage.setText(settings.db['WINDOWS_CODEPAGE'])

#-------------------------------------------------------------------------------
# restoreSettings()
#-------------------------------------------------------------------------------
    def restoreSettings(self):
        try:
            with open(os.path.join(self.appDir, const.HISTORY_FILE), "rb") as fp:
                self.aCommands = pickle.load(fp)
                self.iCommands = len(self.aCommands)
        except:
            pass
        #
        regSettings = QSettings()
        size = regSettings.value('MainWindow/Size', QSize(600,500))
        try:
            self.resize(size)
        except:
            self.resize(size.toSize())
        position = regSettings.value('MainWindow/Position', QPoint(0,0))
        try:
            self.move(position)
        except:
            self.move(position.toPoint())
        try:
            self.restoreState(regSettings.value("MainWindow/WindowState", b"", type='QByteArray'))
            splitterSettings = regSettings.value("MainWindow/SplitterSettings")
            if splitterSettings:
                try:
                    self.splitter.restoreState(splitterSettings)
                except:
                    try:
                        self.splitter.restoreState(splitterSettings.toPyObject())    
                    except:
                        pass
        except:
            pass
        self.cancelSettings()

#-------------------------------------------------------------------------------
# addBookmark()
#-------------------------------------------------------------------------------
    def addBookmark(self, event):
        self.statusBar.showMessage("CLICK STAR", settings.db['TIMER_STATUS'])

#-------------------------------------------------------------------------------
# backupSettings()
#-------------------------------------------------------------------------------
    def backupSettings(self):
        with open(os.path.join(self.appDir, const.HISTORY_FILE), "wb") as fp:
            pickle.dump(self.aCommands, fp)
        #
        regSettings = QSettings()
        regSettings.setValue("MainWindow/Size", self.size())
        regSettings.setValue("MainWindow/Position", self.pos())
        regSettings.setValue("MainWindow/WindowState", self.saveState())
        splitterSettings = self.splitter.saveState()
        if splitterSettings:
            regSettings.setValue("MainWindow/SplitterSettings", self.splitter.saveState())     
        settings.db['TIMER_STATUS'] = int(self.txtTimerStatus.text())
        settings.db['CONSOLE_PROMPT'] = self.txtConsolePrompt.text()
        settings.db['WINDOWS_CODEPAGE'] = self.txtWindowsCodePage.text()
        settings.db.sync()
        self.statusBar.showMessage("Settings saved", settings.db['TIMER_STATUS'])
        
#-------------------------------------------------------------------------------
# runCommand()
#-------------------------------------------------------------------------------
    def runCommand(self):        
        self.flagBusy = True
        self.btnEnter.setEnabled(False)
        self.statusBar.showMessage("Running...", settings.db['TIMER_STATUS'])
        self.lblLED.setPixmap(QPixmap("led_red.png"))
        self.repaint()
        self.aCommands.append(self.txtCommand.text())
        self.iCommands = self.iCommands + 1        
        command = str(self.txtCommand.text()).strip()
        if command == "cls" or command == "clear":
            self.txtConsoleOut.setText("")
            self.statusBar.showMessage("Command executed", settings.db['TIMER_STATUS'])
        elif command == "quit" or command == "exit":
            self.close()
        elif command[1:2] == ":":
            self.CurrentDrive = command[0:2].upper()
            self.CurrentDir = os.sep
            self.statusBar.showMessage("Current drive changed", settings.db['TIMER_STATUS'])
        elif command[0:3] == "cd ":
            self.CurrentDir = command[3:]
            self.statusBar.showMessage("Current directory changed", settings.db['TIMER_STATUS'])
        else:
            self.txtConsoleOut.append(settings.db['CONSOLE_PROMPT'] + command + "\n")
            time1 = time.time()
            # p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True, shell = True)
            p = Popen(command, cwd=os.path.join(self.CurrentDrive, self.CurrentDir), stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1, shell = True)
            p.poll()
            while True:
                line = p.stdout.readline()
                if self.CurrentOS == "Windows":
                    sLine = line.decode(settings.db['WINDOWS_CODEPAGE']).rstrip()
                    oLine = self.patchChars(sLine)
                    self.txtConsoleOut.append(oLine)
                else:
                    self.txtConsoleOut.append(line.rstrip())
                self.repaint()
                if not line and p.poll is not None: 
                    break

            while True:
                err = p.stderr.readline()
                if self.CurrentOS == "Windows":
                    sLine = err.decode(settings.db['WINDOWS_CODEPAGE']).rstrip()
                    oLine = self.patchChars(sLine)
                    self.txtConsoleOut.append(oLine)
                else:
                    self.txtConsoleOut.append(err.rstrip())
                self.repaint()
                if not err and p.poll is not None: 
                    break

            self.txtConsoleOut.moveCursor(QTextCursor.End)
            rc = p.poll()
            self.lblRC.setText("RC=" + str(rc))
            if rc != 0:
                self.lblRC.setStyleSheet('background-color : red; color: white')
            else:
                self.lblRC.setStyleSheet('background-color:' + self.colLabel.name() + '; color: black')
            time2 = time.time()
            elapsed = (time2-time1)*1000.0
            self.statusBar.showMessage("Command executed in {:.3f} ms".format(elapsed), settings.db['TIMER_STATUS'])
            self.lblTime.setText("{:.3f} ms".format(elapsed))
        self.tabWidget.setCurrentIndex(0)
        self.flagBusy = False
        self.btnEnter.setEnabled(True)
        self.lblCDR.setText(self.CurrentDrive)
        self.lblPWD.setText(self.CurrentDir)
        self.lblLED.setPixmap(QPixmap("led_green.png"))
        self.txtCommand.selectAll()
        self.txtCommand.setFocus()

#-------------------------------------------------------------------------------
# closeEvent()
#-------------------------------------------------------------------------------
    def closeEvent(self, event):
        if self.dirtyFlag == True:
            result = QMessageBox.question(self,"Commands file modified","Do you want to save it before ?",QMessageBox.Yes| QMessageBox.No)
            if result == QMessageBox.Yes:
                self.saveXML()
        result = QMessageBox.question(self,"Confirm Exit","Are you sure you want to quit ?",QMessageBox.Yes| QMessageBox.No)        
        if result == QMessageBox.Yes:
            self.statusBar.showMessage("Good bye", settings.db['TIMER_STATUS'])
            self.backupSettings()
            event.accept()
        else:
            self.statusBar.showMessage("Welcome back", settings.db['TIMER_STATUS'])
            event.ignore()

#-------------------------------------------------------------------------------
# eventFilter()
#-------------------------------------------------------------------------------
    def eventFilter(self, object, event):
        if object is self.txtCommand and event.type() == event.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                if self.iCommands > 0:
                    self.iCommands = self.iCommands - 1
                else:
                    self.iCommands = len(self.aCommands) - 1
                self.txtCommand.setText(self.aCommands[self.iCommands])
            elif key == Qt.Key_Down:
                if self.iCommands < (len(self.aCommands) - 1):
                    self.iCommands = self.iCommands + 1
                else:
                    self.iCommands = 0
                self.txtCommand.setText(self.aCommands[self.iCommands])
            elif key in (Qt.Key_Enter, Qt.Key_Return):
                self.runCommand()
        return False
    
#-------------------------------------------------------------------------------
# patchChars()
#-------------------------------------------------------------------------------
    def patchChars(self, s):
        myChars = {'“':'ô', 'Š':'ê', '‚':'é', 'ÿ':''}
        foo = s.split()
        ret = []
        for item in foo:
            ret.append(myChars.get(item, item)) # Try to get from dict, otherwise keep value
        return(" ".join(ret))

#-------------------------------------------------------------------------------
# checkCommandsFile()
#-------------------------------------------------------------------------------
    def checkCommandsFile(self):
        try:
            xmlFile = open(os.path.join(self.appDir, const.COMMANDS_FILE), 'r')
        except:
            xmlFile = open(os.path.join(self.appDir, const.COMMANDS_FILE), 'w+')
            xmlFile.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            xmlFile.write("<root>\n")
            xmlFile.write("\t<commands>\n")
            if platform.system() == "Windows":
                xmlFile.write("\t\t<command title='Informations systeme'>\n")
                xmlFile.write("\t\t\t<value>systeminfo</value>\n")
                xmlFile.write("\t\t\t<label>Informations de configuration du systeme</label>\n")
                xmlFile.write("\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t<option format='BUTTON'>\n")
                xmlFile.write("\t\t\t\t\t\t\t<value>/?</value>\n")
                xmlFile.write("\t\t\t\t\t\t<label>Aide</label>\n")
                xmlFile.write("\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t<option format='SYSNAME'>\n")
                xmlFile.write("\t\t\t\t\t\t<value>/S</value>\n")
                xmlFile.write("\t\t\t\t\t\t<label>Systeme</label>\n")
                xmlFile.write("\t\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<option format='USERNAME'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<value>/U</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<label>Utilisateur</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t<option format='PASSWORD'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t\t<value>/P</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t\t<label>Mot de passe</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t<option format='LIST'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<value>/FO</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<label>Format</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<list>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<item>TABLE</item>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<item>LIST</item>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<item>CSV</item>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t</list>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t<option format='CHECKBOX'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t<value>/NH</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t<label>Pas d'en-tete</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t</group>\n")
                xmlFile.write("\t\t</command>\n")
            else:
                xmlFile.write("\t\t<command title='Informations systeme'>\n")
                xmlFile.write("\t\t\t<value>systeminfo</value>\n")
                xmlFile.write("\t\t\t<label>Informations de configuration du systeme</label>\n")
                xmlFile.write("\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t<option format='BUTTON'>\n")
                xmlFile.write("\t\t\t\t\t\t\t<value>/?</value>\n")
                xmlFile.write("\t\t\t\t\t\t<label>Aide</label>\n")
                xmlFile.write("\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t<option format='SYSNAME'>\n")
                xmlFile.write("\t\t\t\t\t\t<value>/S</value>\n")
                xmlFile.write("\t\t\t\t\t\t<label>Systeme</label>\n")
                xmlFile.write("\t\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<option format='USERNAME'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<value>/U</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<label>Utilisateur</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t<option format='PASSWORD'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t\t<value>/P</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t\t<label>Mot de passe</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t<option format='LIST'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<value>/FO</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<label>Format</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<list>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<item>TABLE</item>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<item>LIST</item>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<item>CSV</item>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t</list>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t<group>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t<options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t<option format='CHECKBOX'>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t<value>/NH</value>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t\t<label>Pas d'en-tete</label>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t\t\t\t</option>\n")
                xmlFile.write("\t\t\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t\t\t</group>\n")
                xmlFile.write("\t\t\t\t</options>\n")
                xmlFile.write("\t\t\t</group>\n")
                xmlFile.write("\t\t</command>\n")
            xmlFile.write("\t</commands>\n")
            xmlFile.write("</root>\n")
        xmlFile.close()

#-------------------------------------------------------------------------------
# populateCommandsList()
#-------------------------------------------------------------------------------
    def populateCommandsList(self):
        self.cbxCommands.clear()
        self.checkCommandsFile()
        tree = ET.parse(os.path.join(self.appDir, const.COMMANDS_FILE))
        root = tree.getroot()
        for commands in root.iter("commands"):
            for command in commands.iter("command"):
                self.cbxCommands.addItem(command.attrib['title'])

"""
TODO
"""
