#!/usr/bin/env python

import sys
from PyQt4 import QtCore, QtGui

class Wizard(QtGui.QDialog):

    history = []

    def __init__(self, parent=None):
        super(Wizard, self).__init__(parent)

        self.cancelButton = QtGui.QPushButton("Cancel", self)
        self.backButton = QtGui.QPushButton("< &Back", self)
        self.nextButton = QtGui.QPushButton("Next >", self)
        self.finishButton = QtGui.QPushButton("&Finish", self)

        self.cancelButton.clicked.connect(self.reject)
        self.backButton.clicked.connect(self.backButtonClicked)
        self.nextButton.clicked.connect(self.nextButtonClicked)
        self.finishButton.clicked.connect(self.accept)

        self.buttonLayout = QtGui.QHBoxLayout()

        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.backButton)
        self.buttonLayout.addWidget(self.nextButton)
        self.buttonLayout.addWidget(self.finishButton)

        self.mainLayout = QtGui.QVBoxLayout()
        self.mainLayout.addStretch(1)
        self.mainLayout.addLayout(self.buttonLayout)
        self.setLayout(self.mainLayout)

    def setFirstPage(self, page):
        page.resetPage()
        self.history.append(page)
        self.switchPage(None)

    def backButtonClicked(self):
        oldPage = self.history.pop(-1)
        oldPage.resetPage()
        self.switchPage(oldPage)

    def nextButtonClicked(self):
        oldPage = self.history[-1]
        newPage = oldPage.nextPage()
        newPage.resetPage()
        self.history.append(newPage)
        self.switchPage(oldPage)

    def completeStateChanged(self):
        currentPage = self.history[-1]
        if currentPage.isLastPage():
            self.finishButton.setEnabled(currentPage.isComplete())
        else:
            self.nextButton.setEnabled(currentPage.isComplete())

    def switchPage(self, oldPage):
        if oldPage:
            oldPage.hide()
            self.mainLayout.removeWidget(oldPage)
            oldPage.completeStateChanged.disconnect(self.completeStateChanged)

        newPage = self.history[-1]
        self.mainLayout.insertWidget(0, newPage)
        newPage.show()
        newPage.setFocus()
        newPage.completeStateChanged.connect(self.completeStateChanged)

        self.backButton.setEnabled(len(self.history) != 1)
        if newPage.isLastPage():
            self.nextButton.setEnabled(False)
            self.finishButton.setDefault(True)
        else:
            self.nextButton.setDefault(True)
            self.finishButton.setEnabled(False)

        self.completeStateChanged()

class WizardPage(QtGui.QWidget):
    
    completeStateChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(WizardPage, self).__init__(parent)

        self.hide()

    def resetPage(self):
        pass

    def nextPage(self):
        return None

    def isLastPage(self):
        return False

    def isComplete(self):
        return True
