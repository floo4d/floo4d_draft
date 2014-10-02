import os

from matplotlib import pyplot as plt

pyside = True

if pyside:
    from PySide.QtGui import QMainWindow, QApplication, QWidget, QToolButton, QAction, QVBoxLayout
    os.environ["QT_API"] = "pyside"
    from PySide import QtCore, QtGui
    from PySide.QtCore  import SIGNAL 
    from PySide.QtCore import QObject as Qobj
else:
    from PyQt4.QtGui import QMainWindow, QApplication, QWidget, QToolButton, QAction, QVBoxLayout
    from PyQt4 import QtCore, QtGui
    from PyQt4.QtCore  import SIGNAL 
    from PyQt4.QtCore import QObject as Qobj
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s
