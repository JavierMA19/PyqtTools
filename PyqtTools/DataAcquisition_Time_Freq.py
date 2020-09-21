# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 09:02:01 2020

@author: Lucia
"""

from PyQt5 import Qt

import numpy as np

import Pyxi.FMAcqCore_Time_Freq as CoreMod

# estoy habrá que improtarlo de otra manera
aiChannels = {'Ch09': ('ai0', 'ai8'),
              'Ch10': ('ai1', 'ai9'),
              'Ch11': ('ai2', 'ai10'),
              'Ch12': ('ai3', 'ai11'),
              'Ch13': ('ai4', 'ai12'),
              'Ch14': ('ai5', 'ai13'),
              'Ch15': ('ai6', 'ai14'),
              'Ch16': ('ai7', 'ai15'),
              'Ch01': ('ai16', 'ai24'),
              'Ch02': ('ai17', 'ai25'),
              'Ch03': ('ai18', 'ai26'),
              'Ch04': ('ai19', 'ai27'),
              'Ch05': ('ai20', 'ai28'),
              'Ch06': ('ai21', 'ai29'),
              'Ch07': ('ai22', 'ai30'),
              'Ch08': ('ai23', 'ai31'),
              }
DOChannels = ['port0/line0:15', ]

DOChannels = ['port0/line0:9', ]

aoChannels = ['ao1', 'ao0']

SampSettingConf = ({'title': 'Channels Config',
                    'name': 'ChsConfig',
                    'type': 'group',
                    'children': ({'title': 'Acquire DC',
                                  'name': 'AcqDC',
                                  'type': 'bool',
                                  'value': True},
                                 {'title': 'Acquire AC',
                                  'name': 'AcqAC',
                                  'type': 'bool',
                                  'value': False},
                                 {'title': 'Acquire DC and AC',
                                  'name': 'AcqDCAC',
                                  'type': 'bool',
                                  'value': False},
                                 {'tittle': 'Channels',
                                  'name': 'Channels',
                                  'type': 'group',
                                  'children': ({'name': 'Ch01',
                                                'tip': 'Ch01',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch02',
                                                'tip': 'Ch02',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch03',
                                                'tip': 'Ch03',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch04',
                                                'tip': 'Ch04',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch05',
                                                'tip': 'Ch05',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch06',
                                                'tip': 'Ch06',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch07',
                                                'tip': 'Ch07',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch08',
                                                'tip': 'Ch08',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch09',
                                                'tip': 'Ch09',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch10',
                                                'tip': 'Ch10',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch11',
                                                'tip': 'Ch11',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch12',
                                                'tip': 'Ch12',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch13',
                                                'tip': 'Ch13',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch14',
                                                'tip': 'Ch14',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch15',
                                                'tip': 'Ch15',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch16',
                                                'tip': 'Ch16',
                                                'type': 'bool',
                                                'value': True},
                                               ), },
                                 ), },

                   {'name': 'Sampling Settings',
                    'type': 'group',
                    'children': ({'title': 'Sampling Frequency',
                                  'name': 'Fs',
                                  'type': 'float',
                                  'value': 10e3,
                                  'step': 100,
                                  'siPrefix': True,
                                  'suffix': 'Hz'},
                                 {'title': 'Refresh Time',
                                  'name': 'Refresh',
                                  'type': 'float',
                                  'value': 1.0,
                                  'step': 0.01,
                                  'limits': (0.01, 500),
                                  'suffix': 's'},
                                 {'title': 'Vds',
                                  'name': 'Vds',
                                  'type': 'float',
                                  'value': 0.05,
                                  'step': 0.01,
                                  'limits': (0, 0.1)},
                                 {'title': 'Vgs',
                                  'name': 'Vgs',
                                  'type': 'float',
                                  'value': 0.1,
                                  'step': 0.1,
                                  'limits': (-0.1, 0.5)},
                                 {'title': 'Refresh graph',
                                  'name':'Graph',
                                  'type': 'action',},
                                  
                                  
                                     ), }
                   )


###############################################################################


class SampSetParam(pTypes.GroupParameter):
    NewConf = Qt.pyqtSignal()

    Chs = []
    Acq = {}

    def __init__(self, **kwargs):
        super(SampSetParam, self).__init__(**kwargs)
        self.addChildren(SampSettingConf)

        self.SampSet = self.param('Sampling Settings')
        self.Fs = self.SampSet.param('Fs')
        self.Refresh = self.SampSet.param('Refresh')

        self.ChsConfig = self.param('ChsConfig')
        self.Channels = self.ChsConfig.param('Channels')

        # Init Settings
        self.on_Acq_Changed()
        self.on_Ch_Changed()
        self.on_Fs_Changed()

        # Signals
        self.Channels.sigTreeStateChanged.connect(self.on_Ch_Changed)
        self.ChsConfig.param('AcqAC').sigValueChanged.connect(self.on_Acq_Changed)
        self.ChsConfig.param('AcqDC').sigValueChanged.connect(self.on_Acq_Changed)
        self.Fs.sigValueChanged.connect(self.on_Fs_Changed)

    def on_Acq_Changed(self):
        for p in self.ChsConfig.children():
            if p.name() is 'AcqAC':
                self.Acq[p.name()] = p.value()
            if p.name() is 'AcqDC':
                self.Acq[p.name()] = p.value()
        self.on_Fs_Changed()
        self.NewConf.emit()

    def on_Fs_Changed(self):
        if self.Chs:
            Index = 1
            if self.Acq['AcqDC'] and self.Acq['AcqAC'] is True:
                Index = 2
            if self.Fs.value() > (1e6/(len(self.Chs)*Index)):
                self.SampSet.param('Fs').setValue(1e6/(len(self.Chs)*Index))

    def on_Ch_Changed(self):
        self.Chs = []
        for p in self.Channels.children():
            if p.value() is True:
                self.Chs.append(p.name())
        self.on_Fs_Changed()
        self.NewConf.emit()

    def GetChannelsNames(self):
        Ind = 0
        ChNames = {}
        acqTys = []
        for tyn, tyv in self.Acq.items():
            if tyv:
                acqTys.append(tyn)

        if 'AcqDC' in acqTys:
            for Ch in self.Chs:
                ChNames[Ch + 'DC'] = Ind
                Ind += 1

        if 'AcqAC' in acqTys:
            for Ch in self.Chs:
                ChNames[Ch + 'AC'] = Ind
                Ind += 1

        return ChNames

    def GetSampKwargs(self):
        GenKwargs = {}
        for p in self.SampSet.children():
            GenKwargs[p.name()] = p.value()
        return GenKwargs

    def GetChannelsConfigKwargs(self):
        ChanKwargs = {}
        for p in self.ChsConfig.children():
            if p.name() is 'Channels':
                ChanKwargs[p.name()] = self.Chs
            else:
                ChanKwargs[p.name()] = p.value()
        print(ChanKwargs, 'ChanKwargs')
        return ChanKwargs

###############################################################################

class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()

    def __init__(self, CarrierConfig=None, ColChannels=None, FsGen=None, 
                 GenSize=None, ScopeChannels=None, FsScope=None, 
                 BufferSize=None, CMVoltage=None, AcqVRange=5, 
                 GainBoard=5e3, AcqDiff=False, AvgIndex=5, MeaType='Freq',
                 ChannelsConfigKW=None, SampKw=None):

        super(DataAcquisitionThread, self).__init__()
        
        self.SampKw = SampKw
        
        if MeaType == 'Time':
            self.DaqInterface = CoreMod.ChannelsConfig(aiChannels=aiChannels,
                                                       doChannels=DOChannels,
                                                       aoChannels=aoChannels,
                                                       **ChannelsConfigKW)
            self.DaqInterface.DataEveryNEvent = self.NewDataTime
        
        if MeaType == 'Freq':
            #aquí hacer el import del diccionario de canales que toque
            
            self.DaqInterface = CoreMod.ChannelsConfig(Channels=ScopeChannels,
                                                       Range=AcqVRange,
                                                       Cols=ColChannels,
                                                       AcqDiff=AcqDiff,
                                                       aiChannels=aiChannels,
                                                       aoChannels=aoChannels
                                                       )
            
            self.DaqInterface.DataEveryNEvent = self.NewDataFreq
            self.Channels = ScopeChannels
            self.AvgIndex = AvgIndex
            self.FsGen = FsGen
            self.GenSize = GenSize
            self.FsScope = FsScope
            self.EveryN = BufferSize
    
            self.gain = GainBoard
            self.Col1 = CarrierConfig['Col1']
            self.Freq = self.Col1['Frequency']
            self.phase = self.Col1['Phase']
            self.Amplitude = self.Col1['Amplitude']
            self.Vcm = CMVoltage  # se empieza el sweep con el primer valor
            self.OutSignal(Vds=self.Amplitude)

    def run(self, *args, **kwargs):
        if self.SampKw is None:
            self.DaqInterface.StartAcquisition(Fs=self.FsScope,
                                               EveryN=self.EveryN,
                                               Vgs=self.Vcm,
                                               )
        else:
            self.DaqInterface.StartAcquisition(**self.SampKw)  

        self.loop = Qt.QEventLoop()
        self.loop.exec_()

    def NewDataTime(self, aiData, aiDataAC=None):
        self.aiData = aiData
        self.aiDataAC = aiDataAC
        self.NewTimeData.emit()
    
    def NewDataFreq(self, aiData):
        # print(self.Vcm)
        self.OutDataVolts = aiData # (Pico)
        self.OutData = (aiData/self.gain)  # (Pico)

        self.NewMuxData.emit()
        
    def OutSignal(self, Vds):
        stepScope = 2*np.pi*(self.Freq/self.FsScope)
        t = np.arange(0, ((1/self.FsGen)*(self.GenSize)), 1/self.FsGen)
        # self.Signal = np.ndarray((len(t), len(Vds)))
        # self.Vcoi = np.ndarray((self.Signal.shape))
        # for ind, Vd in enumerate(Vds):
        #     self.Signal[:,ind] = Vd*np.cos(self.Freq*2*np.pi*t)
        #     self.Vcoi = np.complex128(1*np.exp(1j*(stepScope*np.arange(self.EveryN))))

        self.Signal = Vds*np.cos(self.Freq*2*np.pi*t)
        self.Vcoi = np.complex128(1*np.exp(1j*(stepScope*np.arange(self.EveryN))))

