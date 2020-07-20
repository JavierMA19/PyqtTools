#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 18:44:39 2019

@author: aguimera
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph as pg
import copy
from PyQt5 import Qt
import numpy as np
from scipy.signal import welch
import math


ChannelPars = {'name': 'Ch01',
               'type': 'group',
               'children': [{'name': 'name',
                             'type': 'str',
                             'value': 'ChXX'},
                            {'name': 'Enable',
                             'type': 'bool',
                             'value': False, },
                            {'name': 'Window',
                             'limits': (0, 32),
                             'type': 'int',
                             'value': 0, },
                            {'name': 'Axis',
                             'type': 'int',
                             'limits': (0, 32),
                             'value': 0, },
                            {'name': 'Offset',
                             'type': 'float',
                             'value': 0, },
                            {'name': 'color',
                             'type': 'color',
                             'value': "FFF"},
                            {'name': 'width',
                             'type': 'float',
                             'value': 0.5,
                             'limits': (0, 5), },
                            {'name': 'Input',
                             'type': 'int',
                             'readonly': True,
                             'value': 1, }]
               }

PlotterPars = ({'name': 'Fs',
                'readonly': True,
                'type': 'float',
                'siPrefix': True,
                'suffix': 'Hz'},
               {'name': 'PlotEnable',
                'title': 'Plot Enable',
                'type': 'bool',
                'value': True},
               {'name': 'nChannels',
                'readonly': True,
                'type': 'int',
                'value': 1},
               {'name': 'SelIndex',
                'title': 'Inputs indexes',
                'type': 'str',
                'value': '1:3,'},
               {'name': 'Indexes',
                'title': 'Selected Inputs indexes',
                'readonly': True,
                'type': 'str'},
               {'name': 'ViewBuffer',
                'type': 'float',
                'value': 30,
                'step': 1,
                'limits': (0.01, 1e3),
                'siPrefix': True,
                'suffix': 's'},
               {'name': 'ViewTime',
                'type': 'float',
                'value': 10,
                'limits': (1e-3, 1e3),
                'step': 1,
                'siPrefix': True,
                'suffix': 's'},
               {'name': 'RefreshTime',
                'type': 'float',
                'value': 4,
                'step': 1,
                'limits': (1, 1e3),
                'siPrefix': True,
                'suffix': 's'},
               {'name': 'Windows',
                'type': 'int',
                'value': 1,
                'limits': (1, 16),
                },
               {'name': 'IncOffset',
                'title': 'Incremental Offset',
                'type': 'float',
                'value': 0,
                'siPrefix': True,
                },
               {'name': 'ChsAxis',
                'title': 'Channels per axis',
                'type': 'int',
                'value': 1,
                'limits': (1, 100),
                'siPrefix': True,
                },
               {'name': 'ShowSamples',
                'title': 'Show Samples',
                'type': 'bool',
                'value': False,
                },
               {'name': 'EnableAll',
                'title': 'Enable all channels',
                'type': 'action',
                },
               {'name': 'DisableAll',
                'title': 'Disable all channels',
                'type': 'action',
                },
               {'name': 'Channels',
                'type': 'group',
                'children': []},)


DiscarParamsPlt = ('Channels',
                   'Windows',
                   'PlotEnable',
                   'EnableAll',
                   'DisableAll',
                   'IncOffset',
                   'SelIndex',
                   'Indexes',
                   'ChsAxis',
                   )


class PlotterParameters(pTypes.GroupParameter):
    NewConf = Qt.pyqtSignal()

    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChildren(PlotterPars)
        self.param('Windows').sigValueChanged.connect(self.on_WindowsChange)
        self.param('IncOffset').sigValueChanged.connect(self.on_SetOffset)
        self.param('EnableAll').sigActivated.connect(self.on_EnableAll)
        self.param('DisableAll').sigActivated.connect(self.on_DisableAll)
        self.param('ViewTime').sigValueChanged.connect(self.on_ViewTime)
        self.param('SelIndex').sigValueChanged.connect(self.on_SelIndex)
        self.param('RefreshTime').sigValueChanged.connect(self.on_RefreshTime)
        self.param('ChsAxis').sigValueChanged.connect(self.on_ChsAxis)

    def on_RefreshTime(self):
        self.NewConf.emit()
        
    def on_ViewTime(self):
        vt = self.param('ViewTime').value()
        vb = self.param('ViewBuffer').value()
        if vt > vb:
            self.param('ViewTime').setValue(vb)
        self.NewConf.emit()

    def on_SetOffset(self):
        Windows = {}
        ChsDistribution, _, _ = self.GetChannelDistribution()
        
        incoff = self.param('IncOffset').value()
        offsets = {}
        for win, axs in ChsDistribution.items():
            for ax, chs in axs.items():
                off = 0
                for chn in chs:                    
                    offsets[chn] = off
                    off += incoff

        for p in self.param('Channels').children():
            if p.param('Enable').value():
                p.param('Offset').setValue(offsets[p['name']])
                
    def on_EnableAll(self):
        for p in self.param('Channels').children():
            p.param('Enable').setValue(True)

    def on_DisableAll(self):
        for p in self.param('Channels').children():
            p.param('Enable').setValue(False)   
       
    def on_ChsAxis(self):
        _ , ChannelConf, WinDist = self.GetChannelDistribution()
        
        chPAxis = self.param('ChsAxis').value()

        AxisDist = {}
        for win, chs in WinDist.items():            
            for ich, chn in enumerate(chs):
                AxisDist[chn] = int(ich/chPAxis)

        print(AxisDist, WinDist)
        for p in self.param('Channels').children():
            for pp in p.children():
                if pp.name() == 'Axis':
                    axs = AxisDist[p.name()]
                    pp.setValue(axs)

        self.on_SetOffset()

    def on_WindowsChange(self):
        # Assing window to each channel
        chs = self.param('Channels').children()
        chPWind = math.ceil(len(chs)/self.param('Windows').value())
        for ind, ch in enumerate(chs):            
            ch.child('Window').setValue(int(ind/chPWind))
       
        self.on_ChsAxis()
                
    def SetChannels(self, Channels):
        """
        Set the plotting channels.

        Parameters
        ----------
        Channels : Dictionary, where key is the channel name
                   and value is an integer which indicate the index of the
                   input data array.
        """      
        nChannels = len(Channels)

        self.param('nChannels').setValue(nChannels)
        chPWind = int(nChannels/self.param('Windows').value())
        Chs = []
        for chn, ind in Channels.items():
            Ch = copy.deepcopy(ChannelPars)
            pen = pg.mkPen((ind, 1.3*nChannels))
            Ch['name'] = chn
            Ch['children'][0]['value'] = chn
            Ch['children'][2]['value'] = int(ind//chPWind)
            Ch['children'][5]['value'] = pen.color()
            Ch['children'][7]['value'] = ind
            Chs.append(Ch)
            
        self.ChannelConf = Chs

    def on_SelIndex(self):
        strind = self.param('SelIndex').value()
        nChannels = self.param('nChannels').value()

        try:
            # strind = '0, 9, 2:8, 9:16:2'
            inds = []
            for parts in strind.split(','):
                raargs = []
                ra = parts.split(':')
                if len(ra) == 1:
                    inds.append(int(ra[0]))
                else:
                    for r in ra:
                        raargs.append(int(r))
                    for i in range(*raargs):
                        inds.append(i)
            inds = list(set(sorted(inds)))
            inds = [x for x in inds if x < nChannels]
            inds = [x for x in inds if x >= 0]
        except:
            print('Invalid parsing')
            return

        self.InputIndexs = inds
        self.param('Indexes').setValue(str(inds))

        self.param('Channels').clearChildren()
        
        nChannelsPlt = len(inds)
        Chs = []
        for ind, i in enumerate(inds):
            Ch = self.ChannelConf[i]
            pen = pg.mkPen((ind, 1.3*nChannelsPlt))
            Ch['children'][1]['value'] = True
            Ch['children'][5]['value'] = pen.color()
            Chs.append(Ch)
        
        self.param('Channels').addChildren(Chs)
        self.on_WindowsChange()

    def GetChannelDistribution(self):
        Windows = {}
        WinDist = {}
        for i in range(self.param('Windows').value()):
            Windows[i] = []
            WinDist[i] = []

        for p in self.param('Channels').children():
            if p['Enable']:
                Windows[p['Window']].append(p['Axis'])
                WinDist[p['Window']].append(p['name'])

        ChsDistribution = {}
        for win in range(self.param('Windows').value()):
            ChsDistribution[win] = {}
            for ax in set(Windows[win]):
                ChsDistribution[win][ax] = []

        ChannelConf = {}
        for p in self.param('Channels').children():
            chp = {}
            for pp in p.children():
                chp[pp.name()] = pp.value()
            ChannelConf[chp['name']] = chp.copy()
            if chp['Enable']:
                ChsDistribution[chp['Window']][chp['Axis']].append(chp['name'])
        
        return ChsDistribution, ChannelConf, WinDist

    def GetParams(self):
        PlotterKwargs = {}
        for p in self.children():
            if p.name() in DiscarParamsPlt:
                continue
            PlotterKwargs[p.name()] = p.value()

        ChsDistribution, ChannelConf, _ = self.GetChannelDistribution()
        PlotterKwargs['ChannelConf'] = ChannelConf
        PlotterKwargs['ChsDistribution'] = ChsDistribution

        return PlotterKwargs

class Buffer2D(np.ndarray):
    def __new__(subtype, Fs, nChannels, ViewBuffer,
                dtype=float, buffer=None, offset=0,
                strides=None, order=None, info=None):
        # Create the ndarray instance of our type, given the usual
        # ndarray input arguments.  This will call the standard
        # ndarray constructor, but return an object of our type.
        # It also triggers a call to InfoArray.__array_finalize__
        BufferSize = int(ViewBuffer*Fs)
        shape = (BufferSize, nChannels)
        obj = super(Buffer2D, subtype).__new__(subtype, shape, dtype,
                                               buffer, offset, strides,
                                               order)
        # set the new 'info' attribute to the value passed
        obj.counter = 0
        obj.totalind = 0
        obj.Fs = float(Fs)
        obj.Ts = 1/obj.Fs
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None:
            return
        self.bufferind = getattr(obj, 'bufferind', None)

    def AddData(self, NewData):        
        newsize = NewData.shape[0]
        if newsize > self.shape[0]:
            self[:, :] = NewData[:self.shape[0], :]
        else:
            self[0:-newsize, :] = self[newsize:, :]
            self[-newsize:, :] = NewData
        self.counter += newsize
        self.totalind += newsize

    def IsFilled(self):
        return self.counter >= self.shape[0]

    def GetTimes(self, Size):
        stop = self.Ts * self.totalind
        start = stop - self.Ts*Size
        times = np.arange(start, stop, self.Ts)
        return times[-Size:]

    def Reset(self):
        self.counter = 0


class PgPlotWindow(Qt.QWidget):
    def __init__(self):
        super(PgPlotWindow, self).__init__()
        layout = Qt.QVBoxLayout(self) #crea el layout
        self.pgLayout = pg.GraphicsLayoutWidget()
        self.pgLayout.setFocusPolicy(Qt.Qt.WheelFocus)
        layout.addWidget(self.pgLayout)
        self.setLayout(layout) #to install the QVBoxLayout onto the widget
        self.setFocusPolicy(Qt.Qt.WheelFocus)
        self.show()


labelStyle = {'color': '#FFF',
              'font-size': '7pt',
              'bold': True}


class Plotter(Qt.QThread):

    def __init__(self, Fs, nChannels, ViewBuffer, ViewTime, RefreshTime, 
                 ChannelConf, ChsDistribution, ShowSamples=False):
        super(Plotter, self).__init__()

        self.Winds = []
        self.nChannels = nChannels
        self.Plots = {}
        self.Curves = {}
        self.ChannelConf = {}
        self.ChsDistribution = ChsDistribution

        self.ShowSamples = ShowSamples
        self.Fs = Fs
        self.Ts = 1/float(self.Fs)
        self.Buffer = Buffer2D(Fs, nChannels, ViewBuffer)

        self.SetRefreshTime(RefreshTime)
        self.SetViewTime(ViewTime)

        for win, axs in ChsDistribution.items():
            wind = PgPlotWindow()
            self.Winds.append(wind)

            xlink = None
            p = None
            for ax, chs in axs.items():
                wind.pgLayout.nextRow()
                p = wind.pgLayout.addPlot()
                p.hideAxis('bottom')

                p.setDownsampling(auto=True,
                                  # mode='peak',
                                  mode='subsample',
                                  )
                if xlink is not None:
                    p.setXLink(xlink)
                xlink = p

                lab = ''
                for chn in chs:
                    lab = lab + chn + '\n\r'
                    self.ChannelConf[chn] = ChannelConf[chn]
                    col = ChannelConf[chn]['color']
                    width = ChannelConf[chn]['width']
                    c = p.plot(pen=pg.mkPen(color=col,
                                            width=width))
                    self.Plots[chn] = p
                    self.Curves[chn] = c

                p.setLabel(axis='left',
                           text=lab,
                           units='A',
                           **labelStyle)


            if p is not None:
                p.setClipToView(True)
                p.showAxis('bottom')
                if not self.ShowSamples:
                    p.setLabel('bottom', 'Time', units='s', **labelStyle)
                else:
                    p.setLabel('bottom', 'Samps', **labelStyle)


    def SetViewTime(self, ViewTime):
        self.ViewTime = ViewTime
        self.ViewInd = int(ViewTime/self.Ts)

    def SetRefreshTime(self, RefreshTime):
        self.RefreshTime = RefreshTime
        self.RefreshInd = int(RefreshTime/self.Ts)

    def run(self, *args, **kwargs):
        while True:
            if self.Buffer.counter > self.RefreshInd:
                if not self.ShowSamples:
                    t = self.Buffer.GetTimes(self.ViewInd)
                self.Buffer.Reset()

                for chn, ch in self.ChannelConf.items():
                    dat = self.Buffer[-self.ViewInd:, ch['Input']]+ch['Offset']
                    if not self.ShowSamples:
                        self.Curves[chn].setData(t, dat)
                    else:
                        self.Curves[chn].setData(dat)
            else:
#                pg.QtGui.QApplication.processEvents()
                Qt.QThread.msleep(100)

    def AddData(self, NewData):
        self.Buffer.AddData(NewData)

    def stop(self):
        for wind in self.Winds:
            wind.close()
        self.terminate()


##############################################################################

PSDPars = ({'name': 'Fs',
            'readonly': True,
            'type': 'float',
            'value': 2,
            'siPrefix': True,
            'suffix': 'Hz'},
           {'name': 'nChannels',
            'readonly': True,
            'type': 'int',
            'value': 1},
           {'name': 'PlotEnable',
            'type': 'bool',
            'value': True},
           {'name': 'Fmin',
            'type': 'float',
            'value': 1,
            'step': 10,
            'limits': (0.001, 1000),
            'siPrefix': True,
            'suffix': 'Hz'},
           {'name': 'nFFT',
            'title': 'nFFT 2**x',
            'type': 'int',
            'limits': (2, 32),
            'value': 15,
            'step': 1},
           {'name': 'scaling',
            'type': 'list',
            'values': ('density', 'spectrum'),
            'value': 'density'},
           {'name': 'nAvg',
            'type': 'int',
            'value': 4,
            'limits': (0, 30),
            'step': 1},
           {'name': 'AcqTime',
            'readonly': True,
            'type': 'float',
            'siPrefix': True,
            'suffix': 's'},
           {'name': 'AllChannels',
            'title': 'Show All Channels',
            'type': 'bool',
            'value': True,
            },
           )

PSDParsList = ('Fs', 'nFFT', 'nAvg', 'nChannels', 'scaling')


class PSDParameters(pTypes.GroupParameter):
    NewConf = Qt.pyqtSignal()

    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChildren(PSDPars)
        self.param('Fs').sigValueChanged.connect(self.on_FsChange)
        self.param('Fmin').sigValueChanged.connect(self.on_FminChange)
        self.param('nFFT').sigValueChanged.connect(self.on_nFFTChange)
        self.param('nAvg').sigValueChanged.connect(self.on_nAvgChange)
        
        self.ChannelConf = None

    def on_FsChange(self):
        Fs = self.param('Fs').value()
        FMin = self.param('Fmin').value()
        nFFT = np.around(np.log2(Fs/FMin))+1
        self.param('nFFT').setValue(nFFT, blockSignal=self.on_nFFTChange)
        self.on_nAvgChange()

    def on_FminChange(self):
        Fs = self.param('Fs').value()
        FMin = self.param('Fmin').value()
        nFFT = np.around(np.log2(Fs/FMin))+1
        self.param('nFFT').setValue(nFFT, blockSignal=self.on_nFFTChange)
        self.on_nAvgChange()

    def on_nFFTChange(self):
        Fs = self.param('Fs').value()
        nFFT = self.param('nFFT').value()
        FMin = Fs/2**nFFT
        self.param('Fmin').setValue(FMin, blockSignal=self.on_FminChange)
        self.on_nAvgChange()

    def on_nAvgChange(self):
        Fs = self.param('Fs').value()
        nFFT = self.param('nFFT').value()
        nAvg = self.param('nAvg').value()
        AcqTime = ((2**nFFT)/Fs)*nAvg
        self.param('AcqTime').setValue(AcqTime)
        self.NewConf.emit()

    def GetParams(self):
        PSDKwargs = {}
        for p in self.children():
            if p.name() not in PSDParsList:
                continue
            PSDKwargs[p.name()] = p.value()

        ChannelConf = {}
        for Ch in self.ChannelConf:
            chp = {}
            for pp in Ch['children']:
                chp[pp['name']] = pp['value']

            if self.param('AllChannels').value():
                ChannelConf[chp['name']] = chp
            if chp['Enable']:
                ChannelConf[chp['name']] = chp
    
        PSDKwargs['ChannelConf'] = ChannelConf
        return PSDKwargs


class PSDPlotter(Qt.QThread):

    def __init__(self, Fs, nFFT, nAvg, nChannels, scaling, ChannelConf):

        super(PSDPlotter, self).__init__()

        self.scaling = scaling
        self.nChannels = nChannels
        self.Fs = Fs
        self.InitBuffer(nFFT, nAvg)

        self.Plots = {}
        self.Curves = {}
        self.ChannelConf = {}

        self.wind = PgPlotWindow()
        self.wind.pgLayout.nextRow()
        p = self.wind.pgLayout.addPlot()
        p.setLogMode(True, True)
        p.setLabel('bottom', 'Frequency', units='Hz', **labelStyle)
        p.setDownsampling(auto=True,
                           mode='peak',
                          # mode='subsample',
                          )
        if scaling == 'density':
            p.setLabel('left', ' PSD', units=' V**2/Hz', **labelStyle)
        else:
            p.setLabel('left', ' PSD', units=' V**2', **labelStyle)
        # self.Legend = p.addLegend()

        for chn, ch in ChannelConf.items():
            self.ChannelConf[chn] = ch
            c = p.plot(pen=pg.mkPen(ch['color'],
                                    width=ch['width'],
                                    name=chn))
            # self.Legend.addItem(c, chn)
            self.Plots[chn] = p
            self.Curves[chn] = c

    def InitBuffer(self, nFFT, nAvg):
        self.nFFT = 2**nFFT
        self.BufferSize = int(self.nFFT * nAvg)
        self.Buffer = Buffer2D(self.Fs, self.nChannels,
                               self.BufferSize/self.Fs)

    def run(self, *args, **kwargs):
        while True:
            if self.Buffer.IsFilled():
                ff, psd = welch(self.Buffer,
                                fs=self.Fs,
                                nperseg=self.nFFT,
                                scaling=self.scaling,
                                axis=0)
                self.Buffer.Reset()
                for chn, ch in self.ChannelConf.items():
                    self.Curves[chn].setData(ff[1:], psd[1:, ch['Input']])
            else:
                Qt.QThread.msleep(100)

    def AddData(self, NewData):
        self.Buffer.AddData(NewData)

    def stop(self):
        self.wind.close()
        self.terminate()


