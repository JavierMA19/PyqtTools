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

        # Event for debug print of changes
        self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)

        # First call of some events for initializations
        self.on_gennChannels_changed()
        self.on_genFs_changed()

        # Event of main button start and stop
        self.btnStart.clicked.connect(self.on_btnStart)

        # Add tree structure to main window
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(550, 10, 400, 700)
        self.setWindowTitle('MainWindow')
        
  
    
        # self.Parameters.addChild(self.SigParams)
        # You can create variables of the main class with the values of
        # an specific tree you have create in a concret GrouParameter class
        # self.GenParams = self.SigParams.param('GeneralConfig')
        # self.CarrParams = self.SigParams.param('CarrierConfig')
        # self.ModParams = self.SigParams.param('ModConfig')

# # #############################Save##############################
#         # With this line, it is initize the group of parameters that are
#         # going to be part of the full GUI
#         self.Parameters = Parameter.create(name='params',
#                                            type='group',
#                                            children=(self.SaveStateParams,))
# # #############################File##############################
#         self.FileParams = FileMod.SaveFileParameters(QTparent=self,
#                                                      name='Record File')
#         self.Parameters.addChild(self.FileParams)



# # #############################Plots##############################
#         self.PsdPlotParams = PSDPltPars(name='PSD Plot Options')
#         self.PsdPlotParams.param('Fs').setValue(self.SigParams.Fs.value())
#         self.PsdPlotParams.param('Fmin').setValue(50)
#         self.PsdPlotParams.param('nAvg').setValue(50)
#         self.Parameters.addChild(self.PsdPlotParams)

        
#         # self.PlotParams.SetChannels({'Row1': 2,})
#         self.PlotParams.param('Fs').setValue(self.SigParams.Fs.value())

#         self.Parameters.addChild(self.PlotParams)
        
# # ############################Instancias for Changes######################
#         # Statement sigTreeStateChanged.connect is used to execute a function
#         # if any parameter of the indicated tree changes
#         self.GenParams.sigTreeStateChanged.connect(self.on_GenConfig_changed)
#         self.CarrParams.sigTreeStateChanged.connect(self.on_CarrierConfig_changed)
#         self.ModParams.sigTreeStateChanged.connect(self.on_ModConfig_changed)
        
#         self.PlotParams.param('PlotEnable').sigValueChanged.connect(self.on_PlotEnable_changed)
#         self.PlotParams.param('RefreshTime').sigValueChanged.connect(self.on_RefreshTimePlt_changed)
#         self.PlotParams.param('ViewTime').sigValueChanged.connect(self.on_SetViewTimePlt_changed)
#         self.PsdPlotParams.param('PSDEnable').sigValueChanged.connect(self.on_PSDEnable_changed)

# # ############################GuiConfiguration##############################
#         # Is the same as before functions but for 'Parameters' variable,
#         # which conatins all the trees of all the Gui, so on_Params_changed
#         # will be execute for any change in the Gui

    def on_gennChannels_changed(self):
        self.PlotParams.SetChannels(self.SigGenParams.GetChannels())

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

        
# # ############################Changes Emits##############################
#     def on_GenConfig_changed(self):
#         '''
#         This function is used to change the Sampling frequency value and 
#         nSamples value of plots to the ones specified in the signal configuration

#         '''
#         # All Fs values are changed with SigParams.Fs value
#         self.PlotParams.param('Fs').setValue(self.SigParams.Fs.value())
#         self.PsdPlotParams.param('Fs').setValue(self.SigParams.Fs.value())
#         self.PlotParams.param('ViewBuffer').setValue(
#             self.SigParams.nSamples.value()/self.SigParams.Fs.value())
        
#     def on_CarrierConfig_changed(self):
#         '''
#         This function is used to change the Carrier parameters while the
#         program is running

#         '''
#         # It is checked if the Thread of generation is active
#         if self.threadGeneration is not None:
#             # Gen Carrier function is called and appropiate parameters are
#             # sent to generate the new waveform
#             SigGen.GenAMSignal(**self.SigParams.Get_SignalConf_Params())

#     def on_ModConfig_changed(self):
#         '''
#         This function is used to change the Modulation parameters while the
#         program is running

#         '''
#         # It is checked if the Thread of generation is active
#         if self.threadGeneration is not None:
#             if self.ModParams.param('ModType').value() == 'sinusoidal':
#                 # GenModulation for a sinusoidal waveform function is called
#                 # and appropiate parameters are sent to generate the new
#                 # waveform
#                 SigGen.GenAMSignal(**self.SigParams.Get_SignalConf_Params())

#             if self.ModParams.param('ModType').value() == 'square':
#                 # GenModulation for an square waveform function is called
#                 # and appropiate parameters are sent to generate the new
#                 # waveform
#                 SigGen.GenAMSignal(**self.SigParams.Get_SignalConf_Params())

#     def on_PSDEnable_changed(self):
#         '''
#         This function is used to Generate or destroy the PSD plot 

#         '''
#         if self.threadGeneration is not None:
#             self.Gen_Destroy_PsdPlotter()

#     def on_PlotEnable_changed(self):
#         '''
#         This function is used to Generate or destroy the Time plot 

#         '''
#         if self.threadGeneration is not None:
#             self.Gen_Destroy_Plotters()

#     def on_RefreshTimePlt_changed(self):
#         '''
#         This function is used to change the refresh time of Time Plot

#         '''
#         if self.threadPlotter is not None:
#             self.threadPlotter.SetRefreshTime(self.PlotParams.param('RefreshTime').value())

#     def on_SetViewTimePlt_changed(self):
#         '''
#         This function is used to change the View time of Time Plot

#         '''
#         if self.threadPlotter is not None:
#             self.threadPlotter.SetViewTime(self.PlotParams.param('ViewTime').value())

    def on_btnStart(self):
        """Start/Stop the signal generation."""

        if self.threadGeneration is None:
            # Configure genration
            SigGenKwargs = self.SigGenParams.Get_SignalConf_Params()
            self.threadGeneration = SigGen.GenerationThread(**SigGenKwargs)
            self.threadGeneration.NewGenData.connect(self.on_NewSample)

            if self.PlotParams.param('PlotEnable').value():
                Pltkw = self.PlotParams.GetParams()
                self.threadPlotter = TimePlt(**Pltkw)
                self.threadPlotter.start()

            if self.PsdPlotParams.param('PlotEnable').value():
                PSDKwargs = self.PsdPlotParams.GetParams()
                ChannelConf = self.PlotParams.GetParams()['ChannelConf']
                self.threadPsdPlotter = PSDPlt(ChannelConf=ChannelConf,
                                               nChannels=Pltkw['nChannels'],
                                               **PSDKwargs)
                self.threadPsdPlotter.start()

            if self.FileParams.param('Enabled').value():
                FilekwArgs = {'FileName': self.FileParams.FilePath(),
                              'nChannels': self.SigGenParams.nChannels.value(),
                              'Fs': None,
                              'ChnNames': None,
                              'MaxSize': None,
                              'dtype': 'float',
                              }
                self.threadSave = self.FileMod.DataSavingThread(**FilekwArgs)

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

# # #############################Savind Files##############################
#     def SaveFiles(self):
#         '''
#         This function is executed to initialize and start save thread
#         '''
#         # The File Name is obtained from the GUI File Path
#         FileName = self.FileParams.param('File Path').value()
#         # If the is no file name, No file is printed
#         if FileName == '':
#             print('No file')
#         # If there is file name
#         else:
#             # It is checked if the file exists, if it exists is removed
#             if os.path.isfile(FileName):
#                 print('Remove File')
#                 os.remove(FileName)
#             # Maximum size alowed for the new file is obtained from the GUI
#             MaxSize = self.FileParams.param('MaxSize').value()
#             # The threas is initialized
#             self.threadSave = FileMod.DataSavingThread(FileName=FileName,
#                                                        nChannels=1,
#                                                        MaxSize=MaxSize,
#                                                        Fs = self.SigParams.Fs.value(),
#                                                        tWait=self.SigParams.tInterrput.value(),
#                                                        dtype='float')
#             # And then started
#             self.threadSave.start()

# ############################MAIN##############################

if __name__ == '__main__':
    app = Qt.QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec_()
