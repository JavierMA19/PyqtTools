#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 17:42:36 2019

@author: aguimera
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5.QtWidgets import QFileDialog
import h5py
from PyQt5 import Qt
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt


SaveFilePars = [{'name': 'Save File',
                 'type': 'action'
                 },
                {'name': 'File Path',
                 'type': 'str',
                 'value': ''
                 },
                {'name': 'MaxSize',
                 'type': 'int',
                 'siPrefix': True,
                 'suffix': 'B',
                 'limits': (1e6, 1e12),
                 'step': 100e6,
                 'value': 50e6
                 },
                {'name': 'Enabled',
                 'type': 'bool',
                 'value': False,
                 },
                ]


class SaveFileParameters(pTypes.GroupParameter):
    def __init__(self, QTparent, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.QTparent = QTparent
        self.addChildren(SaveFilePars)
        self.param('Save File').sigActivated.connect(self.FileDialog)

    def FileDialog(self):
        RecordFile, _ = QFileDialog.getSaveFileName(self.QTparent,
                                                    "Recording File",
                                                    "",
                                                    )
        if RecordFile:
            if not RecordFile.endswith('.h5'):
                RecordFile = RecordFile + '.h5'
            self.param('File Path').setValue(RecordFile)

    def FilePath(self):
        return self.param('File Path').value()


class FileBuffer():
    def __init__(self, FileName, MaxSize, nChannels, Fs=None, ChnNames=None):
        self.FileBase = FileName.split('.h5')[0]
        self.PartCount = 0
        self.nChannels = nChannels
        self.MaxSize = MaxSize
        self.Fs = Fs
        self.ChnNames = ChnNames
        self._initFile()

    def _initFile(self):
        if self.MaxSize is not None:
            FileName = '{}_{}.h5'.format(self.FileBase, self.PartCount)
        else:
            FileName = self.FileBase + '.h5'
        self.FileName = FileName
        self.PartCount += 1
        self.h5File = h5py.File(FileName, 'w')
        if self.Fs is not None:
            self.FsDset = self.h5File.create_dataset('Fs', 
                                                     data=self.Fs)
        if self.ChnNames is not None:
            self.ChnNamesDset = self.h5File.create_dataset('ChnNames', 
                                                           dtype='S10',
                                                           data=self.ChnNames)
        
        self.Dset = self.h5File.create_dataset('data',
                                               shape=(0, self.nChannels),
                                               maxshape=(None, self.nChannels),
                                               compression="gzip")

    def AddSample(self, Sample):
        nSamples = Sample.shape[0]
        FileInd = self.Dset.shape[0]
        self.Dset.resize((FileInd + nSamples, self.nChannels))
        self.Dset[FileInd:, :] = Sample
        self.h5File.flush()

        stat = os.stat(self.FileName)
        if stat.st_size > self.MaxSize:
#            print(stat.st_size, self.MaxSize)
            self._initFile()

    def RefreshPlot(self):
        plt.figure()
        x, y = self.Dset.shape
        Time = np.linspace(0, x/self.Fs, x)
        plt.plot(Time, self.Dset)


class DataSavingThread(Qt.QThread):
    def __init__(self, FileName, nChannels, Fs=None, ChnNames=None, 
                 MaxSize=None, dtype='float'):
        super(DataSavingThread, self).__init__()
        self.NewData = None
        self.FileBuff = FileBuffer(FileName=FileName,
                                   nChannels=nChannels,
                                   MaxSize=MaxSize,
                                   Fs=Fs,
                                   ChnNames=ChnNames)

    def run(self, *args, **kwargs):
        while True:
            if self.NewData is not None:
                self.FileBuff.AddSample(self.NewData)
                self.NewData = None
            else:
                Qt.QThread.msleep(10)

    def AddData(self, NewData):
        if self.NewData is not None:
            print('Error Saving !!!!')
        else:
            self.NewData = NewData
    
    def stop (self):
        self.FileBuff.h5File.close()
        self.terminate()



SaveStatePars = [{'name': 'Save State',
                  'type': 'action'},
                 {'name': 'Load State',
                  'type': 'action'},
                ]

class SaveSateParameters(pTypes.GroupParameter):
    def __init__(self, QTparent, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.QTparent = QTparent
        self.addChildren(SaveStatePars)
        self.param('Save State').sigActivated.connect(self.on_Save)
        self.param('Load State').sigActivated.connect(self.on_Load)

    def _GetParent(self):
        parent = self.parent()
#        while parent is None:
#            parent = self.parent()
        return parent

    def on_Load(self):
        parent = self._GetParent()        
        
        RecordFile, _ = QFileDialog.getOpenFileName(self.QTparent,
                                                    "state File",
                                                    "",
                                                   )
        
        if RecordFile:
            with open(RecordFile, 'rb') as file:
                parent.restoreState(pickle.loads(file.read()))

    def on_Save(self):
        parent = self._GetParent()        
        
        RecordFile, _ = QFileDialog.getSaveFileName(self.QTparent,
                                                    "state File",
                                                    "",
                                                   )
        
        if RecordFile:
            with open(RecordFile, 'wb') as file:
                file.write(pickle.dumps(parent.saveState()))


def GenArchivo(name, dic2Save):
    """
    Generate a file of type .dat that saves a dictionary

    Parameters
    ----------
    :param: name: the name the saved file will have
        'name.dat'
    :param: dic2Save: the dictionary is wanted to be saved

    Returns
    -------
        None.
    """
    with open(name, "wb") as f:
        pickle.dump(dic2Save, f)

def ReadArchivo(name):
    """
    Generate a file of type .dat that saves a dictionary

    Parameters
    ----------
    :param: name: the name of the file to open. it is need:
        ·All the directory path if it is on a diferent folder from the script.
        ·The extention of the file

    Returns
    -------
    :return: pickle.load(): returns the read dictionary from file
    """
    with open(name, "rb") as f:
        return pickle.load(f ,encoding = 'latin1')


if __name__ == '__main__':
    import time
    
    
    f = FileBuffer(FileName='test.h5',
                   MaxSize=50e6,
                   nChannels=32)
    
    
    
    samps = np.int64(np.logspace(1, 7, 20))
    
    ts = []
    for s in samps:
        a = np.ones((s, 32))
        Told = time.time()
        f.AddSample(a)       
        ts.append(time.time() - Told)        
        
    print(ts)
    
    plt.plot(samps, ts)
    
    plt.figure()
    plt.plot(samps, samps/ts)
    
    