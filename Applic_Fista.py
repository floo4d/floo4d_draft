'''
Paths:
    In listpaths (beginning of the prog) enters the address to folder /draft of NPKv2. (eg '/Users/chiron/draft')
    listpaths = []
    Name of the msh5 or .d file to treat : fsup.addr_file = name msh5 or .d
    
Fista users parameter :
    triggers Fista : fsup.make_fista = True
    
Experiment parameters:
    value for superresolution : fsup.superresol = 8 # superresolution ratio
    the cut in the Fid is the inverse here of the superresolution : fsup.cut_ratio = fsup.superresol
    beginning point : fsup.cut_beg = 100000
    
Saving parameters : 
    Save truncated fid FFTed results in csv file : self.save_fft_div = True
    Save Fista results in csv file : fsup.save_fista_spec = True

Created by Lionel Chiron  18/10/2013 
Copyright (c) 2013 __NMRTEC__. All rights reserved.
'''
from util.debug_tools import dec_class_pr, decclassdebugging, debug, pr
import os, sys, glob, re, shutil
from time import strftime, localtime
import unittest
##### Visualisation.
from matplotlib import pyplot as plt
###### Multiprocessing.
import multiprocessing as mproc
import itertools
##### Processing general libraries.
from NPKData import as_cpx, copyaxes
import numpy as np
from numpy import fft
####### Fista
from Algo import Fista
from Algo.Fista_util.Config import config_fista
import Algo.CS_transformations as cstr
from util.signal_tools import findnoiselevel_offset  as findnoiselevel
import Algo.Fista_util.pickle_instance # for now, obliged not to create itrators nowhere but for mp...
from Algo.Fista_util.versions import save_working_pckg_versions
from File.Thermo import Import_1D as importOrbi
from Algo.Fista_util.read_mass_spec import FTICR_treat, Orbitrap_treat
from Algo.Fista_util.algo_debug import fista_debugs
#####

__version__ = 0.1
__date__ = "Nov 2013"

save_working_pckg_versions()

'''
Makes superresolution with Fista or makes NUS (Non Uniform Sampling).
It has to be launched after having filled the configuration file Applic_Fista.mscf located at the top of NPK. 
'''
def datetime():
    "return string coding current date"
    return strftime('%Y-%m-%d-%Hh-%M-%S', localtime())
    
class NAMEfile(object):
    '''
    File names for Applic_Fista.
    '''
    def __init__(self, fista):
        '''
        Definition of recurrent part of the names.
        '''
        self.fista = fista
        self.deb_name = os.path.join(fista.directory_results, "Processed_")
        self.extension = ".csv"
        self.end_surr = str(fista.superresol) + self.extension
        self.zerf = str(fista.zerofill_ref)
        # self.cut_end = fista.cut_beg + data.size1/fista.fid_length_div_by
        # self.intervall = '_in_' + str(fista.cut_beg) + '_to_'+ str(self.cut_end) + '_'
        self.makes_name()
        
    def makes_name(self):
        '''
        Builds the name for saving data.
        Called in do_ref and do_Fista
        '''
        div = self.fista.list_fid_length_div_by
        self.ref = os.path.join(self.deb_name + '_ref_zerf_x' + self.zerf + self.extension)                                 # name for reference.
        self.nodiv = os.path.join(self.deb_name + 'fista_x' + self.end_surr)                                                #
        self.divided = os.path.join(self.deb_name + '_div_by_' + str(div) + '_fista_x'+ self.end_surr)
        self.apod = os.path.join(self.deb_name + 'apod_fista_x' + self.end_surr)
        self.fft_div = os.path.join(self.deb_name + '_div_by_' + str(div) + '_fft'+  self.extension)
        #self.interv = os.path.join(self.deb_name + self.intervall + str(div) + '_fista_x'+ self.end_surr)

@dec_class_pr
@decclassdebugging
class FISTA_sup(object):

    def __init__(self, configfile):
        """param is the configuration file"""
        self.save_date = False
        self.directory_results = None                       # directory containing files result of the processing
        self.save_ref_spec = None                           # saves the spectrum of original data.
        self.cut_beg = None
        self.addr_file = None                               # address of the file to be processed
        self.save_fft_div = None                            # saves the truncated Fid spectrum
        self.ext_orb = None
        self.ext_fticr = None                               #
        self.orb = None                                     # an object created when loading orbitrap data
        self.fticr = None                                   # an object created when loading FTICR data
        self.data = None
        self.name = None                                    # name without extension of the processed file.
        self.save_fista_spec = None                         #
        self.ext = None                                     # extension of the file                              
        self.name_file = None
        self.kind_data = None                               # indicates the type of data, FTICR or Orbitrap.
        self.fistafft = None                                # resulting spectrum with Fista.
        self.data_sampled = False                                # takes into account of the data comes from a sampling or not.
        ##############
        self.param = config_fista(configfile)                   # Proc_Parameters() object containing additional parameters for processing
        '''
        Loads storage parameters.
        Saves a reference spectrum, and the spectra of the truncated Fid
        for Fista modulus and classical FFT. 
        '''
        #### Storage informations
        self.save_ref_spec = self.param.save_ref_spec       # saves reference spectrum.
        self.save_fista_spec = self.param.save_fista_spec   # saves Fista result
        self.save_fft_div = self.param.save_fft_div         # saves reference shorten spectrum
        self.save_date = self.param.save_date               # saves file with date
        self.addr_data_saved = self.param.addr_data_saved   # addresses for storing the data.
        #### Defines parameters for Fista algorithm.
        self.do_fista = self.param.do_fista                             # makes Fista
        self.fista_iterat = 20                                          # Fista with a given number of iterations and no lambda adaptation.
        self.prec = 0.1                                                 # precision on the residual for stopping the algorithm
        self.fista_miniterat = 300                                      # limit of iteration for fista for each lambda value.
        self.lb = 3e-6                                                  # for apodisation with wiener filter.
        self.superresol = self.param.superresol                         # superresolution ratio 
        self.divide_lambda = self.param.divide_lambda                   # correction on noise level, float number.
        #### Parameters secondary processings 
        self.cut_beg = self.param.first_point_trunc_fid                 # index of beginning of the truncation for the Fid
        self.list_fid_length_div_by = [self.param.fid_length_div_by]    # shortening factors before performing Fista processing
        self.fid_length_div_by = self.param.fid_length_div_by           # factor of reduction of the Fid length.
        self.apod_fista = self.param.apod_fista                         # apodisation for Fista.
        self.zerofill_ref = self.param.zerofill_ref                     # zerofilling for the reference spectrum, multiply the size of the spectrum by this number.
        self.show_truncated_fid = self.param.show_truncated_fid         # show the truncated Fid before processing.
        self.addr_sampling = self.param.addr_sampling                   # address of the file containing the sampling indices.
        self.data_sampled = self.param.data_sampled                     # flag to indicate if data are sampled or not.
        if self.data_sampled:                                          # if an adrress of sampling file is provided in the configuration file, retrieves the fields.
            self.sampling, self.param_sampling = cstr.sampling_load(self.addr_sampling)
        else :
            self.sampling, self.param_sampling = None, None             # no Non Uniform Sampling. 
        self.b_analyt = None                                            # Analytic for of the observed data.
        self.init_reads()                                               # instantiates classes for reading FTICR and Orbitrap
        self.makes_storing_directory()                                  # makes the storing directories.
        self.compr = True                                               # csv compression, (x,y) where y ==0 are removed
        self.namef = NAMEfile(self)                                     # instantiation for the storage namings.

    def report(self):
        "dumps content"
        for i in dir(self):
            if not i.startswith('_') or not callable(getattr(self, i)):
                print i, getattr(self, i)

    def init_reads(self):
        '''
        Instantiates classes for FTICR and Orbitrap.
        '''
        self.orb = Orbitrap_treat()
        self.fticr = FTICR_treat(self.addr_data_saved)
        self.ext_fticr = ['.d', '.msh5']
        self.ext_orb = ['.dat']
  
    def load_data(self):
        '''
        Takes the FTICR or Orbitrap data.
        The bandwidth is changed via the attribute specwidth
        '''
        if self.kind_data == 'fticr':
            data = self.fticr.read(self.addr_file)                  # reads FTICRData.
            data.specwidth = 2*161290.33 #APO_AI                    # Changes the bandwidth for FTICR data.
        elif self.kind_data == 'orb':
            data = importOrbi(self.addr_file)                       # read Orbitrap data
        if data.axis1.sampled:                                      # if flag sampled for NPKData, self.data_sampled = True
            self.data_sampled = True
        return data
    
    def em(self, x):
        '''
        Wiener filter
        multiply x(t) by exp(-lb*t)
        '''
        t = 1.0*np.arange(len(x))
        return x*np.exp(-t*self.lb)

    def apod(self, x):
        return self.em(x)
    
    def FISTA_prepare(self, data, superresol = 4):
        '''
        data is in format NPKData/FTICRData.
        Apply FISTA for superresolution
        superresol : superresolution factor
        '''
        print "### in FISTA_prepare ### "
        if debug(self):
            print "#### data.buffer.size ", data.buffer.size
        
        self.b_analyt = fft.ifft(as_cpx(data.copy().rfft().buffer))                                    # passing to analytic signal
        if debug(self):
            print "self.b_analyt.size ", self.b_analyt.size                                     # size of the analytic signal observed data.
        trans, ttrans = self.definetransf()   
        if debug(self):
            print "trans, ttrans ", trans, ttrans
        return  trans, ttrans, self.b_analyt                                             
                                                 
    def definetransf(self):
        '''
        Defining the linear transformations trans and ttrans
        1st use: from b makes a supperresolved spectrum. 
            parameter : self.superresol
        2nd use: from sampled b makes finds the spectrum we would obtain without sampling with FFT.
            parameters: self.addr_sampling address of the sampling scheme
                        self.sampling indices of the sampling operation.
        '''
        if self.data_sampled:                                                                           # NUS aposteriori
            print "len(self.sampling) ", len(self.sampling)
            tr = cstr.transformations(self.b_analyt.size, len(self.sampling), debug = 0)                
            tr.sampling = self.sampling
        #if self.addr_sampling:
        #    self.sampling, self.param_sampling = cstr.sampling_load(self.addr_sampling) 
        #    tr = cstr.transformations(sizex, len(self.sampling), debug = 0)
        #    tr.sampling = self.sampling
        else:
            tr = cstr.transformations(self.superresol*self.b_analyt.size, self.b_analyt.size, debug = 0) 
        if self.apod_fista:
            tr.tpost_ft = self.apod
        trans = tr.transform
        ttrans = tr.ttransform
        return trans, ttrans
    
    def Fista_run(self, trans, ttrans, b):
        '''
        Solves the LASSO problem with Fista. 
        Takes into account if the data are sampled or not. 
        '''
        if self.data_sampled:                                                                                                                    # if the data are sampled data
            if self.addr_sampling:                                                                                                          # if it exists a sampling file address. 
                self.data.axis1.load_sampling(self.addr_sampling)                                                                           # associated sampling scheme to data
                self.data.zf()                                                                                                              # zerofill the sampled data
                noise_level = findnoiselevel(abs(ttrans(self.data.buffer)), nbseg = 11)                                                # calculation of the nosielevel outside Fista
                fista = Fista.Fista(trans, ttrans, self.data.buffer[self.sampling], lengthx = b.size, noise_level = noise_level)            # prepares the transformation for sampling with Fista.
            else: 
                raise NPKError("no sampling file given ", data = self)
        #if self.addr_sampling: # spectrometer sampling
        #    ratio = int(1/float(self.param_sampling['# sampling ratio']))                   # retrieves the ratio between observed and spectrum. 
        #    fista = Fista.Fista(trans, ttrans, b, lengthx = b.size*ratio)                   # prepares the transformation for sampling with Fista.
        else:
            print "Performing superresolution  "
            print "b.size ", b.size
            fista = Fista.Fista(trans, ttrans, b, lengthx = self.superresol*b.size)          # prepares the transformation for superresolution with Fista.  
        '''
        Activate debugs
        '''
        fista.adaptlamb_debug = False                                      # debugs the adaptation of lambda parameter.
        fista.corealgo_debug = True                                        # debugs The core algorithm of Fista.
        fista.fistaloop_debug = True                                       # debugs the main loop of Fista.
        fista.shorten_fid_debug = True                                     # debugs the shortening of the Fid
        fista.solve_debug = True                                           # debugs of Fista solver
        fista.do_fista_debug = True                                        # 
        fista.FISTA_prepare_debug = True                                   # debugs for Transformations and the Fista run.
        # adapt forced paramters
        if self.fista_iterat:
            fista.iterat = self.fista_iterat
        if self.prec:
            fista.prec = self.prec
        if self.fista_miniterat:
            fista.miniterat = self.fista_miniterat
        if self.divide_lambda:
            fista.divide_lambda = self.divide_lambda
        fista.report()                                                  # report for Fista parameters.
        fista_debugs(fista)                                             # debugs inside Fista.
        Data = type(self.data)                                          # either FTICRData or OrbiData
        fista_solution = fista.solve()                                  # launches the algorithm.
        fista.plot_monitorings()                                        # Plots monitoring parameters.
        plt.show()                                                      # Shows the plots
        self.fistafft = Data(buffer = abs(fista_solution))              # launches Fista and makes modulus.
        copyaxes(self.data, self.fistafft)                              # copy the axis from FTICR or Orbitrap data
        self.fistafft.adapt_size()                                      # fits the size of the buffer to the object fistafft
    
    def shorten_fid(self, data_interm):
        '''
        For shortening fids, called in the method self.solve()
        '''
        data = data_interm.copy()
        if self.cut_beg != None:
            cut_end = self.cut_beg + data.size1/self.fid_length_div_by          # limit sup
            data.buffer = data.buffer[self.cut_beg : cut_end]                   # cuts the interesting part of the fid.
            data.axis1.size = data.buffer.size                                  # changes information about size of FTICRData.
            if self.show_truncated_fid :                                        # Shows the truncated Fid above the original one.
                plt.plot(np.arange(data_interm.len()), data_interm.buffer)
                plt.plot(np.arange(self.cut_beg, cut_end), data.buffer, linewidth = 0.1)
                plt.show()  
        else:
            if debug(self):
                print "doing ratio ", self.div
            data.chsize(data.size1/self.div) # truncates the fid
            if debug(self):
                print "data.buffer.size after truncation", data.buffer.size
        return data
        
    def solve(self):                                      
        '''
        Computes and saves the reference spectra if asked,  
        then solves Fista and makes FFTs if asked for short Fids.
        '''
        self.data = self.load_data()                                # produces a NPK object data, defines self.resol
        data_interm = self.data.copy()                              # copy original, NPK object data
        print "data_interm.itype ", data_interm.itype
        if self.save_ref_spec :
            self.do_ref()                                           # saves the reference spectrum with zerofilling x2 
        if self.list_fid_length_div_by != []:                       # if we want to make fista on divided spectra.
            for self.div in self.list_fid_length_div_by:
                short_fid = self.shorten_fid(data_interm)           # shorten the data dividing by fid_length_div_by 
                short_fid_copy = short_fid.copy()
                self.run_fista(short_fid)                           # makes Fista on the shorten Fid
                if self.save_fft_div :
                    self.do_fft_div(short_fid_copy)                 # makes FFT on the shorten Fid
        else: 
            long_fid = data_interm.copy()
            self.run_fista(long_fid)                                # makes Fista on the full Fid. 

    def xy_from_data(self, data, MaxMass = 5000):
        '''
        makes (x, y) pairs from y (m/z format) for FTICR or Orbitrap.
        It cuts the spectrum to MaxMass.
        '''
        imax = data.axis1.mztoi(MaxMass)
        x, y = data.axis1.mass_axis(), data.buffer
        return x[imax:], y[imax:]
    
    def run_fista(self, b):
        '''
        Fista processing and storing
        '''
        if self.do_fista :
            print "####  makes FISTA_prepare "
            trans, ttrans, b_analyt = self.FISTA_prepare(b, superresol = self.superresol)   # Prepares the transformations for Fista
            self.Fista_run(trans, ttrans, b_analyt)                                         # lauches Fista.                        
            self.saving_fista_results()                                                             # storing the results of Fista processing.
         
    def check_ext_ok(self, f):
        self.name, self.ext = os.path.splitext(f)
        if self.ext in self.ext_fticr or self.ext in self.ext_orb:
            return True
        else:
            return False

    def name_and_ext(self, f):
        if self.check_ext_ok(f):
            print "good extension"
            self.name_file = self.name
            self.keep_kind_data(self.ext)
            return True
        return False
    
    def solve_file(self):
        '''
        Applies Fista on one file
        which address is self.param.file_to_treat
        '''
        f = self.param.file_to_treat
        if self.name_and_ext(f):
            self.addr_file = f#
            self.solve()
      
    def keep_kind_data(self, ext):
        '''
        Registering the kind of data, FTICR or Orbitrap.
        '''
        if ext in self.ext_fticr:
            self.kind_data = 'fticr'
        elif ext in self.ext_orb:
            self.kind_data = 'orb'

    def do_ref(self):
        '''
        Computes and saves reference spectrum (ZF FFT Modulus)
        '''
        print "save ref"
        ref_spec = self.data.chsize(self.zerofill_ref*self.data.size1).apod_sin(maxi = 0.5).rfft().modulus()
        xref, yref = self.xy_from_data(ref_spec)
        namecsv = self.namef.ref #self.makes_name('ref')
        self.save_csv(xref, yref, namecsv, kind = 'ref')

    def do_fft_div(self, short_fid):
        '''
        Saves the fft of the truncated fid. Zerofilling for retrieving initial size and apodisation.
        Fid shortened with self.shorten_fid()
        '''
        short_fft = short_fid.chsize(self.data.size1).apod_sin(maxi = 0.5).rfft().modulus()
        xdiv, ydiv = self.xy_from_data(short_fft)
        namecsv = self.namef.fft_div #self.makes_name('fft_div')
        print "save fft_div"
        self.save_csv(xdiv, ydiv , namecsv, kind = 'fft_div')

    def saving_fista_results(self):
        '''
        Save the resolution obtained with Fista in csv format.
        Names are made with makes_name()
        The maximal m/z is fixed with mzmax.
        Fista spectrum result is stocked in self.fistafft.
        if self.compr == True it compresses the data and saves them in x,y pairs where y != 0.
        '''
        if self.save_fista_spec :
            namecsv = self.namef.nodiv #self.makes_name('nodiv')
            if self.list_fid_length_div_by != []:                          # Fista with truncature before superresolution
                namecsv = self.namef.divided #self.makes_name('div')
            x, y = self.xy_from_data(self.fistafft)
            print "len(x), len(y)  ", len(x), len(y)
            if self.compr :
                print "makes Fista compression for csv."
                y = np.roll(y,1)*1e-20 + y + np.roll(y,-1)*1e-20
                x = x[y != 0.0]
                y = y[y != 0.0]
            self.save_csv(x, y, namecsv, kind = 'fista')

    def save_configfile(self):
        '''
        Saves the configfile with the data.
        The directory with the name of the file is "self.directory_results"
        '''
        path_configfile = os.path.join(os.path.dirname(self.directory_results), 'Applic_Fista_new.mscf')
        print "path_configfile  ", path_configfile 
        print "os.path.dirname(__file__) ", os.path.dirname(__file__)
        print "self.directory_results ", self.directory_results
        if os.path.exists(path_configfile): # If yet a configfile
            shutil.move(path_configfile, self.directory_results)
            print "moved ", path_configfile, "to ", self.directory_results
        else:
            # Takes the address Applic_Fista.mscf at the same level as "Applic_Fista.py"
            path_configfile = os.path.join(os.path.dirname(__file__), 'Applic_Fista.mscf')    
            print "path_configfile is ", path_configfile
            shutil.copy2(path_configfile, self.directory_results)

    def makes_storing_directory(self):
        '''
        Makes the storing directory for the processed files.
        This directory is name with the name of the file to be processed and with the date.
        '''
        if self.addr_data_saved == '':
            self.directory_results = self.param.filename + '_fista_' + datetime()
        else:
            self.directory_results = os.path.join(self.addr_data_saved, os.path.basename(self.param.filename))
        print "results directory is ", self.directory_results
        if not os.path.exists(self.directory_results):
            os.mkdir(self.directory_results)
        self.save_configfile()

    def makecsv(self, dataname, data, namefile):
        '''
        format to enter :  "name 1st col   name 2nd col ", (x, y), namefile
        '''
        output = np.column_stack(data)
        with open(namefile, 'wb') as f:
            f.write(dataname+'\n')
            np.savetxt(f, output, delimiter=',', fmt ='%1.16e')
        print "saved file ", namefile

    def save_csv(self, x, y, namef, kind = ''):
        '''
        Save csv for Fista or truncated fid FFTed.
        '''
        if kind == 'fista' :
            self.makecsv("# mz   fista", (x, y), namef ) # Makes csv file
        if kind == 'fft_div' :
            self.makecsv("# mz   div", (x, y), namef)  # Makes csv file
        if kind == 'ref' :
            self.makecsv("# mz   ref", (x, y), namef ) # Makes csv file

class Test(unittest.TestCase):
    """tests """        
    def test_applic_fista(self):
        "apply a complete processing test"
        main(["Applic_Fista_eg.mscf",])

def message_time():
    print "algo starts at ", datetime()

def main(argv = None):
    "does the whole job"
    message_time()
    ######### read arguments
    if not argv:
        argv = sys.argv
    try:                                                        # First try to read config file from arg list
        configfile = argv[1]
    except IndexError:                                          # then assume standard name
        configfile = "Applic_Fista.mscf"                        # If config file not given takes the local configfile Applic_Fista.mscf
    print "using %s as configuration file" % configfile
    fsup = FISTA_sup(configfile)                                # Using configfile
    fsup.solve_file()                                           # Makes Fista for one file

if __name__ == '__main__':
    main()