# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 11:42:44 2020

@author: lucia
"""

import numpy as np
import pickle

from PyQt5.QtWidgets import QFileDialog
import pyqtgraph.parametertree.parameterTypes as pTypes


ConfigSweepsParams = {'name': 'SweepsConfig',
                      'type': 'group',
                    'children': ({'name': 'Start/Stop Sweep',
                                  # 'title': 'Start Sweep',
                                  'type': 'action', },
                                 {'name': 'Pause Sweep',
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
            if Config.name() == 'Pause Sweep':
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
