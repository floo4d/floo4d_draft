'''
Created by Lionel Chiron  18/10/2013 
Copyright (c) 2013 __NMRTEC__. All rights reserved.
'''
from util.debug_tools import dec_class_pr, decclassdebugging, debug, pr
import os, sys, glob, re, shutil
from time import time, strftime, localtime
from matplotlib import pyplot as plt
import numpy as np
from numpy import fft
import unittest
###
from NPKData import NPKData, as_cpx
from NPKData import as_cpx, copyaxes
###
from Algo.urQRd import urQRd
from Algo.urQRd_util.Config import config_urqrd
param = config_urqrd()
import Algo.urQRd_util.pickle_instance # for now, obliged not to create itrators nowhere but for mp...
from Algo.urQRd_util.versions import save_working_pckg_versions
from File.Thermo import Import_1D as importOrbi
from Algo.urQRd_util.read_mass_spec import FTICR_treat, Orbitrap_treat
from Algo.urQRd_util.algo_debug import urqrd_debugs
#####
import multiprocessing as mproc
import itertools
######

save_working_pckg_versions()
__version__ = 0.1
__date__ = "Nov 2013"

'''
urQRd denoising.
'''
def datetime():
    "return string coding current date"
    from time import time, strftime, localtime
    return strftime('%Y-%m-%d-%Hh-%M-%S', localtime())


class NAMEfile(object):
    '''
    File names for Applic_urQRd.
    '''
    def __init__(self, urqrd):
        self.urqrd = urqrd
        self.deb_name = os.path.join(urqrd.directory_results, "Processed_")
        self.extension = ".csv"
        self.makes_name()

    def makes_name(self):
        '''
        Builds the name for saving data.
        Called in do_ref and do_Fista
        '''
        self.ref_spec = os.path.join(self.deb_name + '_ref_' + self.extension)                                 # name for reference.
        self.urqrd_spec = os.path.join(self.deb_name + '_urqrd_spec_' + self.extension)                                                #
        self.urqrd_fid = os.path.join(self.deb_name + '_urqrd_' + self.extension)
      
@dec_class_pr
@decclassdebugging
class UrQRd_denoise(object):
    '''
    Makes denoising with urQRd (You are cured !!!)
    '''
    def __init__(self, configfile):
        self.save_date = False
        self.directory_results = None                   #directory containing files result of the processing
        self.param = config_urqrd(configfile)           # Proc_Parameters() object containing additional parameters for processing
        '''
        loads store information.
        '''
        self.save_ref_spec = self.param.save_ref_spec         # saves reference spectrum.
        self.save_urqrd_spec = self.param.save_urqrd_spec     # saves urqrd result
        self.save_urqrd_fid = self.param.save_urqrd_fid       # saves urqrd denoised fid
        ####
        self.save_date = self.param.save_date                 # saves file with date
        self.addr_data_saved = self.param.addr_data_saved     # address of the directory where to save data.
        '''
        Defines parameters for treatment
        '''
        self.rank = self.param.rank                           # rank parameter, rule of thumb: two times the number of lines
        self.iterations = self.param.iterations               # iterations for urQRd.
        self.zerofill = self.param.zerofill                   # zerofilling for the reference spectrum.
        self.orb = Orbitrap_treat()
        self.fticr = FTICR_treat()
        self.ext_fticr = ['.d', '.msh5']
        self.ext_orb = ['.dat']
        self.makes_directory()
        self.namef = NAMEfile(self)
    
    def report(self):
        "dumps content"
        for i in dir(self):
            if not i.startswith('_'):
                print i, getattr(self,i)
    
    def f_init(self,q):
        global fq
        fq = q
    
    def do_urqrd(self):
        '''
        Performs urQRd
        '''
        print "self.rank, self.iterations ", self.rank, self.iterations
        self.urqrd_fid = self.data.copy()
        urqrd_denoised = urQRd(self.data_interm.buffer, self.rank, iterations = self.iterations) # urqrd on fid
        self.urqrd_fid.buffer = urqrd_denoised
    
    def recupdata(self):
        '''
        Takes the FTICR data .
        The bandwith is changed via the attribute specwidth
        '''
        if self.kind_data == 'fticr':
            datafticr = self.fticr.read(self.addr_file)
            datafticr.specwidth = 2*161290.33 #APO_AI
            return datafticr
        elif self.kind_data == 'orb':
            dataorbit = importOrbi(self.addr_file) # read in npk data format
            return dataorbit
    
    def solve(self):
        '''
        Save reference if asked and solve urqrd.
        '''
        self.data = self.recupdata() # produces a NPK object data, defines self.resol
        self.data_interm = self.data.copy() # copy original, NPK object data
        print "self.data_interm.itype ", self.data_interm.itype
        print "before do_ref"
        print "self.kind_data ",self.kind_data
        self.do_ref() # saves the reference spectrum
        self.do_urqrd()
        self.saving_urqrd()
        
    def xy_from_data(self, data, MaxMass=5000):
        '''
        makes x, y from y for FTICR and Orbitrap
        '''
        imax = data.axis1.mztoi(MaxMass)
        x, y = data.axis1.mass_axis(), data.buffer
        return x[imax:], y[imax:]

    def solve_unit(self, f):
        self.addr_file = f #
        self.solve()
        
    def check_ext_ok(self, f):
        self.name, self.ext = os.path.splitext(f)
        if self.ext in self.ext_fticr or self.ext in self.ext_orb:
            return True
        else:
            return False

    def name_and_ext(self, f):
        '''
        '''
        if self.check_ext_ok(f):
            print "good extension"
            self.keep_kind_data(self.ext)
            return True
        return False
    
    def solve_file(self):
        '''
        Applies urqrd to a given file
        '''
        f = self.param.file_to_treat
        if self.name_and_ext(f):
            self.solve_unit(f)
    
    def save_configfile(self):
        '''
        Saves the configfile with the data.
        '''
        name_config = 'Applic_urqrd.mscf'
        path_configfile = os.path.join(os.path.dirname(self.directory_results), name_config)
        if os.path.exists(path_configfile): # If yet a configfile
            shutil.move(path_configfile, self.directory_results)
            print "moved ", path_configfile, "to ", self.directory_results
        else:
            path_configfile = os.path.join(os.path.dirname(__file__), name_config)
            print "path_configfile is ", path_configfile
            shutil.copy2(path_configfile, self.directory_results)
    
    def makes_directory(self):
        '''
        Makes the storage directory containing the reference file, processed file etc.. 
        '''
        if self.addr_data_saved == '':
            self.directory_results = self.param.filename + '_urqrd_' + datetime()
            print "##### self.directory_results is ", self.directory_results
        else:
            self.directory_results = os.path.join(self.addr_data_saved, os.path.basename(self.param.filename))
        if not os.path.exists(self.directory_results):
            os.mkdir(self.directory_results)
        self.save_configfile()
    
    def do_ref(self):
        '''
        Computes and saves the csv of reference spectrum (ZF FFT Modulus)
        '''
        ref_spec = self.data.chsize(self.zerofill*self.data.size1).apod_sin(maxi = 0.5).rfft().modulus()
        xref, yref = self.xy_from_data(ref_spec)
        name_data = self.namef.ref_spec                                                                     #self.makes_name('ref_spec')
        self.save_csv(xref, yref , name_data, kind = 'ref_spec')

    def saving_urqrd(self):
        '''
        Saves the spectrum and the fid obtained with urQRd.
        The sizes are copied from the size of the reference spectrum.
        '''
        urqrd_fid_spec = self.urqrd_fid.copy()
        if self.save_urqrd_spec :
            name_data = self.namef.urqrd_spec #self.makes_name('urqrd_spec')
            urqrd_spec = urqrd_fid_spec.chsize(self.zerofill*self.data.size1).apod_sin(maxi = 0.5).rfft().modulus()
            x, y = self.xy_from_data(urqrd_spec)
            self.save_csv(x, y, name_data, kind = 'urqrd_spec')
        if self.save_urqrd_fid:
            name_data = self.namef.urqrd_fid #self.makes_name('urqrd_fid')
            x = ''
            y = self.urqrd_fid # FTICR or NPKData
            self.save_csv(x, y, name_data, kind = 'urqrd_fid')

    def makecsv(self, dataname, data, namefile):
        '''
        format to enter :  "name 1st col   name 2nd col ",(x, y), namefile
        format of the data is given by option fmt.
        '''
        output = np.column_stack(data)
        with open(namefile, 'wb') as f:
            f.write(dataname + '\n')
            np.savetxt(f, output, delimiter = ',', fmt = '%1.16e')
        print "###### saved csv file ", namefile

    # def save_file_native_format(self, y, namefile):
    #     '''
    #     Data are saved with their original format.
    #     '''
    #     if self.kind_data == 'orb':
    #         print "type(y.buffer) ", type(y.buffer)
    #         self.orb.write(y.buffer, namefile)
    #     elif self.kind_data == 'fticr':
    #         self.fticr.write(y, namefile)

    def save_csv(self, x, y, namef, kind = ''):
        '''
        Save data after urqrd was performed.
        Data stored are the urQRd processed Fid, the urQRd processed spectrum
        and the reference spectrum.
        '''
        if kind == 'urqrd_fid' :
            self.makecsv("urqrd_fid",(y), namef ) #   # save urqrd fid
        if kind == 'ref_spec' :
            self.makecsv("#mz   ref_spec",(x, y), namef ) # 
        if kind == 'urqrd_spec' :
            self.makecsv("#mz   urqrd_spec",(x, y), namef ) #

                
    def keep_kind_data(self, ext):
        if ext in self.ext_fticr:
            self.kind_data = 'fticr'
        elif ext in self.ext_orb:
            self.kind_data = 'orb'

class Test(unittest.TestCase):
    """tests """        

    def test_applic_urqrd(self):
        "apply a complete processing test"
        main(["Applic_urQR_eg.mscf",])
     
def message_time():
    print "algo starts at ", datetime()

def main(argv = None):
    "does the whole job"
    message_time()
    ######### reads the arguments
    if not argv:
        argv = sys.argv
    try:                                            # First try to read config file from arg list
        configfile = argv[1]
    except IndexError:                              # then assumes standard name
        configfile = "Applic_urqrd.mscf" 
    print "using %s as configuration file" %configfile
    urqrd = UrQRd_denoise(configfile)               # instantiate for the denoising
    urqrd.solve_file()                          # one file only processed


if __name__ == '__main__':
    main()
