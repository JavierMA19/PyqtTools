#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 23:29:34 2021

@author: aguimera
"""

import pickle
import pyqtgraph as pg
from PyqtTools.PlotModule import PgPlotWindow
from PyQt5 import Qt
from PyQt5 import QtGui
import PyGFETdb.DataStructures as FetStruct
import numpy as np
import itertools 
import time
from scipy import interpolate


class CharactPlotter(Qt.QThread):
    PSDInterpolationPoints = 100

    def __init__(self, DevDCVals, DevACVals=None):
        super(CharactPlotter, self).__init__()
        self.Wind = PgPlotWindow()
        self.Refresh = False
        self.OldSelCurve = None

        self.PlotSel = self.Wind.pgLayout.addPlot(col=0,
                                                 row=0,
                                                 )
        self.PlotAC = self.Wind.pgLayout.addPlot(col=0,
                                                 row=1,
                                                 )
        self.PlotDC = self.Wind.pgLayout.addPlot(col=1,
                                                 row=0,
                                                 rowspan=2,
                                                 colspan=1,
                                                 )

        self.PlotDC.setLabel('left', 'Ids', units='A')
        self.PlotDC.setLabel('bottom', 'Vgs', units='V')
        self.PlotDC.showGrid(x=True, y=True)

        self.PlotAC.setLabel('left', 'PSD [A**2/Hz]')
        self.PlotAC.setLabel('bottom', 'Frequency [Hz]')
        self.PlotAC.getAxis('left').enableAutoSIPrefix(False)
        self.PlotAC.getAxis('bottom').enableAutoSIPrefix(False)
        self.PlotAC.showGrid(x=True, y=True)

        self.PlotSel.setLabel('left', 'PSD [A**2/Hz]')
        self.PlotSel.setLabel('bottom', 'Frequency [Hz]')
        self.PlotSel.getAxis('left').enableAutoSIPrefix(False)
        self.PlotSel.getAxis('bottom').enableAutoSIPrefix(False)
        self.PlotSel.showGrid(x=True, y=True)
        self.PlotSel.setTitle('No Selection (Click to select)')

        self.DevDCVals = DevDCVals
        self.DevACVals = DevACVals
        chn = list(self.DevDCVals.keys())[0]
        self.Vds = self.DevDCVals[chn]['Vds']
        self.Vgs = self.DevACVals[chn]['Vgs']

        # Create channels pen dictionary
        nChannels = len(self.DevDCVals)
        self.ChPens = {}
        for ind, chn in enumerate(self.DevDCVals.keys()):
            self.ChPens[chn] = pg.mkPen(color=(ind, 1.3*nChannels),
                                        width=1.5)

        # Create Vgs pen dictionary
        nVgs = len(self.Vgs)
        self.VgsPens = {}
        for vgi, vg in enumerate(self.Vgs):
            self.VgsPens[vgi] = pg.mkPen(color=(vgi, 1.3*nVgs),
                                         width=1.5)

        # Init Ids curves
        T1 = time.time()
        self.IdsCurves = []
        for vdi, vd in enumerate(self.Vds):
            for chn in self.DevDCVals.keys():            
                c = pg.PlotCurveItem(parent=self.PlotDC,
                                     pen=self.ChPens[chn],
                                     clickable=True,
                                     name=chn)   
                c.opts['vdi'] = vdi
                c.opts['vds'] = vd
                self.IdsCurves.append(c)
        # Add curves to plot
        for c in self.IdsCurves:
            self.PlotDC.addItem(c)
            c.sigClicked.connect(self.on_IdsClicked)
        print('create + add', time.time() - T1)

        # Init PSD Plot
        T1 = time.time()
        # Init PSD curves
        self.PSDCurves = []
        self.SelPSDCurves = []
        if self.DevACVals is not None:
            chn = list(self.DevACVals.keys())[0]
            self.Fpsd = self.DevACVals[chn]['Fpsd']
            self.FpsdLog = np.logspace(np.log10(self.Fpsd[1]),
                                       np.log10(self.Fpsd[-2]),
                                       self.PSDInterpolationPoints)
 
            for chn in self.DevACVals.keys():
                c = pg.PlotDataItem(pen=self.ChPens[chn],
                                     name=chn)                
                self.PSDCurves.append(c)
            for c in self.PSDCurves:
                self.PlotAC.addItem(c)
            self.PlotAC.setLogMode(True, True)
            
            for vdi, vd in enumerate(self.Vds):
                for vgi, vg in enumerate(self.Vgs):
                    c = pg.PlotDataItem(pen=self.VgsPens[vgi],
                                        name=vgi)
                    c.opts['vdi'] = vdi
                    c.opts['vds'] = vd
                    c.opts['vgi'] = vgi
                    c.opts['vgs'] = vg
                    self.SelPSDCurves.append(c)
            for c in self.SelPSDCurves:
                self.PlotSel.addItem(c)
            self.PlotSel.setLogMode(True, True)           
            
        print('create + add', time.time() - T1) 

    def on_IdsClicked(self, SelCur):
        chn = SelCur.opts['name']
        title = 'Selected {} Vds {}'.format(chn,
                                            SelCur.opts['vds'])
        self.PlotSel.setTitle(title)
        if self.OldSelCurve is not None:
            self.OldSelCurve.opts['pen'] = self.OldSelPen        
        self.OldSelCurve = SelCur
        self.OldSelPen = SelCur.opts['pen']
        SelCur.setPen('w', width=3)

        data = self.DevACVals[chn]['PSD']
        for c in self.SelPSDCurves:
            sVdi = 'Vd' + str(c.opts['vdi'])
            dat = data[sVdi][c.opts['vgi'], :]
            pltpsd = interpolate.interp1d(self.Fpsd, dat)(self.FpsdLog)
            c.setData(self.FpsdLog, pltpsd)        
        

    def run(self, *args, **kwargs):
        while True:
            if self.Refresh:                
                for c in self.IdsCurves:
                    Ids = self.DevDCVals[c.opts['name']]['Ids']
                    dat = Ids[:, c.opts['vdi']]
                    c.setData(self.Vgs, dat)                        

                sVdi = 'Vd' + str(self.VdInd)
                for c in self.PSDCurves:
                    chn = c.opts['name']
                    dat = self.DevACVals[chn]['PSD'][sVdi][self.VgInd, :]
                    pltpsd = interpolate.interp1d(self.Fpsd, dat)(self.FpsdLog)
                    c.setData(self.FpsdLog, pltpsd)

                self.Refresh = False
            else:
                Qt.QThread.msleep(100)


    def RefreshPlot(self, VgInd, VdInd):
        if self.Refresh:
            print('overlap')
        self.Refresh = True
        self.VgInd = VgInd
        self.VdInd = VdInd


class GenerationThread(Qt.QThread):
    NewGenData = Qt.pyqtSignal()

    def __init__(self):
        super(GenerationThread, self).__init__()
        
        TestFile = open('../Test/TestData.pkl', 'rb')
        self.DevDCVals, self.DevACVals = pickle.load(TestFile, encoding='latin')
        
        chn = list(self.DevDCVals.keys())[0]
        # self.Vds = self.DevDCVals[chn]['Vds']
        self.Vgs = self.DevDCVals[chn]['Vgs']
        
        # nChannels = 8
        # self.Vds = np.array([0.15, 0.1, 0.05])
        # self.IdsOffVds = [3, 2, 1]

        nChannels = 1024
        self.Vds = np.array([0.05, ])
        self.IdsOffVds = [1, ]
        
        ChNames = ['Ch' + str(i) for i in range(nChannels)]               
              
        self.IdsRnd = {}
        for Chn in ChNames:
            self.IdsRnd[Chn] = np.random.rand()*2e-6

        self.PSDRnd = {}
        for Chn in ChNames:
            self.PSDRnd[Chn] = np.random.rand()*1e-19
        
        self.MeasDC = FetStruct.InitDCRecord(nVds=self.Vds,
                                             nVgs=self.Vgs,
                                             ChNames=ChNames,
                                             Gate=False)

        self.Fpsd = self.DevACVals[chn]['Fpsd']
        self.MeasAC = FetStruct.InitACRecord(nVds=self.Vds,
                                             nVgs=self.Vgs,
                                             ChNames=ChNames,
                                             nFpsd=self.Fpsd,
                                             nFgm=np.array([]),
                                             )
        
    def run(self):
        '''
        Run function in threads is the loop that will start when thread is
        started.

        Returns
        -------
        None.

        '''
    
        for vdi, vd in enumerate(self.Vds):
            sVdi = 'Vd' + str(vdi)
            for vgi, vg in enumerate(self.Vgs):
                DCvals = itertools.cycle([data for chn, data in self.DevDCVals.items()])
                ACvals = itertools.cycle([data for chn, data in self.DevACVals.items()])
                
                for chn, data in self.MeasDC.items():
                    ids = next(DCvals)['Ids'][vgi, 0]
                    ids = (ids + self.IdsRnd[chn]) * self.IdsOffVds[vdi]
                    self.MeasDC[chn]['Ids'][vgi, vdi] = ids
      
                for chn, data in self.MeasAC.items():
                    psd = next(ACvals)['PSD']['Vd0'][vgi, :]
                    psd = (psd + self.PSDRnd[chn])
                    self.MeasAC[chn]['PSD'][sVdi][vgi, :] = psd
    
                self.VgInd = vgi
                self.VdInd = vdi
                self.NewGenData.emit()
                Qt.QThread.msleep(5000)
                


class MainWindow(Qt.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setFocusPolicy(Qt.Qt.WheelFocus)
        layout = Qt.QVBoxLayout(self)

        self.btnStart = Qt.QPushButton("Start Gen and Adq!")
        layout.addWidget(self.btnStart)
        self.btnStart.clicked.connect(self.on_btnStart)

    def on_btnStart(self):
        print('Init Generation')        
        T1 = time.time()
        self.GenData = GenerationThread()
        self.GenData.NewGenData.connect(self.NewData)
        print('Init Generation ', time.time()-T1)
        
        print('Init Plotter')
        T1 = time.time()
        self.CharPlot = CharactPlotter(self.GenData.MeasDC, self.GenData.MeasAC)    
        print('Init Plotter ', time.time()-T1)
        
        print('Start Threads')
        self.CharPlot.start()        
        self.GenData.start()

    def NewData(self):
        print('NewData')
        self.CharPlot.RefreshPlot(VgInd=self.GenData.VgInd,
                                  VdInd=self.GenData.VdInd)
        
        
           
if __name__ == '__main__':
   
    app = Qt.QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec_()  

    

    


    



