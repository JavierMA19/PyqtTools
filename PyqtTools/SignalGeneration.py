# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 10:09:59 2020

@author: lucia
"""

import numpy as np
from scipy import signal
from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes

SamplingConf = {'name': 'SamplingConf',
                'title': 'Sampling',
                'type': 'group',
                'children': ({'name': 'Fs',
                              'title': 'Sampling Rate',
                              'type': 'float',
                              'value': 50e3,
                              'siPrefix': True,
                              'suffix': 'Hz'},
                             {'name': 'nSamples',
                              'title': 'Number of Samples',
                              'type': 'int',
                              'value': int(20e3),
                              'siPrefix': True,
                              'suffix': 'Samples'},
                             {'name': 'tInterrupt',
                              'title': 'Interruption Time',
                              'type': 'float',
                              'readonly': True,
                              'value': 0.5,
                              'siPrefix': True,
                              'suffix': 's'},
                             {'name': 'nChannels',
                              'title': 'Number of Channels',
                              'type': 'int',
                              'value': 3,
                              },
                             )
                }

CarrierConf = {'name': 'CarrierConf',
               'title': 'Carrier',
               'type': 'group',
               'children': (
                            {'name': 'CarrFrequency',
                             'title': 'Carrier Frequency',
                             'type': 'float',
                             'value': 10e3,
                             'siPrefix': True,
                             'suffix': 'Hz'},
                            {'name': 'Phase',
                             'title': 'Carrier Phase',
                             'type': 'float',
                             'value': 0,
                             'siPrefix': True,
                             'suffix': 'degree'},
                            {'name': 'Amplitude',
                             'title': 'Carrier Amplitude',
                             'type': 'float',
                             'value': 0.05,
                             'siPrefix': True,
                             'suffix': 'V'},
                            {'name': 'CarrNoise',
                             'title': 'Noise Level',
                             'type': 'float',
                             'value': 0,
                             'siPrefix': True,
                             'suffix': 'V'},
                            )
               }

ModulationConf = {'name': 'ModulationConf',
                  'title': 'Modulation',
                  'type': 'group',
                  'children': ({'name': 'ModType',
                                'title': 'Waveform Type',
                                'type': 'list',
                                'values': ['sinusoidal', 'square'],
                                'value': 'sinusoidal',
                                'visible': True
                                },
                               {'name': 'ModFrequency',
                                'title': 'Modulation Frequency',
                                'type': 'float',
                                'value': 1e3,
                                'siPrefix': True,
                                'suffix': 'Hz'
                                },
                               {'name': 'ModFactor',
                                'title': 'Modulation Factor',
                                'type': 'float',
                                'value': 0.01,
                                'siPrefix': True
                                },
                               {'name': 'ModNoise',
                                'title': 'Noise Level',
                                'type': 'float',
                                'value': 0,
                                'siPrefix': True,
                                'suffix': 'V'
                                },
                               )
                  }


class SignalConfigTree(pTypes.GroupParameter):

    def __init__(self, QTparent, **kwargs):

        pTypes.GroupParameter.__init__(self, **kwargs)

        # Add Sampling Configuration parameters
        self.addChild(SamplingConf)
        self.addChild(ModulationConf)
        self.addChild(CarrierConf)

        self.SampConf = self.param('SamplingConf')
        self.ModConf = self.param('ModulationConf')
        self.CarConf = self.param('CarrierConf')

        # # And assign its variables
        self.Fs = self.SampConf.param('Fs')
        self.nSamples = self.SampConf.param('nSamples')
        self.tInterrput = self.SampConf.param('tInterrupt')
        self.nChannels = self.SampConf.param('nChannels')
        # # Link the change of a value of the tree to a function
        # # With Fs and nSamples is calculated tInterrpution
        self.SampConf.sigTreeStateChanged.connect(self.on_GeneralConfig_changed)
        # # Add Carrier Configuration Tree
        # self.CarrierConfig = self.param('CarrierConfig')
        # # And assign variables
        # self.CarrType = self.CarrierConfig.param('CarrType')
        # self.CarrFreq = self.CarrierConfig.param('CarrFrequency')
        # self.CarrAmp = self.CarrierConfig.param('Amplitude')
        # self.CarrPhase = self.CarrierConfig.param('Phase')
        # self.CarrNoise = self.CarrierConfig.param('CarrNoise')
        # # Link the change of a Frequency value to a function
        # # It is needed Freq and Fs to be Multiples
        # self.CarrFreq.sigValueChanged.connect(self.on_CarrFreq_changed)
        # # Add Modulation Configuration Tree
        # self.addChild(ModulationConfiguration)
        
        # # And assign variables
        # self.ModType = self.ModConfig.param('ModType')
        # self.ModFreq = self.ModConfig.param('ModFrequency')
        # self.ModFact = self.ModConfig.param('ModFactor')
        # self.ModNoise = self.ModConfig.param('ModNoise')
        # # Call the on_XX functions to initialize correctly the variables
        # self.on_GeneralConfig_changed()
        # self.on_CarrFreq_changed()

    def GetChannels(self):
        """
        Return the channels dictionary.

        Returns
        -------
        Channels : Dictionary, where key is the channel name
                   and value is an integer which indicate the index of the
                   input data array.
        """
        Channels = {}
        for i in range(self.nChannels.value()):
            Name = 'Ch' + str(i)
            Channels[Name] = i
        return Channels

    def on_GeneralConfig_changed(self):
        '''
        This functions is used to calculate the interruption time. If the
        processes take more time data will be overwritten and lost.

        Returns
        -------
        None.

        '''
        # value is used to aqcuire the value of the variable
        tInt = self.nSamples.value()/self.Fs.value()
        # setValue is used to change a value of the tree
        self.tInterrput.setValue(tInt)
        # self.on_CarrFreq_changed()

    def on_CarrFreq_changed(self):
        '''
        This function is used to ensure that carrier frequency and sampling
        frequency are multiples.

        Returns
        -------
        None.

        '''
        # value is used to aqcuire the value of the variable
        Fc = self.CarrFreq.value()
        factor = round((self.nSamples.value()*Fc)/self.Fs.value())
        FcNew = factor*self.Fs.value()/self.nSamples.value()
        # setValue is used to change a value of the tree
        self.CarrFreq.setValue(FcNew)

    def Get_SignalConf_Params(self):
        '''
        This function returns a dictionary conatining all the information
        related with the configurations set in the different signal trees

        Returns
        -------
        :return: A Dictionary with the data arranged as follows:
        SignalConfig : dictionary
                     {'Fs': 2000000.0,
                      'nSamples': 20000,
                      'tInterrupt': 0.01,
                      'CarrType': 'sinusoidal',
                      'CarrFrequency': 30000.0,
                      'Phase': 0,
                      'Amplitude': 0.05,
                      'CarrNoise': 0,
                      'ModType': 'sinusoidal',
                      'ModFrequency': 1000.0,
                      'ModFactor': 0.1,
                      'ModNoise': 0}
        '''
        SignalConfig = {}
        for Params in self.SampConf.children():
            SignalConfig[Params.name()] = Params.value()
        for Params in self.CarConf.children():
            SignalConfig[Params.name()] = Params.value()
        for Params in self.ModConf.children():
            SignalConfig[Params.name()] = Params.value()
            
        return SignalConfig


def GenAMSignal(Fs, nSamples, Amplitude, CarrFrequency, CarrNoise, Phase,
                 ModType, ModFrequency, ModFactor, ModNoise, nChannels,
                 **kwargs):
        '''
        This class is used to generate Carrier and Modulation Waveform and
        combine them as AM Modulation

        Parameters
        ----------
        :param:Fs: float
        :param:nSamples: int
        :param:Amplitude: float
        :param:CarrFrequency: float
        :param:CarrNoise: float
        :param:Phase: int
        :param:ModType: str
        :param:ModFrequency: float
        :param:ModFactor: float
        :param:ModNoise: float
        :param:**Kwargs: kwargs

        Returns
        -------
        None.

        '''

        t = np.arange(0, ((1/Fs)*(nSamples)), (1/Fs))
        AmpMod = Amplitude*ModFactor

        if ModType == 'sinusoidal':
            Modulation = AmpMod*np.cos(ModFrequency*2*np.pi*(t))
        if ModType == 'square':
            Modulation = AmpMod*signal.square(ModFrequency*2*np.pi*(t))

        Carrier = Amplitude*np.cos(CarrFrequency*2*np.pi*(t)+Phase)

        OutSignal = np.ones((nSamples, nChannels))
        for ic in range(nChannels):
            Carrier += np.real(np.random.normal(0,
                                                CarrNoise,
                                                Carrier.size
                                                ))
            Modulation += np.real(np.random.normal(0,
                                                   ModNoise,
                                                   Modulation.size
                                                   ))

            AMSignal = (1+Modulation)*Carrier
            OutSignal[:, ic] = AMSignal

        return OutSignal


class GenerationThread(Qt.QThread):
    NewGenData = Qt.pyqtSignal()

    def __init__(self, tInterrupt, **kwargs):
        '''
        Initialation of the Thread for Generation

        Parameters
        ----------
        :param SigConfig: dictionary, contains all variables related with
                          signal configuration
        SigConfig : dictionary
                    {'Fs': 2000000.0,
                     'nSamples': 20000,
                     'tInterrupt': 0.01,
                     'CarrType': 'sinusoidal',
                     'CarrFrequency': 30000.0,
                     'Phase': 0,
                     'Amplitude': 0.05,
                     'CarrNoise': 0,
                     'ModType': 'sinusoidal',
                     'ModFrequency': 1000.0,
                     'ModFactor': 0.1,
                     'ModNoise': 0
                    }

        Returns
        -------
        None.

        '''
        # super permits to initialize the classes from which this class depends
        super(GenerationThread, self).__init__()
        self.SigConfigKwargs = kwargs
        self.tInterrupt = tInterrupt * 1000

    def run(self):
        '''
        Run function in threads is the loop that will start when thread is
        started.

        Returns
        -------
        None.

        '''
        # while True statement is used to generate a lopp in the run function
        # so, while the thread is active, the while loop is running
        while True:
            # the generation is started
            # The dictionary SigConfig is passed to SignalGenerator class as
            # kwargs, this means you can send the full dictionary and only use
            # the variables in which you are interesed in
            self.OutData = GenAMSignal(**self.SigConfigKwargs)

            self.NewGenData.emit()

            Qt.QThread.msleep(self.tInterrupt)


