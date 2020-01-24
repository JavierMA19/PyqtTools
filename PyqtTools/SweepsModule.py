# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 09:25:47 2019

@author: Lucia
"""

import pyqtgraph.parametertree.parameterTypes as pTypes

import numpy as np

SweepsParams = {'name': 'SweepsConfig',
                'type': 'group',
                'children': ({'name': 'Enable',
                              'type': 'bool',
                              'value': True, },
                             {'name': 'VgSweep',
                                      'type': 'group',
                                      'children': ({'name': 'Vgs_init',
                                                    'type': 'float',
                                                    'value': 0,
                                                    'siPrefix': True,
                                                    'suffix': 'V'},
                                                   {'name': 'Vgs_final',
                                                    'type': 'float',
                                                    'value': 0.4,
                                                    'siPrefix': True,
                                                    'suffix': 'V'},
                                                   {'name': 'NSweeps',
                                                    'type': 'int',
                                                    'value': 20,
                                                    'siPrefix': True,
                                                    'suffix': 'Sweeps'},
#                                                   {'name': 'Vstep',
#                                                    'type': 'float',
#                                                    'value': -0.01,
#                                                    'siPrefix': True,
#                                                    'suffix': 'V'},
                                                   )},
                             {'name': 'VdSweep',
                              'type': 'group',
                              'children': ({'name': 'Vds_init',
                                            'type': 'float',
                                            'value': 0.05,
                                            'siPrefix': True,
                                            'suffix': 'V'},
                                           {'name': 'Vds_final',
                                            'type': 'float',
                                            'value': 0.05,
                                            'siPrefix': True,
                                            'suffix': 'V'},
                                           {'name': 'NSweeps',
                                            'type': 'int',
                                            'value': 1,
                                            'siPrefix': True,
                                            'suffix': 'Sweeps'},
#                                           {'name': 'Vstep',
#                                            'type': 'float',
#                                            'value': 0.01,
#                                            'siPrefix': True,
#                                            'suffix': 'V'},
                                           )},
                             {'name': 'MaxSlope',
                              'title': 'Maximum Slope',
                              'type': 'list',
                              'values':[5e-8,
                                        1e-6,
                                        5e-7,
                                        1e-7,
                                        1e-8,
                                        5e-9,
                                        1e-9,
                                        1e-10,
                                        1
                                        ]},
                             {'name': 'TimeOut',
                              'title': 'Max Time for Stabilization',
                              'type': 'int',
                              'value': 10,
                              'siPrefix': True,
                              'suffix': 's'},
                             )}


class SweepsConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChild(SweepsParams)
        self.SwConfig = self.param('SweepsConfig')

        self.VgParams = self.SwConfig.param('VgSweep')
        self.VdParams = self.SwConfig.param('VdSweep')
        # self.DevCond = self.SwConfig.param('MaxSlope')

        self.VgParams.sigTreeStateChanged.connect(self.on_Sweeps_Changed)
        self.VdParams.sigTreeStateChanged.connect(self.on_Sweeps_Changed)
        # self.DevCond.sigTreeStateChanged.connect(self.on_Sweeps_Changed)
        self.on_Sweeps_Changed()

    def on_Sweeps_Changed(self):
#        self.VgSweepVals = np.arange(self.VgParams.param('Vinit').value(),
#                                     self.VgParams.param('Vfinal').value(),
#                                     self.VgParams.param('Vstep').value())
#
#        self.VdSweepVals = np.arange(self.VdParams.param('Vinit').value(),
#                                     self.VdParams.param('Vfinal').value(),
#                                     self.VdParams.param('Vstep').value())
        self.VgSweepVals = np.linspace(self.VgParams.param('Vgs_init').value(),
                                       self.VgParams.param('Vgs_final').value(),
                                       self.VgParams.param('NSweeps').value())

        self.VdSweepVals = np.linspace(self.VdParams.param('Vds_init').value(),
                                       self.VdParams.param('Vds_final').value(),
                                       self.VdParams.param('NSweeps').value())

        # self.DevCondition = self.DevCond.value()

    def GetSweepsParams(self):
        '''Returns de parameters to do the sweeps
           SwConfig={'Enable': True,
                     'VgSweep': array([ 0. , -0.1, -0.2, -0.3]),
                     'VdSweep': array([0.1]),
                     'MaxSlope': 1e-9,
                     'TimeOut': 10
                     }
        '''
        SwConfig = {}
        for Config in self.SwConfig.children():

            if Config.name() == 'VgSweep':
                SwConfig[Config.name()] = self.VgSweepVals
                continue
            if Config.name() == 'VdSweep':
                SwConfig[Config.name()] = self.VdSweepVals
                continue
            SwConfig[Config.name()] = Config.value()
        return SwConfig
