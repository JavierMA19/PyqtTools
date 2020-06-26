# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 08:17:10 2020

@author: Lucia
"""

import numpy as np
import pickle
from scipy.signal import welch

import pyqtgraph.parametertree.parameterTypes as pTypes

from PyQt5 import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog

import PyGFETdb.DataStructures as PyData
import PyqtTools.PlotModule as PltBuffer2D

################PARAMETER TREE################################################

ConfigSweepsParams = {'name': 'SweepsConfig',
                      'type': 'group',
                    'children': ({'name': 'Start/Stop Sweep',
                                  # 'title': 'Start Sweep',
                                  'type': 'action', },
                                 {'name': 'Pause/ReStart Sweep',
                                  # 'title': 'Start Sweep',
                                  'type': 'action', },
                                 {'name': 'ACenable',
                                  'title': 'AC Characterization',
                                  'type': 'bool',
                                  'value': True, },
                                 {'name': 'VgSweep',
                                          'type': 'group',
                                          'children': ({'name': 'Vinit',
                                                        'type': 'float',
                                                        'value': 0,
                                                        'siPrefix': True,
                                                        'suffix': 'V'},
                                                       {'name': 'Vfinal',
                                                        'type': 'float',
                                                        'value': -0.4,
                                                        'siPrefix': True,
                                                        'suffix': 'V'},
                                                       {'name': 'NSweeps',
                                                        'type': 'int',
                                                        'value': 1,
                                                        'siPrefix': True,
                                                        'suffix': 'Sweeps'},
                                                       )},
                                 {'name': 'VdSweep',
                                  'type': 'group',
                                  'children': ({'name': 'Vinit',
                                                'type': 'float',
                                                'value': 0.02,
                                                'siPrefix': True,
                                                'suffix': 'VRMS'},
                                               {'name': 'Vfinal',
                                                'type': 'float',
                                                'value': 0.2,
                                                'siPrefix': True,
                                                'suffix': 'VRMS'},
                                               {'name': 'NSweeps',
                                                'type': 'int',
                                                'value': 1,
                                                'siPrefix': True,
                                                'suffix': 'Sweeps'},
                                               )},
                                 {'name': 'MaxSlope',
                                  'title': 'Maximum Slope',
                                  'type': 'float',
                                  'value': 1e-10},
                                 {'name': 'TimeOut',
                                  'title': 'Max Time for Stabilization',
                                  'type': 'int',
                                  'value': 10,
                                  'siPrefix': True,
                                  'suffix': 's'},
                                 {'name': 'TimeBuffer',
                                  'title': 'Buffer Time for Stabilization',
                                  'type': 'int',
                                  'value': 1,
                                  'siPrefix': True,
                                  'suffix': 's'},
                                 )}

SaveSweepsParams = ({'name': 'SaveSweepConfig',
                    'type': 'group',
                    'children': ({'name': 'Save File',
                                  'type': 'action'},
                                 {'name': 'Folder',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Oblea',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Disp',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Name',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Cycle',
                                  'type': 'int',
                                  'value': 0},
                                 )
                    })

class SweepsConfig(pTypes.GroupParameter):
    def __init__(self, QTparent, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.QTparent = QTparent
        
        self.addChild(ConfigSweepsParams)
        self.SwConfig = self.param('SweepsConfig')

        self.VgParams = self.SwConfig.param('VgSweep')
        self.VdParams = self.SwConfig.param('VdSweep')

        self.VgParams.sigTreeStateChanged.connect(self.on_Sweeps_Changed)
        self.VdParams.sigTreeStateChanged.connect(self.on_Sweeps_Changed)
        self.on_Sweeps_Changed()
        
        self.addChild(SaveSweepsParams)
        self.SvSwParams = self.param('SaveSweepConfig')
        self.SvSwParams.param('Save File').sigActivated.connect(self.FileDialog)

    def on_Sweeps_Changed(self):
        self.VgSweepVals = np.linspace(self.VgParams.param('Vinit').value(),
                                       self.VgParams.param('Vfinal').value(),
                                       self.VgParams.param('NSweeps').value())

        self.VdSweepVals = np.linspace(self.VdParams.param('Vinit').value(),
                                       self.VdParams.param('Vfinal').value(),
                                       self.VdParams.param('NSweeps').value())

    def FileDialog(self):
        RecordFile = QFileDialog.getExistingDirectory(self.QTparent,
                                                      "Select Directory",
                                                      )
        if RecordFile:
            self.SvSwParams.param('Folder').setValue(RecordFile)

    def FilePath(self):
        return self.param('Folder').value()
    
    def GetConfigSweepsParams(self):
        '''Returns de parameters to do the sweeps
           SwConfig={'Enable': True,
                     'VgSweep': array([ 0. , -0.1, -0.2, -0.3]),
                     'VdSweep': array([0.1]),
                     'MaxSlope': 1e-10,
                     'TimeOut': 10
                     }
        '''
        SwConfig = {}
        for Config in self.SwConfig.children():
            if Config.name() == 'Start/Stop Sweep':
                continue
            if Config.name() == 'Pause/ReStart Sweep':
                continue
            if Config.name() == 'VgSweep':
                SwConfig[Config.name()] = self.VgSweepVals
                continue
            if Config.name() == 'VdSweep':
                SwConfig[Config.name()] = self.VdSweepVals
                continue
            SwConfig[Config.name()] = Config.value()
        return SwConfig
    
    def GetSaveSweepsParams(self):
        '''Returns de parameters to save the caracterization
           Config={'Folder': 'C:/Users/Lucia/Dropbox (ICN2 AEMD - GAB GBIO)/
                              TeamFolderLMU/FreqMux/Lucia/DAQTests/SweepTests
                              /18_12_19',
                   'Oblea': 'testPyCont',
                   'Disp': 'Test',
                   'Name': 'Test',
                   'Cycle': 0
                   }
        '''
        Config = {}
        for Conf in self.SvSwParams.children():
            if Conf.name() == 'Save File':
                continue
            Config[Conf.name()] = Conf.value()
        print('ConfigSave', Config)
        return Config  

################CHARACTERIZATION THREAD#######################################
        
class StbDetThread(Qt.QThread):
    NextVg = Qt.pyqtSignal()
    NextVd = Qt.pyqtSignal()
    CharactEnd = Qt.pyqtSignal()

    def __init__(self, ACenable, VdSweep, VgSweep, MaxSlope, TimeOut, TimeBuffer, 
                 nChannels, ChnName, PlotterDemodKwargs, **kwargs):
        '''Initialization for Stabilitation Detection Thread
           VdVals: Array. Contains the values to use in the Vd Sweep.
                          [0.1, 0.2]
           VgVals: Array. Contains the values to use in the Vg Sweep
                          [0., -0.1, -0.2, -0.3]
           MaxSlope: float. Specifies the maximum slope permited to consider
                            the system is stabilazed, so the data is correct
                            to be acquired
           TimeOut: float. Specifies the maximum amount of time to wait the
                           signal to achieve MaxSlope, if TimeOut is reached
                           the data is save even it is not stabilazed
           nChannels: int. Number of acquisition channels (rows) active
           ChnName: dictionary. Specifies the name of Row+Column beign
                                processed and its index:
                                {'Ch04Col1': 0,
                                'Ch05Col1': 1,
                                'Ch06Col1': 2}
           PlotterDemodKwargs: dictionary. Contains Demodulation Configuration
                                           an parameters
                                           {'Fs': 5000.0,
                                           'nFFT': 8.0,
                                           'scaling': 'density',
                                           'nAvg': 50 }
        '''
        super(StbDetThread, self).__init__()
        self.threadCalcPSD = None
        self.ToStabData = None
        self.Stable = False
        self.Datos = None
        
        self.ACenable = ACenable
        self.MaxSlope = MaxSlope
        self.TimeOut = TimeOut

        self.VgIndex = 0
        self.VdIndex = 0
        self.VgSweepVals = VgSweep
        self.VdSweepVals = VdSweep
        self.NextVgs = self.VgSweepVals[self.VgIndex]
        self.NextVds =self.VdSweepVals[self.VdIndex]

        self.Timer = Qt.QTimer()
        self.Timer.timeout.connect(self.printTime)

        self.Buffer = PltBuffer2D.Buffer2D(PlotterDemodKwargs['Fs'],
                                           nChannels,
                                           TimeBuffer)
        
        self.SaveDCAC = SaveDicts(ACenable=self.ACenable,
                                  SwVdsVals=VdSweep,
                                  SwVgsVals=VgSweep,
                                  Channels=ChnName,
                                  nFFT=int(PlotterDemodKwargs['nFFT']),
                                  FsDemod=PlotterDemodKwargs['Fs']
                                  )
        if self.ACenable:
            self.threadCalcPSD = CalcPSD(nChannels=nChannels,
                                         **PlotterDemodKwargs)
            self.threadCalcPSD.PSDDone.connect(self.on_PSDDone)
            self.SaveDCAC.PSDSaved.connect(self.on_NextVgs)
            
        else:
            self.SaveDCAC.DCSaved.connect(self.on_NextVgs)

    def run(self):
        while True:
            if self.Buffer.IsFilled():
                Data = self.Buffer
                ChnInd = 0
                Dev = np.ndarray((Data.shape[1],))
                for ChnInd, dat in enumerate(Data.transpose()):
                    r = len(dat)
                    x = np.arange(0, r)
                    mm, oo = np.polyfit(x, dat, 1)
                    Dev[ChnInd] = np.abs(np.mean(mm))
                    if Dev[ChnInd] > self.MaxSlope:
                        print('ChnInd', ChnInd)
                        print('Slope Calc -->', Dev)
                
                for slope in Dev:
                    if slope < self.MaxSlope:
                        print('Final slope is -->', Dev)
                        self.Timer.stop()
                        # self.Timer.timeout.disconnect(self.printTime)
                        self.DCIdCalc()
                        break

                self.Buffer.Reset()

            else:
                Qt.QThread.msleep(10)


    def AddData(self, NewData):
        if self.Stable is False:
            self.Buffer.AddData(NewData)
            self.Datos = self.Buffer  # se guardan los datos para que no se sobreescriban
        if self.ACenable:
            if self.Stable is True:
                self.threadCalcPSD.AddData(NewData)

    def printTime(self):
        print('TimeOut')
        self.Timer.stop()
        # self.Timer.timeout.disconnect(self.printTime)
        self.DCIdCalc()

    def DCIdCalc(self):
        self.Buffer.Reset()
        # se activa el flag de estable
        self.Stable = True
        # se activa el thread para calcular PSD
        if self.ACenable:
            self.threadCalcPSD.start()
        # se obtiene el punto para cada Row
        self.DCIds = np.ndarray((self.Datos.shape[1], 1))
        for ind in range(self.Datos.shape[1]):
            Data = np.abs(self.Datos[:, ind])
            x = np.arange(Data.size)
            self.ptrend = np.polyfit(x, Data, 1)

            self.DCIds[ind] = (self.ptrend[-1])  # Se toma el ultimo valor
        
        # Se guardan los valores DC
        self.SaveDCAC.SaveDCDict(Ids=self.DCIds,
                                 SwVgsInd=self.VgIndex,
                                 SwVdsInd=self.VdIndex)    

    def on_PSDDone(self):
        self.freqs = self.threadCalcPSD.ff
        self.PSDdata = self.threadCalcPSD.psd
        # se desactiva el thread para calcular PSD
        self.threadCalcPSD.stop()
        
        # Se guarda en AC dicts
        self.SaveDCAC.SaveACDict(psd=self.PSDdata,
                                 ff=self.freqs,
                                 SwVgsInd=self.VgIndex,
                                 SwVdsInd=self.VdIndex
                                 )

    def on_NextVgs(self):
        self.Stable = False
        self.VgIndex += 1
        if self.VgIndex < len(self.VgSweepVals):
            self.NextVgs = self.VgSweepVals[self.VgIndex]
            print(self.VgIndex)
            self.NextVg.emit()
        else:
            self.VgIndex = 0
            self.NextVgs = self.VgSweepVals[self.VgIndex]
            self.on_NextVds()

    def on_NextVds(self):
        self.VdIndex += 1
        
        if self.VdIndex < len(self.VdSweepVals):
            self.NextVds = self.VdSweepVals[self.VdIndex]
            print(self.VdIndex)
            self.NextVd.emit()

        else:
            self.VdIndex = 0
            self.NextVds = self.VdSweepVals[self.VdIndex]
            self.DCDict = self.SaveDCAC.DevDCVals
            if self.ACenable:
                self.ACDict = self.SaveDCAC.DevACVals
            else:
                self.ACDict = None
            self.CharactEnd.emit()
        
            
    def stop(self):
        # self.SaveDCAC.DCSaved.disconnect()
        if self.threadCalcPSD is not None:
            self.SaveDCAC.PSDSaved.disconnect()
            self.threadCalcPSD.PSDDone.disconnect()
            self.threadCalcPSD.stop()
        self.terminate()
        
################CALC PSD THREAD###############################################
        
class CalcPSD(Qt.QThread):
    PSDDone = Qt.pyqtSignal()
    def __init__(self, Fs, nFFT, nAvg, nChannels, scaling):
        '''Initialization of the thread that is used to calculate the PSD
           Fs: float. Sampling Frequency
           nFFT: float.
           nAvg: int.
           nChannels: int. Number of acquisition channels (rows) active
           scaling: str. Two options, Density or Spectrum
        '''
        super(CalcPSD, self).__init__()

        self.scaling = scaling
        self.nFFT = 2**nFFT
        self.nChannels = nChannels
        self.Fs = Fs
        self.BufferSize = self.nFFT * nAvg
        self.Buffer = PltBuffer2D.Buffer2D(self.Fs, self.nChannels,
                                           self.BufferSize/self.Fs)

    def run(self, *args, **kwargs):
        while True:
            if self.Buffer.IsFilled():
                self.ff, self.psd = welch(self.Buffer,
                                          fs=self.Fs,
                                          nperseg=self.nFFT,
                                          scaling=self.scaling,
                                          axis=0)
#                print('PSD DONE EMIT')
                self.Buffer.Reset()
                self.PSDDone.emit()

            else:
                Qt.QCoreApplication.processEvents()
                Qt.QThread.msleep(200)

    def AddData(self, NewData):
        self.Buffer.AddData(NewData)

    def stop(self):
        self.Buffer.Reset()
        self.terminate()

################SAVE CHARACTERIZATION DICTs###################################
        
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
                               
                            }
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