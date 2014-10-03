'''
Created by Lionel Chiron  02/10/2013 
Copyright (c) 2013 __NMRTEC__. All rights reserved.
'''
import sys, os
from InterfProc.configUi import Ui_MainWindow as Ui
from InterfProc.Pyside_PyQt4 import *
opd = os.path.dirname
dir_path_interf = opd(os.path.abspath(__file__)) # path of the directory of the current file
dir_path_general = opd(dir_path_interf) # path of the directory above the directory of the current file ('draft')
import shutil as sh


'''
Program for making the process.mscf file from the interface. 
First make a self.param object containing information from interface. 
Then read the configfile and fill the interface with the values found there. 
'''

class config(): #interface
    '''
    '''
    def __init__(self, interface, interact):
        self.interface = interface
        self.interact = interact
        self.path = ''
        self.checked = QtCore.Qt.CheckState.Checked
        self.param = {}
        try:
            whichapp =  'app is QtGui.QApplication(sys.argv)'
            self.app = QtGui.QApplication(sys.argv)
        except :
            whichapp = 'app is QtCore.QCoreApplication.instance()'
            self.app = QtCore.QCoreApplication.instance()           # Correction for Canopy
        print whichapp 
        self.window = QtGui.QMainWindow()
        self.addr_orig_processing_mscf = os.path.join(dir_path_general, 'process_eg.mscf')
        print "self.addr_orig_processing_mscf = ", self.addr_orig_processing_mscf
        self.addr_last_processing_mscf = os.path.join(dir_path_general, 'process_last.mscf')
        self.ui = Ui()# 
        self.ui.setupUi(self.window)                            #set up of the main window
        self.make_param_dic()                                   # make a dictionary for the parameters to be modified or not.
        self.read_config()                                      # read the configfile and complete the dictionary
        self.ui.pushButton.clicked.connect(self.save_config)    # button for saving configfile

    def make_param_dic(self):
        '''
        Make the object self.param from the Pyside interface informations.
        '''
        self.configui = open('InterfProc/configUi.py','r')
        for param in self.param:
            self.param[param] = ''  # self.param[param] contains a blank in case the parameter is not specified.
        self.configui.close() 
            
        for l in self.configui.readlines():
            if ('label' in l  or 'checkBox' in l) and 'setText' in l:
                try:
                    nb = l.split('.')[1].split('_')[1]
                except:
                    nb = ''
                if 'label' in l:
                    elem = 'l'
                elif 'checkBox' in l:
                    elem = 'c'
                try:
                    self.param[l.split('"')[3].split(':')[0].rstrip()] = [elem+nb]
                except:
                    print "l.split() ", l.split('"')
                    print "no position 3 in the string"
        self.configui.close()
        print self.param
        
    def read_config(self):
        '''
        read the Original config file or the last config file produced.
        Saved mscf is saved next to processed files.
        Show the values in the interface.
        '''
        print 'take a configfile for making self.param'
        if not os.path.exists(self.addr_last_processing_mscf):
            file_config = open(self.addr_orig_processing_mscf,'r') # takes the example config file for completing the dictionary
            print "using self.addr_orig_processing_mscf ", self.addr_orig_processing_mscf
            self.current_used_configfile = self.addr_orig_processing_mscf
        else:
            file_config = open(self.addr_last_processing_mscf,'r') # takes the last config file for completing the dictionary
            print "using self.addr_last_processing_mscf ", self.addr_last_processing_mscf
            self.current_used_configfile = self.addr_last_processing_mscf
        for line in file_config:
            for param in self.param: 
                     
                if line.startswith(param) : # if the line in the configfile contains an entry of the interface.. 
                    value_mscf = line.split('=')[1]
                    self.param[param].append(value_mscf)    # build a dictionnary from the used config file.

            if len(self.param['proc_number']) == 1:
                self.param['proc_number'].append('1')
                self.proc_number = 1
        
        # Show in the interface the default values.
        # print "setting values in the interface from the configfile"
        # print "#################"
        # print "self.param ", self.param
        # print "#################"
        for param in self.param:
            '''
            For each element in self.param set the corresponding object in the interface with the right value. 
            '''
            print "param is ", param
            if self.param.has_key(param):
                print "self.param.has_key(param)"
                kind, attr = self.choose_attr(param) # according to the ui object is lineEdit or checkBox make a choice.
                print "kind, attr ",kind, attr
                setcf = getattr(self.ui, attr)     # retrieve the corresponding attribute in the interface
                if kind == 'l':
                    #print "self.param[param] ", self.param[param]
                    setcf.setText(self.param[param][1])                     # set the line values.
                if kind == 'c':
                    print "param ", param
                    #print eval(self.param[param][1])
                    if self.param[param][1] == '':
                        self.param[param][1] = 'False'
                    print "self.param[param][1] ",self.param[param][1]
                    setcf.setChecked(eval(self.param[param][1]))            # make the check buttons
        print "param ", param
        file_config.close()
    
    def choose_attr(self, param):
        '''
        according to the element in the dictionary param,  return lineEdit or checkBox. 
        '''
        cf_kind = self.param[param][0]
        if cf_kind[0] == 'l':                   # values entered inline.
            return 'l', 'lineEdit' + '_' + cf_kind[1:]
        elif cf_kind[0] == 'c':                 # checkbox
            if cf_kind[1:] != '':
                return 'c','checkBox' + '_' + cf_kind[1:]
            else:
                return 'c','checkBox'
    
    def write_case(self, param, new_config_file, setcf, kind):
        '''
        Called in "save_config" once read_config has been done.
        Write parameters with their value in the new config file.
        '''
        print "####### write case for param ", param
        if kind == 'l':
            new_config_file.writelines(param + ' = ' + setcf.text().lstrip() + '\n')
        if param == 'proc_number':
            self.proc_number = int(setcf.text())                                # keep the value from interface of the number of proc for multiprocessing. 
            print "self.proc_number ", self.proc_number
        elif kind == 'c':
            if setcf.checkState() == self.checked :
                chstate = 'True'
            else:
                chstate = 'False'
            new_config_file.writelines(param + ' = ' + chstate + '\n')
    
    def save_config(self):
        '''
        Write new configfile next to the file to the data to be processed.
        Write also in the InterfProc directory the last process.mscf used.   
        '''
        print "write the configfiles"
        num_lines = sum(1 for line in open(self.current_used_configfile))
        print "num_lines ",num_lines
        file_config = open(self.current_used_configfile,'r')                          # take an arbitrary configfile for presenting values in the interface (process_eg.mscf or last process.mscf)
        self.addr_new_config_file = self.path[:-2]+'.mscf'                              # address for the mscf just close to the file to process.
        new_config_file = open(self.addr_new_config_file,'w')
        proc_number_found = False
        for numline, line in enumerate(file_config):
            print_line = True
            for param in self.param:
                if 'proc_number' in line:
                    proc_number_found = True # there is a line with "proc_number"
                # print "numline ", numline
                # print "num_lines-1 ",num_lines-1
                # print "not proc_number_found ",not proc_number_found
                # print "numline == (num_lines-1) and not proc_number_found ",numline == num_lines and not proc_number_found
                if line.startswith(param) or (numline == (num_lines-1) and not proc_number_found) :
                    print_line = False
                    kind, attr = self.choose_attr(param)
                    setcf = getattr(self.ui, attr) 
                    self.write_case(param, new_config_file, setcf, kind)
                    break
            if print_line:
                new_config_file.writelines(line)                                        # write the new configfile next to the file to be processed.
        new_config_file.close()
        print 'created the config file at address ', self.addr_new_config_file
        file_config.close()                                                             # close the configfile
        sh.copy(self.addr_new_config_file, self.addr_last_processing_mscf)              # keep a copy of the configfile in InterfProc
        print 'copied the config file at address ', self.addr_last_processing_mscf
        self.window.close()                                                             # close the configuration window.
        self.interface.ui.pushButton.setEnabled(True)                                   # Enable the processing once all the preceding steps have been done.
        self.interface.ui.pushButton.clicked.connect(self.interact.do_processing)       # execute the processing..
    
    def run(self):
        print 'run configuration file'
        self.window.show()
