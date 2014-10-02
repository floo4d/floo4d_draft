'''
Created by Lionel Chiron  02/10/2013 
Copyright (c) 2013 __NMRTEC__. All rights reserved.
'''
import os,sys
os.environ["QT_API"] = "pyside"
from  InterfProc.interface import interf
from InterfProc.interface_actions import interact

'''
Fista interface.
'''
def run(namef = None):
    
    interface = interf()        # instantiates the interface
    inter = interact(interface) # interaction of the interface with orbitrap library
    interface.run()             # launches the interface. 

if __name__ == '__main__':
    run()
