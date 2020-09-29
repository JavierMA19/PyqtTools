# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 09:11:50 2020

@author: Lucia
"""

import PyqtTools.DaqInterface as DaqInt
import numpy as np

class ChannelsConfig():

    ChannelIndex = None
    ChNamesList = None
    AnalogInputs = None
    DigitalOutputs = None
    SwitchOut = None
    Dec = None
    DCSwitch = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, ], dtype=np.uint8)
    ACSwitch = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=np.uint8)
    # DecDigital = np.array([0, 1, 0, 1, 1], dtype=np.uint8) # Ouput should be: P26
    # Events list
    DataEveryNEvent = None
    DataDoneEvent = None
        
    def __init__(self, Channels, Cols=None,
                 AcqDC=False, AcqAC=False, AcqDCAC=False,
                 ACGain=1e6, DCGain=10e3, AcqDiff=False, Range=5,
                 aiChannels=None, aoChannels=None, diChannels=None, 
                 doChannels=None, decoder=None, **kwargs):
        
        print('InitChannels')
        
        self._InitAnalogOutputs(ChVgs=aoChannels[0],
                                ChVds=aoChannels[1])
        
        self.ChNamesList = sorted(Channels)
        
        self.AcqAC = AcqAC
        self.AcqDC = AcqDC
        self.AcqDCAC = AcqDCAC
        self.ACGain = ACGain
        self.DCGain = DCGain
        self.DOChannels = doChannels
        
        self._InitAnalogInputs(aiChannels=aiChannels,
                               Diff=AcqDiff,
                               Range=Range,
                               )
        
        if doChannels is not None:
            self.SwitchOut = DaqInt.WriteDigital(Channels=doChannels)
            
        if decoder is not None:
            self.Dec = DaqInt.WriteDigital(Channels=decoder)
        
        if Cols is not None:
            self.MuxChannelNames = []
            for Row in self.ChNamesList:
                for Col in Cols:
                    self.MuxChannelNames.append(Row + Col)
                    
    def _InitAnalogInputs(self, aiChannels, Diff=False, Range=5.0):
        self.ChannelIndex = {}
        self.DCChannelIndex = {}
        self.ACChannelIndex = {}
        InChans = []

        index = 0
        sortindex = 0
        if self.AcqDCAC:
            for ch in self.ChNamesList:
                InChans.append(aiChannels[ch][0])
                self.DCChannelIndex[ch] = (index, sortindex)
                index += 1
                InChans.append(aiChannels[ch][1])
                self.ACChannelIndex[ch] = (index, sortindex)
                index += 1
                sortindex += 1
            
            for ch in self.ChNamesList:
                print (ch, ' DC -> ', aiChannels[ch][0], self.DCChannelIndex[ch])
                print (ch, ' AC -> ', aiChannels[ch][1], self.ACChannelIndex[ch])
                
        else:  
            for ch in self.ChNamesList:
                if len(aiChannels[ch]) <= 1:
                    InChans.append(aiChannels[ch])
                    
                else:
                    InChans.append(aiChannels[ch][0])  # only Output+
                
                self.ChannelIndex[ch] = (index)
                index += 1

        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans,
                                              Diff=Diff,
                                              Range=Range)
        
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBack
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack
        
    def _InitAnalogOutputs(self, ChVgs, ChVds):
        print('ChVgs ->', ChVgs)
        print('ChVds ->', ChVds)
        self.VgsOut = DaqInt.WriteAnalog((ChVgs,))
        self.VdsOut = DaqInt.WriteAnalog((ChVds,))

    def SetVcm(self, Vcm):
        print(Vcm)
        self.VgsOut.SetVal(Vcm)
        
    def SetBias(self, Vds, Vgs):
        print('ChannelsConfig SetBias Vgs ->', Vgs, 'Vds ->', Vds)
        self.VdsOut.SetVal(Vds)
        self.VgsOut.SetVal(-Vgs)
        self.BiasVd = Vds-Vgs
        self.Vgs = Vgs
        self.Vds = Vds
        
    def SetFreqSignal(self, Signal, FsGen=2e6, FsBase=""):
        self.VdsOut.SetContSignal(Signal=Signal,
                                  nSamps=len(Signal),
                                  FsBase=FsBase,
                                  FsDiv=FsGen)
        self.Vds = None
    
    def SetDigitalSignal(self, Signal):
        if not self.SwitchOut:
            self.SwitchOut = DaqInt.WriteDigital(Channels=self.DOChannels)
        self.SwitchOut.SetDigitalSignal(Signal)
        if self.Dec is not None:
            self.Dec.SetDigitalSignal(self.DecDigital)

    def SetContSignal(self, Signal, nSamps):
        if not self.VgsOut:
            self.VgsOut = DaqInt.WriteAnalog(('ao2',))
        self.VgsOut.DisableStartTrig()
        self.VgsOut.SetContSignal(Signal=Signal,
                                  nSamps=nSamps)
        
    def _SortChannels(self, data, SortDict):
        (samps, inch) = data.shape
        sData = np.zeros((samps, len(SortDict)))
        
        for chn, inds in sorted(SortDict.items()):
            if chn == 'Gate':
                sData[:, 0] = data[:, inds]
            else:
                if len(inds) <=1:
                    sData[:, inds] = data[:, inds]
                else:
                    sData[:, inds[1]] = data[:, inds[0]]

        return sData
    
    def EveryNEventCallBack(self, Data):
        _DataEveryNEvent = self.DataEveryNEvent

        if _DataEveryNEvent is not None:
            if self.AcqDCAC:
                print('Sending DC DATA')
                aiDataDC = self._SortChannels(Data, 
                                              self.DCChannelIndex)
                aiDataDC = (aiDataDC-self.BiasVd) / self.DCGain
                print('Sending AC DATA')
                aiDataAC = self._SortChannels(Data, 
                                              self.ACChannelIndex)
                aiDataAC = aiDataAC / self.ACGain
                _DataEveryNEvent(aiDataDC, aiDataAC)
                
            else:
                if self.AcqDC:
                    aiDataDC = self._SortChannels(Data, self.ChannelIndex)
                    aiDataDC = (aiDataDC-self.BiasVd) / self.DCGain
    
                if self.AcqAC:
                    aiDataAC = self._SortChannels(Data, self.ChannelIndex)
                    aiDataAC = aiDataAC / self.ACGain
    
                if self.AcqAC and self.AcqDC:
                    print('ERROR')
                    aiData = np.hstack((aiDataDC, aiDataAC))
                    _DataEveryNEvent(aiData)
                elif self.AcqAC:
                    _DataEveryNEvent(aiDataAC)
                elif self.AcqDC:
                    _DataEveryNEvent(aiDataDC)
                    
    def DoneEventCallBack(self, Data):
        print('Done callback')
        
    def StartAcquisition(self, Fs, Vgs, Vds=None, EveryN=None, Refresh=None,
                         **kwargs):
        if Vds is not None:
            self.SetBias(Vgs=Vgs, Vds=Vds)
        else:
            self.SetVcm(Vcm=Vgs)
        
        if self.AcqDC:
            print('DC')
            self.SetDigitalSignal(Signal=self.DCSwitch)
            
        if self.AcqAC:
            print('AC')
            self.SetDigitalSignal(Signal=self.ACSwitch)
                       
        self.Fs = Fs
        if EveryN is None:
            self.EveryN = Refresh*Fs # TODO check this
            
        self.AnalogInputs.ReadContData(Fs=self.Fs,
                                       EverySamps=self.EveryN)

    def Stop(self):
        print('Stopppp')
                
        if self.Vds is not None:
            print('All to 0')
            self.SetBias(Vgs=0, Vds=0)
        
        else:
            self.VgsOut.StopTask()
            self.VgsOut.SetVal(0)
            self.VgsOut.ClearTask()
            self.VgsOut = None
            self.VdsOut.ClearTask()
            self.VdsOut = None

        if self.SwitchOut is not None:
            print('Clear Digital')
            self.SwitchOut.ClearTask()
            self.SwitchOut = None
        
        self.AnalogInputs.StopContData()