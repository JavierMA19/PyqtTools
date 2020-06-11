# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 15:18:09 2020

@author: lucia
"""

from __future__ import print_function
import os

import numpy as np
import time

from PyQt5 import Qt

from pyqtgraph.parametertree import Parameter, ParameterTree

import PyqtTools.SignalGeneration as SigGen

import PyqtTools.FileModule as FileMod
from PyqtTools.PlotModule import Plotter as TimePlt
from PyqtTools.PlotModule import PlotterParameters as TimePltPars
from PyqtTools.PlotModule import PSDPlotter as PSDPlt
from PyqtTools.PlotModule import PSDParameters as PSDPltPars


class MainWindow(Qt.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setFocusPolicy(Qt.Qt.WheelFocus)
        layout = Qt.QVBoxLayout(self)

        self.btnStart = Qt.QPushButton("Start Gen and Adq!")
        layout.addWidget(self.btnStart)

        self.ResetGraph = Qt.QPushButton("Reset Graphics")
        layout.addWidget(self.ResetGraph)

        # Set threads as None
        self.threadGeneration = None
        self.threadPlotter = None
        self.threadPsdPlotter = None
        self.threadSave = None

        # create instances for each parametree class
        self.SigGenParams = SigGen.SignalConfigTree(QTparent=self,
                                                    name='SigGen',
                                                    title='Signal Generation')

        self.PlotParams = TimePltPars(name='TimePlt',
                                      title='Time Plot Options')

        self.PsdPlotParams = PSDPltPars(name='PSDPlt',
                                        title='PSD Plot Options')

        self.SaveStateParams = FileMod.SaveSateParameters(QTparent=self,
                                                          name='FileState',
                                                          title='Save/load config')

        self.FileParams = FileMod.SaveFileParameters(QTparent=self,
                                                     name='FileDat',
                                                     title='Save data')

        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.SigGenParams,
                                                     self.PlotParams,
                                                     self.PsdPlotParams,
                                                     self.SaveStateParams,
                                                     self.FileParams,
                                                     ))

        # Connect event for managing event
        self.SigGenParams.Fs.sigValueChanged.connect(self.on_genFs_changed)
        self.SigGenParams.nChannels.sigValueChanged.connect(self.on_gennChannels_changed)
        self.SigGenParams.sigTreeStateChanged.connect(self.on_SigGen_changed)

        self.PsdPlotParams.NewConf.connect(self.on_NewPSDConf)

        self.PlotParams.NewConf.connect(self.on_NewPlotConf)

        # Event for debug print of changes
        # self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)

        # First call of some events for initializations
        self.on_gennChannels_changed()
        self.on_genFs_changed()

        # Event of main button start and stop
        self.btnStart.clicked.connect(self.on_btnStart)
        self.ResetGraph.clicked.connect(self.on_ResetGraph)

        # Add tree structure to main window
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(550, 10, 400, 700)
        self.setWindowTitle('MainWindow')       

    def on_Params_changed(self, param, changes):
        """Print changes in tree parameter for debug porpouses."""
        print("tree changes:")
        for param, change, data in changes:
            path = self.Parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        print('  parameter: %s' % childName)
        print('  change:    %s' % change)
        print('  data:      %s' % str(data))
        print('  ----------')

    def on_gennChannels_changed(self):
        self.PlotParams.SetChannels(self.SigGenParams.GetChannels())
        self.PsdPlotParams.ChannelConf = self.PlotParams.ChannelConf
        nChannels = self.PlotParams.param('nChannels').value()
        self.PsdPlotParams.param('nChannels').setValue(nChannels)

    def on_SigGen_changed(self):
        if self.threadGeneration is not None:
            SigGenKwargs = self.SigGenParams.Get_SignalConf_Params()
            self.threadGeneration.SigConfigKwargs = SigGenKwargs

    def on_genFs_changed(self):
        Fs = self.SigGenParams.Fs.value()
        self.PlotParams.param('Fs').setValue(Fs)
        self.PsdPlotParams.param('Fs').setValue(Fs)

    def on_NewPSDConf(self):
        if self.threadPsdPlotter is not None:
            nFFT = self.PsdPlotParams.param('nFFT').value()
            nAvg = self.PsdPlotParams.param('nAvg').value()
            self.threadPsdPlotter.InitBuffer(nFFT=nFFT, nAvg=nAvg)

    def on_NewPlotConf(self):
        if self.threadPlotter is not None:
            ViewTime = self.PlotParams.param('ViewTime').value()
            self.threadPlotter.SetViewTime(ViewTime)        
            RefreshTime = self.PlotParams.param('RefreshTime').value()
            self.threadPlotter.SetRefreshTime(RefreshTime)        

    def on_ResetGraph(self):
        if self.threadGeneration is None:
            return

        # Plot and PSD threads are stopped
        if self.threadPlotter is not None:
            self.threadPlotter.stop()
            self.threadPlotter = None

        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.stop()
            self.threadPsdPlotter = None

        if self.PlotParams.param('PlotEnable').value():
            Pltkw = self.PlotParams.GetParams()
            self.threadPlotter = TimePlt(**Pltkw)
            self.threadPlotter.start()

        if self.PsdPlotParams.param('PlotEnable').value():
            PSDKwargs = self.PsdPlotParams.GetParams()
            self.threadPsdPlotter = PSDPlt(**PSDKwargs)
            self.threadPsdPlotter.start()

    def on_btnStart(self):
        """Start/Stop the signal generation."""

        if self.threadGeneration is None:
            # Configure genration
            SigGenKwargs = self.SigGenParams.Get_SignalConf_Params()
            self.threadGeneration = SigGen.GenerationThread(**SigGenKwargs)
            self.threadGeneration.NewGenData.connect(self.on_NewSample)

            if self.FileParams.param('Enabled').value():
                FilekwArgs = {'FileName': self.FileParams.FilePath(),
                              'nChannels': self.SigGenParams.nChannels.value(),
                              'Fs': None,
                              'ChnNames': None,
                              'MaxSize': None,
                              'dtype': 'float',
                              }
                self.threadSave = self.FileMod.DataSavingThread(**FilekwArgs)

            self.on_ResetGraph()

            # Start generation
            self.OldTime = time.time()
            self.threadGeneration.start()
            self.btnStart.setText("Stop Gen")
        else:
            # stopped is printed in the console
            print('Stopped')
            # Thread is terminated and set to None
            self.threadGeneration.NewGenData.disconnect()
            self.threadGeneration.terminate()
            self.threadGeneration = None
            # Plot and PSD threads are stopped
            if self.threadPlotter is not None:
                self.threadPlotter.stop()
                self.threadPlotter = None

            if self.threadPsdPlotter is not None:
                self.threadPsdPlotter.stop()
                self.threadPsdPlotter = None

            # Also save thread is stopped
            if self.threadSave is not None:
                self.threadSave.stop()
                self.threadSave = None
            # Button text is changed again
            self.btnStart.setText("Start Gen and Adq!")

    def on_NewSample(self):
        """To call when new data ready to read."""

        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        # Debug print of interruption time
        print('Sample time', Ts)

        # pass new data to running threads
        if self.threadSave is not None:
            self.threadSave.AddData(self.threadGeneration.OutData)
            
        if self.threadPlotter is not None:
            self.threadPlotter.AddData(self.threadGeneration.OutData)

        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.AddData(self.threadGeneration.OutData)

    def Gen_Destroy_PsdPlotter(self):
        '''
        This function is executed to initialize and start or destroy PSD plot
        '''
        # If PSD plot thread does not exist
        if self.threadPsdPlotter is None:
            # And the plot enable checkbox is selected
            if self.PsdPlotParams.param('PSDEnable').value() is True:
                # A dictionary obtained with Get Params function is saved
                PlotterKwargs = self.PlotParams.GetParams()
                # And is sent to PSDPlotter thread to initialize it
                self.threadPsdPlotter = PSDPlt.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                          nChannels=1,
                                                          **self.PsdPlotParams.GetParams())
                # Then thread is started
                self.threadPsdPlotter.start()
        # If PSD plot thread exists
        if self.threadPsdPlotter is not None:
            # And plot enable checkbox is not selected
            if self.PsdPlotParams.param('PSDEnable').value() is False:
                # The thread is stopped and set to None
                self.threadPsdPlotter.stop()
                self.threadPsdPlotter = None

if __name__ == '__main__':
    app = Qt.QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec_()
