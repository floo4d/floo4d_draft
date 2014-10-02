'''
Created by Lionel Chiron  02/10/2013 
Copyright (c) 2013 __NMRTEC__. All rights reserved.
'''
import sys, os
from interfProcessingUi import Ui_MainWindow as Ui
from InterfProc.Pyside_PyQt4 import *

class interf(): #interface
    '''
    Creation of the graphic window
    Methods :
        init_interf
        run
    '''
    def __init__(self):
        try:
            whichapp =  'app is QtGui.QApplication(sys.argv)'
            self.app = QtGui.QApplication(sys.argv)
        except :
            whichapp = 'app is QtCore.QCoreApplication.instance()'
            self.app = QtCore.QCoreApplication.instance() # Correction for Canopy
        print whichapp 
        self.window = QtGui.QMainWindow()
        self.ui = Ui()# 
        self.ui.setupUi(self.window)#set up of the main window
        
    def makemenubar(self):
        '''
        Add elements to the menubar
        '''
        self.menubar = self.window.menuBar()

        if not hasattr(self,'menubar_file'):
            self.menubar_file = self.menubar.addMenu('&File')
        if not hasattr(self,'menubar_help'):
            self.menubar_help = self.menubar.addMenu('&Help')
        
    def run(self):
        self.window.show()
        sys.exit(self.app.exec_()) # Correction for Canopy
   
    
