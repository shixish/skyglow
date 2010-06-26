#!/usr/bin/env python

from wizard import Wizard, WizardPage
from PyQt4 import QtCore, QtGui
import sys, os


class SGWizard(Wizard):

    def __init__(self, parent=None):
        super(SGWizard, self).__init__(parent)

        self.pathsPage = PathsPage(self)
        # TODO page to de/select files within a data directory
        self.finishPage = FinishPage(self)

        self.setFirstPage(self.pathsPage)

        self.setWindowTitle('Sky Glow Wizard')


class SGWizardPage(WizardPage):

    def __init__(self, parent):
        super(SGWizardPage, self).__init__(parent)

        self.wizard = parent
    

class PathsPage(SGWizardPage):

    completeStateChanged = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(PathsPage, self).__init__(parent)

        topLabel = QtGui.QLabel('Select Data Directory and Location for Results')

        dataLabel = QtGui.QLabel('Data Path')
        resultsLabel = QtGui.QLabel('Results Path')

        self.dataPath = QtGui.QLineEdit('')
        self.dataPath.setReadOnly(True)
        self.resultsPath = QtGui.QLineEdit('')
        self.resultsPath.setReadOnly(True)
        
        self.dataButton = QtGui.QPushButton('Data')
        self.resultsButton = QtGui.QPushButton('Results')

        self.dataButton.clicked.connect(self.queryDataPath)
        self.resultsButton.clicked.connect(self.queryResultsPath)
        self.dataPath.textChanged.connect(self.completeStateChanged)
        self.resultsPath.textChanged.connect(self.completeStateChanged)

        contentLayout = QtGui.QGridLayout()
        contentLayout.addWidget(dataLabel, 0, 0)
        contentLayout.addWidget(self.dataPath, 0, 1)
        contentLayout.addWidget(self.dataButton, 0, 2)
        contentLayout.addWidget(resultsLabel, 1, 0)
        contentLayout.addWidget(self.resultsPath, 1, 1)
        contentLayout.addWidget(self.resultsButton, 1, 2)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(topLabel)
        mainLayout.addLayout(contentLayout)
        self.setLayout(mainLayout)

    def resetPage(self):
        self.dataPath.setText('')
        self.resultsPath.setText('')

    def nextPage(self):
        return self.wizard.finishPage

    def queryDataPath(self):
        d = QtGui.QFileDialog.getExistingDirectory(self, 'Select Data Directory')
        if d:
            self.dataPath.setText(d)
            

    def queryResultsPath(self):
        d = QtGui.QFileDialog.getExistingDirectory(self, 'Select Results Directory')
        if d:
            self.resultsPath.setText(d)

    def pathChanged(self):
        dPath = self.dataPath.text().__str__()
        rPath = self.resultsPath.text().__str__()

        self.canContinue = False

        # TODO make sure we can read/write
        # TODO make sure there are good img files in the data directory
        # TODO be able to select single img file
        if not dPath:
            # warn dialog
            pass
        elif not rPath:
            # warn dialog
            pass
        elif not os.path.isdir(dPath):
            # warn dialog
            pass
        elif not os.path.isdir(rPath):
            # warn dialog
            pass
        else:
            self.canContinue = True

        self.completeStateChanged.emit()

    def isComplete(self):
        dPath = self.dataPath.text().__str__()
        rPath = self.resultsPath.text().__str__()

        canContinue = False

        # TODO make sure we can read/write
        # TODO make sure there are good img files in the data directory
        # TODO be able to select single img file
        if not dPath:
            # warn dialog
            pass
        elif not rPath:
            # warn dialog
            pass
        elif not os.path.isdir(dPath):
            # warn dialog
            pass
        elif not os.path.isdir(rPath):
            # warn dialog
            pass
        else:
            canContinue = True

        return canContinue


class FinishPage(SGWizardPage):

    completeStateChanged = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(FinishPage, self).__init__(parent)

        topLabel = QtGui.QLabel('Click Finish to begin generating data products')

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(topLabel)
        self.setLayout(mainLayout)

    def isLastPage(self):
        return True




def main(args):
    app = QtGui.QApplication(args)
    wiz = SGWizard()
    wiz.show()
    app.lastWindowClosed.connect(app.quit)
    app.exec_()

if __name__=="__main__":
    main(sys.argv)
