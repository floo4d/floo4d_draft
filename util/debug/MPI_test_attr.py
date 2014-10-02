# encoding: utf-8
"""
Testing MPI
"""
import sys
sys.path.append('../')
sys.path.append('../util/') # path to mail
import os
import unittest
import time
import util.mpiutil as mpiutil
from util.sendgmail import mail

'''
(mpirun -np N) python  program   configfile.mscf
'''



# default values
if __name__ == '__main__':
    #unittest.main()
    #f = open('debug_process_urqrd.txt','w')
    print "mpiutil.MPI_size ", mpiutil.MPI_size
    print "mpiutil.MPI_rank ", mpiutil.MPI_rank

