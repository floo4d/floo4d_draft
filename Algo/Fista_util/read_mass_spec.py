from util.debug_tools import*  
import File.Apex as Apex
import numpy as np
from NPKData import NPKData, as_cpx
import re
from Orbitrap import OrbiData
from FTICR import FTICRData

@decclassdebugging                               
class FTICR_treat():
    def __init__(self, addr_save ):
        self.addr_save = addr_save
    
    def read(self, add):
        '''
        Reads Apex or msh5 files. If Apex is used makes locally a corersponding msh5.
        '''
        print "path exists? ",os.path.exists(add)
        nameroot = os.path.basename(add).split(".")[0]
        splitadd = os.path.splitext(add)
        ext = splitadd[-1]
        if ext == '.d' and not os.path.exists(splitadd[0]+".msh5"):
            if self.addr_save:
                print "makes msh5 from Apex file "
                filemsh5 = os.path.join(self.addr_save, nameroot+'.msh5') # name for saving file
            else :
                filemsh5 = ''
            data = Apex.Import_1D(add, filemsh5)
            if self.addr_save:
                f = data.hdf5file
                f.close()
        elif ext == '.msh5' or os.path.exists(splitadd[0]+".msh5"):
            filemsh5 = nameroot+'.msh5'
        else : 
            print "Unknown format"
        if ext == '.d' or ext == '.msh5':
            if filemsh5:
                data = FTICRData(name = filemsh5) # open the msh5 file
        else:
            data = None
        return data

    def xymz(self, datafticr, specfreq, mzmax, resol = 1):
        '''
        transformation for plotting in m/z
        specmzindex  contains the m/z values, x axis
        specmz the corresponding values, y axis
        datafticr (DataFTICR format) is used for recuperating itomz
        '''
        print "in xymz "
        specmz = specfreq
        print "specfreq.size ",specfreq.size
        specmzindex = np.zeros(specfreq.size-1) # initialization
        if resol != 1 : 
            print "superresolution"
        for i in range(1, specmzindex.size): # Super resolution size in case of super resol.. 
            mzval = datafticr.axes(1).itomz(i)
            if resol != 1 : 
                mzcorrect = datafticr.axes(1).itomz(i/float(resol))
                specmzindex[i-1] =  mzcorrect
            else :
                specmzindex[i-1] =  mzval
        print "specmzindex[specmzindex < mzmax]",specmzindex[specmzindex < mzmax]
        indexmz = np.where(specmzindex < mzmax)[0]
        yspecmz  = specmz[1:][indexmz]
        xmz = specmzindex[indexmz]
        yspecmz[np.where(xmz < 300)[0]] = 0 
        return xmz, yspecmz

@decclassdebugging                               
class Orbitrap_treat():
    def __init__(self):
        self.refnorm = 1
        self.refresol = 1
    
    def find_range(self,f):
        '''
        Calculate factor self.range_fact in function of the masss range.
        '''
        a = os.path.basename(f)
        try:
            result = int(re.search('range(\d*)-.*', a).group(1))
            print "result is ", result
            if result <= 100 :
                self.range_fact = 1
            else:
                self.range_fact = 0.5 
        except Exception:
            self.range_fact = 0.5    

    def read(self, f):
        """
        reads Orbitrap .dat FID files
        returns a numpy array with the FID
        """
        print "f ", f
        self.find_range(f)
        with open(f,'rb') as F:
            pos = 0
            for l in F:
                pos += len(l)
                if l.startswith("Data Points"):
                    print re.findall(r'\d+', l)[0]
                if l.startswith("Data:"):
                    break
            F.seek(pos)
            data_interm = np.array(np.fromfile(F, dtype = 'f4').tolist())  # ndarray to list to np.array
            data = OrbiData(buffer = data_interm )
            
        return data
         
    def mzshow(self, spec, col = 'k', linestyle ='-'):
        '''
        print spectrum in m/z
        '''
        print "spec.size",spec.size
        point_ref = spec.size*377500./(2*999982)
        print "point_ref ",point_ref
        mz_ref = 715.3122
        trunc = 0.1 * spec.size
        xaxis = mz_ref/(((1 + np.arange(1.0 * spec.size))/point_ref)**2)
        plt.plot(xaxis[trunc:], spec[trunc:], color = col, linestyle = linestyle)
        
    def zerfapod(self, data, zerofill = False):
        '''
        Zerofilling and apodisation
        '''
        print "self.refresol ",self.refresol
        #apod = apod_sq_sin
        #apod = apod_sin
        if zerofill :
            spec = data.apod_sq_sin(maxi = 0.5).chsize(self.refresol).rfft().modulus().buffer
        else :
            spec = data.apod_sq_sin(maxi = 0.5).rfft().modulus().buffer
        print "spec.size",spec.size
        return spec
    
    def xymz(self, y):
        '''
        Prepare data for orbitrap m/z unit.
        '''
        mz_ref = 715.3122 # reference mass
        trunc_deb = 0.1
        data_size = y.size
        point_ref = data_size * 377500./(2*999982)
        trunc = trunc_deb * data_size
        xaxis = mz_ref/(((1 + np.arange(1.0*data_size)*self.range_fact)/point_ref)**2)
        xmz = xaxis[trunc:]
        yspecmz =  y[trunc:]
        print "xmz, yspecmz ", xmz, yspecmz
        return xmz, yspecmz
