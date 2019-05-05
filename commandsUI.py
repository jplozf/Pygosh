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
import xml.etree.ElementTree as ET
import const, os

#-------------------------------------------------------------------------------
# Class CommandsUI
#-------------------------------------------------------------------------------
class CommandsUI():
    xeq = ""
    par = {}
    anonymous = 0

#-------------------------------------------------------------------------------
# __init__()
#-------------------------------------------------------------------------------
    def __init__ (self, file, cmd, widget):
        layout = widget.pnlArguments.layout()
        self.clearLayout(layout)

        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout,0,0)
        lineLayout.addWidget(QLabel(cmd))
        
        self.xeq = self.parseCommand(file, cmd, layout)
        self.widget = widget
        # self.widget.setWidgetResizable(True)
        self.updateCommandLine()

        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

#-------------------------------------------------------------------------------
# reset()
#-------------------------------------------------------------------------------
    def reset(self):
        self.par = {}
        self.anonymous = 0

#-------------------------------------------------------------------------------
# updateCommandLine()
#-------------------------------------------------------------------------------
    def updateCommandLine(self):
        xeq =  self.xeq
        for p in self.par:
            if " " in self.par[p]:
                pvalue = "'" + self.par[p] + "'"
            else:
                pvalue = self.par[p]
            if p[0:len(const.NOT_AVAILABLE_LABEL)] == const.NOT_AVAILABLE_LABEL:
                xeq = xeq + " " + pvalue
            else:
                xeq = xeq + " " + p + " " + pvalue
        self.widget.txtCommand.setText(xeq)

#-------------------------------------------------------------------------------
# addOptionSysname()
#-------------------------------------------------------------------------------
    def addOptionSysname(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        myLineEdit = QLineEdit()
        myLineEdit.textChanged.connect(lambda value, x=myLineEdit, y=option: self.uiSysnameEvent(x, value, option))
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        lineLayout.addWidget(myLineEdit)

#-------------------------------------------------------------------------------
# addOptionUsername()
#-------------------------------------------------------------------------------
    def addOptionUsername(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        myLineEdit = QLineEdit()
        myLineEdit.textChanged.connect(lambda value, x=myLineEdit, y=option: self.uiUsernameEvent(x, value, option))
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        lineLayout.addWidget(myLineEdit)

#-------------------------------------------------------------------------------
# addOptionPassword()
#-------------------------------------------------------------------------------
    def addOptionPassword(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        myPassword = QLineEdit()
        myPassword.setEchoMode(QLineEdit.Password)
        myPassword.textChanged.connect(lambda value, x=myPassword, y=option: self.uiPasswordEvent(x, value, option))
        lineLayout.addWidget(myPassword)

#-------------------------------------------------------------------------------
# addOptionFile()
#-------------------------------------------------------------------------------
    def addOptionFile(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        myFileEdit = QLineEdit()
        myFileEdit.textChanged.connect(lambda value, x=myFileEdit, y=option: self.uiFileEvent(x, value, option))
        lineLayout.addWidget(myFileEdit)
        myButtonFile = QPushButton()
        myButtonFile.setIcon(QIcon('16x16/Document.png'))
        myButtonFile.clicked.connect(lambda state, x=myFileEdit, y=self.getExtensionFile(option): self.uiButtonFileEvent(x, y))
        lineLayout.addWidget(myButtonFile)

#-------------------------------------------------------------------------------
# addOptionNewFile()
#-------------------------------------------------------------------------------
    def addOptionNewFile(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        myFileEdit = QLineEdit()
        myFileEdit.textChanged.connect(lambda value, x=myFileEdit, y=option: self.uiNewFileEvent(x, value, option))
        lineLayout.addWidget(myFileEdit)
        myButtonFile = QPushButton()
        myButtonFile.setIcon(QIcon('16x16/Document.png'))
        myButtonFile.clicked.connect(lambda state, x=myFileEdit, y=self.getExtensionFile(option): self.uiButtonNewFileEvent(x, y))
        lineLayout.addWidget(myButtonFile)

#-------------------------------------------------------------------------------
# addOptionDir()
#-------------------------------------------------------------------------------
    def addOptionDir(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        myFileEdit = QLineEdit()
        myFileEdit.textChanged.connect(lambda value, x=myFileEdit, y=option: self.uiDirEvent(x, value, option))
        lineLayout.addWidget(myFileEdit)
        myButtonFile = QPushButton()
        myButtonFile.setIcon(QIcon('16x16/Folder.png'))
        myButtonFile.clicked.connect(lambda state, x=myFileEdit: self.uiButtonDirEvent(x))
        lineLayout.addWidget(myButtonFile)

#-------------------------------------------------------------------------------
# addOptionNewDir()
#-------------------------------------------------------------------------------
    def addOptionNewDir(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        myFileEdit = QLineEdit()
        myFileEdit.textChanged.connect(lambda value, x=myFileEdit, y=option: self.uiNewDirEvent(x, value, option))
        lineLayout.addWidget(myFileEdit)
        myButtonFile = QPushButton()
        myButtonFile.setIcon(QIcon('16x16/Folder.png'))
        myButtonFile.clicked.connect(lambda state, x=myFileEdit: self.uiButtonNewDirEvent(x))
        lineLayout.addWidget(myButtonFile)

#-------------------------------------------------------------------------------
# addOptionCheckbox()
#-------------------------------------------------------------------------------
    def addOptionCheckbox(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        myCheckBox = QCheckBox()
        myCheckBox.stateChanged.connect(lambda state, x=myCheckBox, y=option: self.uiCheckboxEvent(x, state, option))
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        lineLayout.addWidget(myCheckBox)

#-------------------------------------------------------------------------------
# addOptionLink()
#-------------------------------------------------------------------------------
    def addOptionLink(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        myButton = QPushButton(self.getLabel(option))
        myButton.clicked.connect(lambda state, x=option: self.uiButtonEvent(x))
        lineLayout.addWidget(myButton)

#-------------------------------------------------------------------------------
# addOptionList()
#-------------------------------------------------------------------------------
    def addOptionList(self, layout, row, option):
        lineLayout = QHBoxLayout()
        layout.addLayout(lineLayout, row)
        myListBox = QComboBox()
        for item in self.getListItems(option):
            myListBox.addItem(item)
        lineLayout.addWidget(QLabel(self.getLabel(option)))
        myListBox.currentIndexChanged.connect(lambda index, x=myListBox, y=option: self.uiListboxEvent(x, index, option))
        lineLayout.addWidget(myListBox)

#-------------------------------------------------------------------------------
# clearLayout()
#-------------------------------------------------------------------------------
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

#-------------------------------------------------------------------------------
# parseCommand()
#-------------------------------------------------------------------------------
    def parseCommand(self, file, cmd, layout):
        tree = ET.parse(file)
        root = tree.getroot()
        for commands in root.iter("commands"):
            for command in commands.iter("command"):
                if cmd == command.attrib['title']:
                    xeq = command.find("value").text
                    for alt in command.iter("group"):
                        x = 0
                        groupBox = QGroupBox()
                        groupBoxLayout=QVBoxLayout()
                        groupBox.setLayout(groupBoxLayout)
                        options = alt.find("options")
                        for option in options.iter("option"):
                            x = x + 1
                            if option.attrib['format'] == "SYSNAME":
                                self.addOptionSysname(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "USERNAME":
                                self.addOptionUsername(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "PASSWORD":
                                self.addOptionPassword(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "BUTTON":
                                self.addOptionLink(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "LINK":
                                self.addOptionLink(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "LIST":
                                self.addOptionList(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "FILE":
                                self.addOptionFile(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "NEWFILE":
                                self.addOptionNewFile(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "DIR":
                                self.addOptionDir(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "NEWDIR":
                                self.addOptionNewDir(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "CHECKBOX":
                                self.addOptionCheckbox(groupBoxLayout, x, option)
                            elif option.attrib['format'] == "LABEL":
                                print("LABEL")
                        layout.addWidget(groupBox)
        return xeq

#-------------------------------------------------------------------------------
# uiSysnameEvent()
#-------------------------------------------------------------------------------
    def uiSysnameEvent(self, lineEdit, value, option):
        if value == "":
            self.removeParameter(option.find("value").text)
        else:
            self.addParameter(option.find("value").text, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# uiUsernameEvent()
#-------------------------------------------------------------------------------
    def uiUsernameEvent(self, lineEdit, value, option):
        if value == "":
            self.removeParameter(option.find("value").text)
        else:
            self.addParameter(option.find("value").text, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# uiPasswordEvent()
#-------------------------------------------------------------------------------
    def uiPasswordEvent(self, lineEdit, value, option):
        if value == "":
            self.removeParameter(option.find("value").text)
        else:
            self.addParameter(option.find("value").text, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# uiButtonEvent()
#-------------------------------------------------------------------------------
    def uiButtonEvent(self, option):
        self.addParameter(option.find("value").text, "")
        self.updateCommandLine()
    
#-------------------------------------------------------------------------------
# uiListboxEvent()
#-------------------------------------------------------------------------------
    def uiListboxEvent(self, listBox, index, option):
        value = listBox.itemText(index)
        if value == const.NOT_AVAILABLE_LABEL:
            self.removeParameter(option.find("value").text)
        else:
            self.addParameter(option.find("value").text, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# uiCheckboxEvent()
#-------------------------------------------------------------------------------
    def uiCheckboxEvent(self, checkBox, state, option):
        if state == Qt.Checked:
            self.addParameter(option.find("value").text, "")
        else:
            self.removeParameter(option.find("value").text)
        self.updateCommandLine()
    
#-------------------------------------------------------------------------------
# uiButtonFileEvent()
#-------------------------------------------------------------------------------
    def uiButtonFileEvent(self, fileEdit, ext):
        filename = str(QFileDialog.getOpenFileName(None, 'Open file', '', ext))
        fileEdit.setText(os.path.normpath(filename))
    
#-------------------------------------------------------------------------------
# uiButtonNewFileEvent()
#-------------------------------------------------------------------------------
    def uiButtonNewFileEvent(self, fileEdit, ext):
        filename = str(QFileDialog.getSaveFileName(None, 'New file', '', ext))
        fileEdit.setText(os.path.normpath(filename))

#-------------------------------------------------------------------------------
# uiFileEvent()
#-------------------------------------------------------------------------------
    def uiFileEvent(self, lineEdit, value, option):
        if option.find("value") is None:
            name = (const.NOT_AVAILABLE_LABEL + "%05d" % self.anonymous)
            self.anonymous = self.anonymous + 1
        else:
            name = option.find("value").text
        if value == "":
            self.removeParameter(name)
        else:
            self.addParameter(name, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# uiNewFileEvent()
#-------------------------------------------------------------------------------
    def uiNewFileEvent(self, lineEdit, value, option):
        if option.find("value") is None:
            name = (const.NOT_AVAILABLE_LABEL + "%05d" % self.anonymous)
            self.anonymous = self.anonymous + 1
        else:
            name = option.find("value").text
        if value == "":
            self.removeParameter(name)
        else:
            self.addParameter(name, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# uiButtonDirEvent()
#-------------------------------------------------------------------------------
    def uiButtonDirEvent(self, fileEdit):
        filename = str(QFileDialog.getExistingDirectory(None, 'Open directory', ''))
        fileEdit.setText(os.path.normpath(filename))
    
#-------------------------------------------------------------------------------
# uiButtonNewDirEvent()
#-------------------------------------------------------------------------------
    def uiButtonNewDirEvent(self, fileEdit):
        filename = str(QFileDialog.getExistingDirectory(None, 'New directory source', ''))
        fileEdit.setText(os.path.normpath(filename))

#-------------------------------------------------------------------------------
# uiDirEvent()
#-------------------------------------------------------------------------------
    def uiDirEvent(self, lineEdit, value, option):
        if option.find("value") is None:
            name = (const.NOT_AVAILABLE_LABEL + "%05d" % self.anonymous)
            self.anonymous = self.anonymous + 1
        else:
            name = option.find("value").text
        if value == "":
            self.removeParameter(name)
        else:
            self.addParameter(name, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# uiNewDirEvent()
#-------------------------------------------------------------------------------
    def uiNewDirEvent(self, lineEdit, value, option):
        if option.find("value") is None:
            name = (const.NOT_AVAILABLE_LABEL + "%05d" % self.anonymous)
            self.anonymous = self.anonymous + 1
        else:
            name = option.find("value").text
        if value == "":
            self.removeParameter(name)
        else:
            self.addParameter(name, value)
        self.updateCommandLine()

#-------------------------------------------------------------------------------
# getLabel()
#-------------------------------------------------------------------------------
    def getLabel(self, option):
        sLabel = const.NOT_AVAILABLE_LABEL
        label = option.find("label")
        if label is not None:
            sLabel = label.text
        return sLabel
    
#-------------------------------------------------------------------------------
# getExtensionFile()
#-------------------------------------------------------------------------------
    def getExtensionFile(self, option):
        sExt = ""
        ext = option.find("ext")
        if ext is not None:
            sExt = ext.text
        return sExt

#-------------------------------------------------------------------------------
# getListItems()
#-------------------------------------------------------------------------------
    def getListItems(self, list):
        lItems = [const.NOT_AVAILABLE_LABEL]
        for item in list.iter("item"):
            lItems.append(item.text)
        return lItems
    
#-------------------------------------------------------------------------------
# addParameter()
#-------------------------------------------------------------------------------
    def addParameter(self, param, value):
        if not param in self.par:
            self.par[param] = value
        else:
            self.par.pop(param)
            self.par[param] = value
        print(self.par)
    
#-------------------------------------------------------------------------------
# removeParameter()
#-------------------------------------------------------------------------------
    def removeParameter(self, param):
        if param in self.par:
            self.par.pop(param)

"""
TODO :

* addOptionNewFile
* addOptionFiles
* addOptionDirectory
* addOptionNewDirectory
* addGroupBox
* addOptionOptions

"""

    
