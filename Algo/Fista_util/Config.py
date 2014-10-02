'''
Created by Lionel Chiron  03/12/2013
Copyright (c) 2013 __NMRTEC__. All rights reserved.
'''
from NPKConfigParser import NPKConfigParser
import re, os, sys

class Proc_Parameters(object):
    """this class is a container for applying Fista"""
    def __init__(self, configfile = None):
        "initialisation"
        # 
        self.do_fista = True
        self.fid_length_div_by = 8
        self.superresol = 8
        self.divide_lambda = 1
        self.apod_fista = False
        self.multiproc = True
        self.zerofill_ref = 2
        self.save_ref_spec = True
        self.save_fista_spec = True
        self.save_fft_div = True
        self.save_date = True
        self.first_point_trunc_fid = 100000
        self.show_truncated_fid = False
        self.addr_sampling = ''
        self.data_sampled = False
        if configfile:
            self.load(configfile)
            
    def load(self, cp):
        "load from cp config file - should have been opened with ConfigParser() first"
        ###
        self.npk_dir =  cp.get( "config", "npk_dir")        # directory of NPKv2
        ### processed addresses.
        self.file_to_treat =  cp.get( "data", "file_to_treat")        # input file
        self.filename, self.ext = os.path.splitext(self.file_to_treat)
        ### Fista
        self.do_fista = cp.getboolean( "fista", "do_fista", str(self.do_fista))                                 # do_fista
        self.multiproc = cp.getboolean( "fista", "multiproc", str(self.multiproc))                              # multiprocessing
        self.show_truncated_fid = cp.getboolean( "fista", "show_truncated_fid", str(self.show_truncated_fid))   # show the Truncated Fid before processing.
        self.first_point_trunc_fid = cp.getint( "fista", "first_point_trunc_fid", self.first_point_trunc_fid)   # first point at which the Fid is truncated.
        self.fid_length_div_by = cp.getint( "fista", "fid_length_div_by", self.fid_length_div_by)               # factor of truncation of the Fid.
        self.divide_lambda = cp.getfloat( "fista", "divide_lambda", self.divide_lambda)                         # lambda parameter for Fista.
        self.apod_fista = cp.getboolean( "fista", "apod_fista", self.apod_fista)                                # apodisation for Fista.
        self.superresol = cp.getint( "fista", "superresol", self.superresol)                                    # superresolution factor.
        self.zerofill_ref = cp.getint( "fista", "zerofill_ref", self.zerofill_ref)                              # zeroffiling for the reference Fid.
        self.addr_sampling = cp.get( "fista", "addr_sampling", self.addr_sampling)                              # address of the sampling file
        self.data_sampled = cp.getboolean( "fista", "data_sampled", self.data_sampled)                          # flag to indicate if the file is sampled or not.
        ### Store
        self.save_ref_spec = cp.getboolean( "store", "save_ref_spec", str(self.save_ref_spec))                  # saves thre reference spectrum.
        self.save_fista_spec = cp.getboolean( "store", "save_fista_spec", str(self.save_fista_spec))            # saves spectrum obtained with Fista.
        self.save_fft_div = cp.getboolean( "store", "save_fft_div", str(self.save_fft_div))                     # saves the size reduced fist corresponding spectrum.
        self.save_date = cp.getboolean( "store", "save_date", str(self.save_date))                              # saves the date of processing.
        self.addr_data_saved =  cp.get( "store", "addr_data_saved")                                             # address for saving data.
        
    def report(self):
        "print a formatted report"
        print "------------ processing parameters ------------------"
        for i in dir(self):
            if not i.startswith('_'):
                v = getattr(self,i)
                if not callable(v):
                    print i, ' :', v
        print "-----------------------------------------------------"
        
def config_fista(configfile = "Applic_Fista.mscf"):
    #### get parameters from configuration file - store them in a parameter object
    cp = NPKConfigParser()
    cp.readfp(open(configfile))
    print "reading config file"
    param = Proc_Parameters(cp)
    return param