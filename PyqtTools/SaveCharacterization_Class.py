# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 11:58:22 2020

@author: lucia
"""

import numpy as np
import pickle

from PyQt5 import Qt
from PyQt5.QtCore import QObject

import PyGFETdb.DataStructures as PyData

class SaveDicts(QObject):
    PSDSaved = Qt.pyqtSignal()
    DCSaved = Qt.pyqtSignal()

    def __init__(self, SwVdsVals, SwVgsVals, Channels,
                 nFFT, FsDemod, Gate=False, ACenable=True):
        '''Initialize the Dictionaries to Save the Characterization
           SwVdsVals: array. Contains the values for the Vd sweep
                             [0.1, 0.2]
           SwVgsVals: array. Contains the values for the Vg sweep
                             [ 0.,  -0.1, -0.2, -0.3]
           Channels: dictionary. Contains the names from each demodulated
                                 channel and column and its index
                                 {'Ch04Col1': 0, 'Ch05Col1': 1, 'Ch06Col1': 2}
           nFFT: int.
                   8
           FsDemod: float. Sampling Frequency used in the Demodulation Process
                           5000.0
        '''
        super(SaveDicts, self).__init__()
        self.ChNamesList = sorted(Channels)
        self.ChannelIndex = {}

        index = 0
        for ch in sorted(Channels):
            self.ChannelIndex[ch] = (index)
            index = index+1

        self.DevDCVals = PyData.InitDCRecord(nVds=SwVdsVals,
                                             nVgs=SwVgsVals,
                                             ChNames=self.ChNamesList,
                                             Gate=Gate)
        # AC dictionaries
        if ACenable:
            self.PSDnFFT = 2**nFFT
            self.PSDFs = FsDemod
    
            Fpsd = np.fft.rfftfreq(self.PSDnFFT, 1/self.PSDFs)
            nFgm = np.array([])
    
            self.DevACVals = PyData.InitACRecord(nVds=SwVdsVals,
                                                 nVgs=SwVgsVals,
                                                 nFgm=nFgm,
                                                 nFpsd=Fpsd,
                                                 ChNames=self.ChNamesList)

    def SaveDCDict(self, Ids, SwVgsInd, SwVdsInd):
        '''Function that Saves Ids Data in the Dc Dict in the appropiate form
           for database
           Ids: array. Contains all the data to be saved in the DC dictionary
           SwVgsInd: int. Is the index of the actual Vg Sweep Iteration
           SwVdsInd: int. Is the Index of the actual Vd Sweep iteration
        '''
        for chn, inds in self.ChannelIndex.items():
            self.DevDCVals[chn]['Ids'][SwVgsInd,
                                       SwVdsInd] = Ids[inds]
        self.DCSaved.emit()

        # print('DCSaved')

    def SaveACDict(self, psd, ff, SwVgsInd, SwVdsInd):
        '''Function that Saves PSD Data in the AC Dict in the appropiate form
           for database
           psd: array(matrix). Contains all the PSD data to be saved in the AC
                               dictionary
           ff: array. Contains the Frequencies of the PSD to be saved in the AC
                      dictionary
           SwVgsInd: int. Is the index of the actual Vg Sweep Iteration
           SwVdsInd: int. Is the Index of the actual Vd Sweep iteration
        '''
        for chn, inds in self.ChannelIndex.items():
            self.DevACVals[chn]['PSD']['Vd{}'.format(SwVdsInd)][
                    SwVgsInd] = psd[:, inds].flatten()
            self.DevACVals[chn]['Fpsd'] = ff
       
        self.PSDSaved.emit()

    def SaveDicts(self, Dcdict, Folder, Oblea, Disp, Name, Cycle, Acdict=None):
        '''Creates the appropiate Folder NAme to be upload to the database
           Dcdict: dictionary. Dictionary with DC characterization that has
                               the structure to be read and save correctly
                               in the database
                               {'Ch04Col1': {'Ids': array([[1.94019351e-02],
                                                           [5.66072141e-08],
                                                           [5.66067698e-08],
                                                           [5.65991858e-08]
                                                           ]),
                                             'Vds': array([0.1]),
                                             'Vgs': array([ 0. , -0.1,
                                                           -0.2, -0.3]),
                                             'ChName': 'Ch04Col1',
                                             'Name': 'Ch04Col1',
                                             'DateTime': datetime.datetime
                                                         (2019, 12, 19, 16, 20,
                                                         59, 52661)
                                             },
                               'Ch05Col1': {'Ids': array([[1.94019351e-02],
                                                          [5.66072141e-08],
                                                          [5.66067698e-08],
                                                          [5.65991858e-08]
                                                          ]),
                                            'Vds': array([0.1]),
                                            'Vgs': array([ 0. , -0.1,
                                                          -0.2, -0.3]),
                                            'ChName': 'Ch05Col1',
                                            'Name': 'Ch05Col1',
                                            'DateTime': datetime.datetime
                                                        (2019, 12, 19, 16, 20,
                                                        59, 52661)
                                            },
                               }
           Acdict: dictionary. Dictionary with AC characterization that has the
                               structure to be read and save correctly in the
                               database
                               {'Ch04Col1': {'PSD': {'Vd0': array([
                                                            [4.67586928e-26,
                                                            1.61193712e-25],
                                                            ...
                                                            [5.64154950e-26,
                                                            2.10064857e-25]
                                                                   ])
                                                    },
                                             'gm': {'Vd0': array([],
                                                                 shape=(4, 0),
                                                                 dtype=complex128
                                                                 )
                                                    },
                                             'Vgs': array([ 0. , -0.1,
                                                           -0.2, -0.3]),
                                             'Vds': array([0.1]),
                                             'Fpsd': array([   0., 19.53125,
                                                            ...  2500.]),
                                             'Fgm': array([], dtype=float64),
                                             'ChName': 'Ch04Col1',
                                             'Name': 'Ch04Col1',
                                             'DateTime': datetime.datetime
                                                         (2019, 12, 19, 16, 20,
                                                         59, 52661)
                                             },
                               'Ch05Col1': {'PSD': {'Vd0': array([
                                                           [4.67586928e-26,
                                                           1.61193712e-25],
                                                           ...
                                                           [5.64154950e-26,
                                                           2.10064857e-25]
                                                                  ])
                                                    },
                                             'gm': {'Vd0': array([],
                                                                 shape=(4, 0),
                                                                 dtype=complex128
                                                                 )
                                                    },
                                             'Vgs': array([ 0. , -0.1,
                                                           -0.2, -0.3]),
                                             'Vds': array([0.1]),
                                             'Fpsd': array([   0., 19.53125,
                                                            ...  2500.]),
                                             'Fgm': array([], dtype=float64),
                                             'ChName': 'Ch05Col1',
                                             'Name': 'Ch05Col1',
                                             'DateTime': datetime.datetime
                                                         (2019, 12, 19, 16, 20,
                                                         59, 52661)
                                             },
           Folder, Oblea, Disp, Name, Cycle: str.
        '''
        self.FileName = '{}/{}-{}-{}-Cy{}.h5'.format(Folder,
                                                     Oblea,
                                                     Disp,
                                                     Name,
                                                     Cycle)
#        print(self.FileName)
        with open(self.FileName, "wb") as f:
            pickle.dump(Dcdict, f)
            if Acdict is not None:
                pickle.dump(Acdict, f)
        print('Saved')
        