#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 14:12:43 2019

@author: aguimera
"""

import PyDAQmx as Daq
import sys
import ctypes
from ctypes import byref, c_int32
import numpy as np


def GetDevName():
    # Get Device Name of Daq Card
    n = 1024
    buff = ctypes.create_string_buffer(n)
    Daq.DAQmxGetSysDevNames(buff, n)
    if sys.version_info >= (3,):
        value = buff.value.decode()
    else:
        value = buff.value

    Dev = None
    value = value.replace(' ', '')
    for dev in value.split(','):
        if dev.startswith('Sim'):
            continue
        Dev = dev + '/{}'

    if Dev is None:
        print('ERRROORR dev not found ', value)

    return Dev

##############################################################################


class ReadAnalog(Daq.Task):

    EveryNEvent = None
    DoneEvent = None
    ContSamps = False

    def __init__(self, InChans, Range=5.0, Diff=False):
        Daq.Task.__init__(self)
        self.Channels = InChans

        Dev = GetDevName()
        for Ch in self.Channels:
            if Diff is False:
                self.CreateAIVoltageChan(Dev.format(Ch), "",
                                         Daq.DAQmx_Val_RSE,
                                         -Range, Range,
                                         Daq.DAQmx_Val_Volts, None)
            if Diff is True:
                self.CreateAIVoltageChan(Dev.format(Ch), "",
                                         Daq.DAQmx_Val_Diff,
                                         -Range, Range,
                                         Daq.DAQmx_Val_Volts, None)

        self.AutoRegisterDoneEvent(0)

    def ReadData(self, Fs, nSamps, EverySamps):
        self.Fs = Fs
        self.EverySamps = EverySamps

        self.Buffer = np.ndarray([nSamps, len(self.Channels)])
        self.BufferIndex = 0
        self.CfgSampClkTiming("", Fs, Daq.DAQmx_Val_Rising,
                              Daq.DAQmx_Val_FiniteSamps, nSamps)

        self.AutoRegisterEveryNSamplesEvent(Daq.DAQmx_Val_Acquired_Into_Buffer,
                                            self.EverySamps, 0)
        print('StarTask')
        self.StartTask()

    def ReadContData(self, Fs, EverySamps):
        self.Fs = Fs
        self.EverySamps = np.int32(EverySamps)
        self.ContSamps = True

        self.CfgSampClkTiming("", Fs, Daq.DAQmx_Val_Rising,
                              Daq.DAQmx_Val_ContSamps,
                              self.EverySamps)

        self.CfgInputBuffer(self.EverySamps*10)
        self.AutoRegisterEveryNSamplesEvent(Daq.DAQmx_Val_Acquired_Into_Buffer,
                                            self.EverySamps, 0)
        self.StartTask()

    def StopContData(self):
        self.StopTask()
        self.ContSamps = False

    def EveryNCallback(self):
        read = c_int32()
        data = np.zeros((self.EverySamps, len(self.Channels)))
        self.ReadAnalogF64(self.EverySamps, 10.0,
                           Daq.DAQmx_Val_GroupByScanNumber,
                           data, data.size, byref(read), None)


        if not self.ContSamps:
            self.Buffer[self.BufferIndex:self.BufferIndex + self.EverySamps, :] = data
            self.BufferIndex += self.EverySamps
            # self.data = np.vstack((self.data, data))

        if self.EveryNEvent:
            self.EveryNEvent(data)

    def DoneCallback(self, status):
        self.StopTask()
        self.UnregisterEveryNSamplesEvent()

        if self.DoneEvent:
            self.DoneEvent(self.Buffer[1:, :])

        return 0  # The function should return an integer


##############################################################################


class WriteAnalog(Daq.Task):

    '''
    Class to write data to Daq card
    '''

    def __init__(self, Channels):
        Daq.Task.__init__(self)
        Dev = GetDevName()
        for Ch in Channels:
            self.CreateAOVoltageChan(Dev.format(Ch), "",
                                     -10.0, 10.0, Daq.DAQmx_Val_Volts, None)
        self.DisableStartTrig()
        self.StopTask()

    def SetVal(self, value):
        self.StartTask()
        self.WriteAnalogScalarF64(1, -1, value, None)
        self.StopTask()

    def SetSignal(self, Signal, nSamps, FsBase='ai/SampleClock', FsDiv=1):
        read = c_int32()

        self.CfgSampClkTiming(FsBase, FsDiv, Daq.DAQmx_Val_Rising,
                              Daq.DAQmx_Val_FiniteSamps, nSamps)

        self.CfgDigEdgeStartTrig('ai/StartTrigger', Daq.DAQmx_Val_Rising)
        self.WriteAnalogF64(nSamps, False, -1, Daq.DAQmx_Val_GroupByChannel,
                            Signal, byref(read), None)
        self.StartTask()

    def SetContSignal(self, Signal, nSamps, FsBase='ai/SampleClock', FsDiv=1):
        read = c_int32()

        self.CfgSampClkTiming(FsBase, FsDiv, Daq.DAQmx_Val_Rising,
                              Daq.DAQmx_Val_ContSamps, nSamps)

        self.CfgDigEdgeStartTrig('ai/StartTrigger', Daq.DAQmx_Val_Rising)
        self.WriteAnalogF64(nSamps, False, -1, Daq.DAQmx_Val_GroupByChannel,
                            Signal, byref(read), None)
        self.StartTask()


##############################################################################


class WriteDigital(Daq.Task):

    '''
    Class to write data to Daq card
    '''

    def __init__(self, Channels):
        Daq.Task.__init__(self)
        Dev = GetDevName()
        for Ch in Channels:
            self.CreateDOChan(Dev.format(Ch), "",
                              Daq.DAQmx_Val_ChanForAllLines)

        self.DisableStartTrig()
        self.StopTask()

    def SetDigitalSignal(self, Signal):
        print('SetDigitalSignal')
        print('SetDigSignal', Signal, Signal.shape)
        # Sig = np.array(Signal, dtype=np.uint8)
        Sig = Signal.astype(np.uint8)
        print(Sig, 'SIGNAL')
        self.WriteDigitalLines(1, 1, 10.0, Daq.DAQmx_Val_GroupByChannel,
                               Sig, None, None)

    def SetContSignal(self, Signal):
        read = c_int32()
        self.CfgSampClkTiming('ai/SampleClock', 1, Daq.DAQmx_Val_Rising,
                              Daq.DAQmx_Val_ContSamps, Signal.shape[1])
        self.CfgDigEdgeStartTrig('ai/StartTrigger', Daq.DAQmx_Val_Rising)
        self.WriteDigitalLines(Signal.shape[1], False, 1,
                               Daq.DAQmx_Val_GroupByChannel,
                               Signal, byref(read), None)
        self.StartTask()
#        print('End SetSingal', read)

##############################################################################
