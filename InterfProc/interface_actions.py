# -*- coding: utf-8 -*-
'''
Created by Lionel Chiron  02/10/2013 
Copyright (c) 2013 __NMRTEC__. All rights reserved.
'''
import sys, os
opd = os.path.dirname
dir_path_interf = opd(os.path.abspath(__file__)) # directory of InterfProc
dir_path_general = opd(dir_path_interf) # draft directory
from InterfProc.Pyside_PyQt4 import *
import os.path as op
from time import sleep
from mail_error_logger import Logger
from InterfProc.Config_by_interf import config
import glob
import subprocess
import pickle
import threading 
import time


class interact(object):
    '''
    Interact with Fista.

    '''
    def __init__(self, interface):
        self.path = ''
        self.interface = interface
        self.dial = Dialog(interface, self)
        self.make_connections()
        self.config = config(interface, self)
        
    def connection_buttons(self):
        '''
        Disable buttons.
        '''
        self.interface.ui.pushButton_2.setEnabled(False)
        self.interface.ui.pushButton.setEnabled(False)
        self.interface.ui.pushButton_3.clicked.connect(self.dial.open_dir_dialog)

    ##################################### Menu Help  

    def make_connections(self):
        '''
        Applying connexion and context menu
        '''
        self.connection_buttons()
    
    def processmpi(self):
        path_processing = os.path.join(dir_path_general, 'processing.py')
        process = 'sh InterfProc/processingmpi.sh {} {} {} '.format(self.config.proc_number, path_processing, self.config.addr_new_config_file)
        print '#############'
        print "process is ", process
        print '#############'
        subprocess.call(process, shell = True)
    
    def refresh_progbar(self):
        pb = ['F2', 0]
        while pb[0] != 'end':
            try:
                f = open('InterfProc/progbar.pkl')
                pb = pickle.load(f)
                self.progressbar(pb[0], pb[1])
                print "pickle result ",pb
                f.close()
                time.sleep(1)
            except:
                pass
            #self.progressbar('F1', 30)
        # except:
        #     print 'pickle does not work, perhaps too early'
        
    
    def do_processing(self):
        '''
        Using command shell line for processing with mpi.
        '''
        t0 = threading.Thread(target=self.processmpi).start()
        t1 = threading.Thread(target=self.refresh_progbar).start()
    

    def progressbar(self, typepgrb, index):
        if typepgrb == 'F2':
            self.interface.ui.progressBar.setValue(index)
        elif typepgrb == 'F1':
            self.interface.ui.progressBar_2.setValue(index)
    
class Dialog(QtGui.QWidget):

    def __init__(self, interface, interact):
        QtGui.QWidget.__init__(self)
        self.interface = interface
        self.interact = interact
        
    def save_last_rep(self):
        '''
        '''
        f = open(os.path.join(dir_path_interf, 'last_rep.txt'), 'w')
        f.write(self.path)
        f.close()
    
    def open_dir_dialog(self):
        """
        Opens directory containing the files to process Fid with urQRd.
        """
        qd = QtGui.QFileDialog
        f = open(os.path.join(dir_path_interf, 'last_rep.txt'), 'r')
        addr = f.readline()
        print "last directory is ", addr
        f.close()
        self.path = qd.getExistingDirectory(None, 'Batch directory', addr, qd.ShowDirsOnly)
        self.save_last_rep()
        self.interface.ui.label_4.setText('Data directory : ' + self.path)
        self.interact.path = self.path
        self.interface.ui.pushButton_2.setEnabled(True)
        self.interface.ui.pushButton_2.clicked.connect(self.interact.config.run) # launch interface configuration.
        self.interact.config.path = self.path
        
    def about(self):
        '''Popup a box with about message.'''
        QMessageBox.about(self, "About PyQt, Platform and the like",
                """<b> About this program </b> v %s
                #<p>Copyright  2013 Lionel Chiron. 
                #All rights reserved in accordance with
                ## - NO WARRANTIES!
                ##<p>This application can be used for
                ##displaying OS and platform details.
                ###<p>Python %s -  PySide version %s - Qt version %s on %s"""  % 
                (__version__, platform.python_version(), PySide.__version__,
                 PySide.QtCore.__version__, platform.system()))
        


