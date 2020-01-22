# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 11:06:38 2020

@author: Javier
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

import numpy as np

BodeParams = {'name': 'BodeConfig',
              'type': 'group',
              'children': ({'title': 'Bode',
                            'name': 'CheckBode',
                            'type': 'Bool',
                            'value': False,
                            },
                           {'title': 'BodeParameters',
                            'name': 'BodeParam',
                            'type': 'group',
                            'children': ({'name': 'FreqMin',
                                          'type': 'float',
                                          'value': 0.35,
                                          'step': 0.05,
                                          'suffix': ' Hz'},
                                         {'name': 'FreqMax',
                                          'type': 'float',
                                          'value': 10e3,
                                          'step': 1e3,
                                          'suffix': ' Hz'},
                                         {'name': 'Arms',
                                          'type': 'float',
                                          'value': 0.001,
                                          'step': 1e-3,
                                          'suffix': ' V'},
                                         {'name': 'nAvg',
                                          'type': 'int',
                                          'value': 2,
                                          'step': 1},
                                         {'name': 'nFreqs',
                                          'type': 'int',
                                          'value': 50,
                                          'step': 1},
                                         {'name': 'BodeL Duration',
                                          'type': 'float',
                                          'value': 20,
                                          'suffix': ' s',
                                          'readonly': True},
                                         {'name': 'BodeH Duration',
                                          'type': 'float',
                                          'value': 20,
                                          'suffix': ' s',
                                          'readonly': True}, )},

                           {'title': 'Rhardware',
                            'name': 'Rhardware',
                            'type': 'bool',
                            'value': False})}

PSDParams = {'name': 'PSDConfig',
             'type': 'group',
             'children': ({'title': 'PSD',
                           'name': 'CheckPSD',
                           'type': 'Bool',
                           'value': False,
                           },
                          {'title': 'PSDParameters',
                           'name': 'PSDParam',
                           'type': 'group',
                           'children': ({'name': 'Fs',
                                         'type': 'float',
                                         'value': 1000,
                                         'step': 100,
                                         'suffix': ' Hz'},
                                        {'name': 'PSDnAvg',
                                         'type': 'int',
                                         'value': 5,
                                         'step': 1, },
                                        {'name': '2**nFFT',
                                         'type': 'int',
                                         'value': 14,
                                         'step': 1,
                                         'suffix': ' Hz'},
                                        {'name': 'PSD Duration',
                                         'type': 'float',
                                         'value': 20,
                                         'suffix': ' s',
                                         'readonly': True}, )}, )}


class ACConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChild(BodeParams)
        self.addChild(PSDParams)

        self.BodeConfig = self.param('BodeConfig')
        self.BodeParameters = self.BodeConfig.param('BodeParam')

        self.FreqMin = self.BodeParameters.param('FreqMin')
        self.FreqMax = self.BodeParameters.param('FreqMax')
        self.Amplitude = self.BodeParameters.param('Arms')
        self.nAvg = self.BodeParameters.param('nAvg')
        self.nFreqs = self.BodeParameters.param('nFreqs')
        self.BodeLDuration = self.BodeParameters.param('BodeL Duration')
        self.BodeHDuration = self.BodeParameters.param('BodeH Duration')

        self.FreqMin.sigvalueChanged.connect(self.GetBodeParams)
        self.FreqMax.sigvalueChanged.connect(self.GetBodeParams)
        self.Amplitude.sigvalueChanged.connect(self.GetBodeParams)
        self.nAvg.sigvalueChanged.connect(self.GetBodeParams)
        self.nFreqs.sigvalueChanged.connect(self.GetBodeParams)

        self.PSDConfig = self.param('PSDConfig')
        self.PSDParameters = self.PSDConfig.param('PSDParameters')

        self.Fs = self.PSDParameters.param('Fs')
        self.nFFT = self.PSDParameters.param('2**nFFT')
        self.PSDnAvg = self.PSDParameters.param('PSDnAvg')

        self.Fs.sigvalueChanged.connect(self.GetPSDDuration)
        self.nFFT.sigvalueChanged.connect(self.GetPSDDuration)
        self.PSDnAvg.sigvalueChanged.connect(self.GetPSDDuration)

    def GetBodeParams(self):
        BodeKwargs = {}
        for p in self.BodeParameters.children():
            BodeKwargs[p.name()] = p.value()
        return BodeKwargs

    def GetBodeSettings(self):
        BodeHardware = {}
        Checkbode = {}

        for p in self.BodeConfig.children():
            if p == 'Rhardware':
                BodeHardware[p.name()] = p.value()
            elif p == 'CheckBode':
                Checkbode[p.name()] = p.value()

        return BodeHardware, Checkbode

    def GetPSDParams(self):
        PSDKwargs = {}
        for p in self.PSDParameters.children():
            PSDKwargs[p.name()] = p.value()
        return PSDKwargs

    def GetPSDConfig(self):
        CheckPSD = {}
        for p in self.PSDConfig.children():
            CheckPSD[p.name()] = p.value()
        return CheckPSD

    def GetPSDDuration(self):
        PSDKwargs = self.GetPSDParams()
        PSDDuration = 2**PSDKwargs['2**nFFT'].value()*PSDKwargs['PSDnAvg']*(
                1/PSDKwargs['Fs'])
        self.PSDParameters.param('PSD Duration').setValue(PSDDuration)
        return PSDDuration
        
                    
        