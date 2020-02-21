# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 14:37:00 2019

@author: Lucia
"""
import numpy as np
from PyQt5 import Qt
from PyQt5.QtCore import QObject
import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5.QtWidgets import QFileDialog
from pyqtgraph.parametertree import Parameter

import PyGFETdb.DataStructures as PyData
import deepdish as dd
import h5py
import pickle

################################PRAMETERES TREE################################

SaveSweepParams = ({'name': 'SaveSweepConfig',
                    'type': 'group',
                    'children': ({'name': 'Save File',
                                 'type': 'action'},
                                  {'name': 'Folder',
                                   'type': 'str',
                                   'value': ''},
                                 # {'name': 'Oblea',
                                 #  'type': 'str',
                                 #  'value': ''},
                                 # {'name': 'Disp',
                                 #  'type': 'str',
                                 #  'value': ''},
                                 {'name': 'Name',
                                  'type': 'str',
                                  'value': ''},
                                 # {'name': 'Cycle',
                                 #  'type': 'int',
                                 #  'value': 0},
                                  )
                    })


class SaveSweepParameters(pTypes.GroupParameter):

    def __init__(self, QTparent, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.QTparent = QTparent
        self.addChild(SaveSweepParams)
        self.SvSwParams = self.param('SaveSweepConfig')
        self.SvSwParams.param('Save File').sigActivated.connect(self.FileDialog)

    def FileDialog(self):
        RecordFile = QFileDialog.getExistingDirectory(self.QTparent,
                                                      "Select Directory",
                                                      )
        if RecordFile:
            self.SvSwParams.param('Folder').setValue(RecordFile)

    def GetParams(self):
        Config = {}
        for Conf in self.SvSwParams.children():
            print(Conf, self.SvSwParams.children())
            if Conf.name() == 'Save File':
                continue
            Config[Conf.name()] = Conf.value()
        return Config

    def FilePath(self):
        return self.param('Folder').value()


###################################CLASS#########################################    


class SaveDicts(QObject):

    PSDSaved = Qt.pyqtSignal()

    def __init__(self, SwVdsVals, SwVgsVals, Channels, nFFT, FsDemod, Gate=False):
       super(SaveDicts, self).__init__()
       self.ChNamesList = sorted(Channels)
       self.ChannelIndex = {}
       index = 0
       for ch in sorted(Channels):
           self.ChannelIndex[ch] = (index)

        # DC dictionaries
       self.DevDCVals = PyData.InitDCRecord(nVds=SwVdsVals,
                                            nVgs=SwVgsVals,
                                            ChNames=self.ChNamesList,
                                            Gate=Gate)
        # AC dictionaries
       self.DevACVals = None
        # if checkPSD:
       # self.PSDnFFT = 2**nFFT
       # self.PSDFs = FsDemod
        
       # Fpsd = np.fft.rfftfreq(self.PSDnFFT, 1/self.PSDFs)
       # nFgm = np.array([])
       # self.DevACVals = PyData.InitACRecord(nVds=SwVdsVals,
       #                                       nVgs=SwVgsVals,
       #                                       nFgm=nFgm,
       #                                       nFpsd=Fpsd,
       #                                       ChNames=self.ChNamesList)
        
        
    def SaveDCDict(self, Ids, SwVgsInd, SwVdsInd):
       for chn, inds in self.ChannelIndex.items():
           self.DevDCVals[chn]['Ids'][SwVgsInd,
                                      SwVdsInd] = Ids[inds]
  
       print('DCSaved')
       self.PSDSaved.emit()

    def SaveACDict(self, psd, ff, SwVgsInd, SwVdsInd):
       for chn, inds in self.ChannelIndex.items():
           self.DevACVals[chn]['PSD']['Vd{}'.format(SwVdsInd)][
                   SwVgsInd] = psd[:, inds].flatten()
           self.DevACVals[chn]['Fpsd'] = ff
       print('ACSaved')
       self.PSDSaved.emit()

    def SaveDicts(self, Dcdict, Acdict, Folder, Name):
                # self.FileName = '{}/{}-{}-{}-Cy{}.h5'.format(Folder,
                #                                      Oblea,
                #                                      Disp,
                #                                      Name,
                #                                      Cycle)

       if Name:
           Filename = Folder + '/' + Name + "{}-Cy{}.h5".format('', 0)
           if Acdict:
               dd.io.save(Filename, (Dcdict, Acdict), ('zlib', 1))
           else:
               dd.io.save(Filename, Dcdict, ('zlib', 1))

       # self.NextCycle()
       # with open(self.FileName, "wb") as f:
       #     pickle.dump(Dcdict, f)
       #     pickle.dump(Acdict, f)