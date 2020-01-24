# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 11:06:38 2020

@author: Javier
"""

import pyqtgraph.parametertree.parameterTypes as pTypes


ACParams = {'name': 'ACConfig',
            'type': 'group',
            'children': [{'name': 'BodeParams',
                          'type': 'group',
                          'children': [{'name': 'CheckBode',
                                        'type': 'bool',
                                        'value': False, },
                                       {'name': 'FreqMin',
                                        'type': 'float',
                                        'value': 0.35,
                                        'step': 0.05,
                                        'sufix': 'Hz'},
                                       {'name': 'FreqMax',
                                        'type': 'float',
                                        'value': 10e3,
                                        'step': 1e3,
                                        'sufix': 'Hz'},
                                       {'name': 'Arms',
                                        'type': 'float',
                                        'value': 0.01,
                                        'step': 1e-3,
                                        'sufix': 'V'},
                                       {'name': 'nAvg',
                                        'type': 'int',
                                        'value': 2,
                                        'step': 1, },
                                       {'name': 'nFreqs',
                                        'type': 'int',
                                        'value': 50,
                                        'step': 1, },
                                       {'name': 'Rhardware',
                                        'type': 'bool',
                                        'value': False, },
                                       {'name': 'BodeL Duration',
                                        'type': 'float',
                                        'value': 20,
                                        'sufix': 's',
                                        'readonly': True},
                                       {'name': 'BodeH Duration',
                                        'type': 'float',
                                        'value': 20,
                                        'sufix': 's',
                                        'readonly': True}, ]
                          },
                         {'name': 'PSDParams',
                          'type': 'group',
                          'children': [{'name': 'CheckPSD',
                                        'type': 'bool',
                                        'value': False, },
                                       {'name': 'Fs',
                                        'type': 'float',
                                        'value': 1000,
                                        'step': 100,
                                        'sufix': 'Hz'},
                                       {'name': 'PSDnAvg',
                                        'type': 'int',
                                        'value': 5,
                                        'step': 1, },
                                       {'name': '2**nFFT',
                                        'type': 'int',
                                        'value': 14,
                                        'step': 1, },
                                       {'name': 'PSD Duration',
                                        'type': 'float',
                                        'value': 20,
                                        'sufix': 's',
                                        'readonly': True}, ]}, ]}


class ACConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChild(ACParams)
        self.ACParameters = self.param('ACConfig')

        self.BodeParameters = self.ACParameters.param('BodeParams')

        self.FreqMin = self.BodeParameters.param('FreqMin')
        self.FreqMax = self.BodeParameters.param('FreqMax')
        self.Amplitude = self.BodeParameters.param('Arms')
        self.nAvg = self.BodeParameters.param('nAvg')
        self.nFreqs = self.BodeParameters.param('nFreqs')
        self.BodeLDuration = self.BodeParameters.param('BodeL Duration')
        self.BodeHDuration = self.BodeParameters.param('BodeH Duration')
        # self.CheckBode = self.BodeParameters.param('CheckBode')
        # self.Rhardware = self.BodeParameters.param('Rhardware')

        self.FreqMin.sigTreeStateChanged.connect(self.GetBodeParams)
        self.FreqMax.sigTreeStateChanged.connect(self.GetBodeParams)
        self.Amplitude.sigTreeStateChanged.connect(self.GetBodeParams)
        self.nAvg.sigTreeStateChanged.connect(self.GetBodeParams)
        self.nFreqs.sigTreeStateChanged.connect(self.GetBodeParams)
        
        # self.CheckBode.sigTreeStateChanged.connect(self.GetBodeSettings)
        # self.Rhardware.sigTreeStateChanged.connect(self.GetBodeSettings)

        self.PSDParameters = self.ACParameters.param('PSDParams')

        self.Fs = self.PSDParameters.param('Fs')
        self.nFFT = self.PSDParameters.param('2**nFFT')
        self.PSDnAvg = self.PSDParameters.param('PSDnAvg')

        self.Fs.sigTreeStateChanged.connect(self.GetPSDDuration)
        self.nFFT.sigTreeStateChanged.connect(self.GetPSDDuration)
        self.PSDnAvg.sigTreeStateChanged.connect(self.GetPSDDuration)

    def GetBodeParams(self):
        BodeKwargs = {}
        for p in self.BodeParameters.children():
            BodeKwargs[p.name()] = p.value()
        return BodeKwargs

    def GetBodeSettings(self):
        BodeHardware = []
        Checkbode = []

        for p in self.BodeParameters.children():

            if p.name() == 'Rhardware':
                print('rh')
                BodeHardware = p.value()
            elif p.name() == 'CheckBode':
                print('chk')
                Checkbode = p.value()

        return BodeHardware, Checkbode

    def GetPSDParams(self):
        PSDKwargs = {}
        CheckPSD = False
        for p in self.PSDParameters.children():
            if p.name() == 'CheckPSD':
                CheckPSD = p.value()
            else:
                PSDKwargs[p.name()] = p.value()
        return PSDKwargs, CheckPSD

    def GetPSDDuration(self):
        PSDKwargs, checkpsd = self.GetPSDParams()
        print(PSDKwargs)
        print(PSDKwargs['2**nFFT'])
        print(PSDKwargs['PSDnAvg'])
        print(PSDKwargs['Fs'])
        PSDDuration = 2**PSDKwargs['2**nFFT']*PSDKwargs['PSDnAvg']*(
                1/PSDKwargs['Fs'])
        self.PSDParameters.param('PSD Duration').setValue(PSDDuration)
        return PSDDuration
