import sys, os, random
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from threading import Thread
from random import randint
#import time
from curses import wrapper
from scipy.interpolate import interp1d
from mpiBusSnifferClass_class_writeLogs_v09 import *
from analogInput_class import *
from pumpCTDtext import *
#from variableCreator import * 
import matplotlib
import numpy as np
from matplotlib.artist import getp
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

global dat
dat = mpiBusSniffer()
#self.dat.setDaemon(True)
dat.start()

global ana
ana = analogInput()
#self.dat.setDaemon(True)
ana.start()

class AppFormText(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.create_main_frame()
        self.dat = dat
        self.ana = ana
        self.process = Thread(target=self.draw, args=[])
        self.process.start()

		
    def draw(self):
		while 1:
			self.textboxw.setText("Depth:\t\t{0}".format(dat.data[2]) + "\nWinch:\t\t{0}".format(dat.winchSpeed) + "\nTemperature:\t{0}".format(self.dat.data[0])  + "\nSalinity:\t\t{0}".format(self.dat.data[3]) + "\n\nOxygen:\t\t{0}".format(self.dat.data[4]) + "\nOxygen Trace:\t{0}".format(self.dat.data[6])+ "\n\nChlorophyll:\t{0}".format(self.dat.data[5]) + "\n\nBottom Contact:\t" + self.dat.BottomContact + "\n\nPump:\t\t{0}".format(self.dat.motorSwitch) + "\n\nPump Status:\t{0}".format(self.dat.pumpErr) + "\nPump Volume:\t{0}".format(self.ana.instVol) + "\nWater Age:\t{0}".format(self.ana.waterAge) + "\nWater Depth:\t{0}".format(self.ana.pumpDepth))
			#print dat.data[2]
			sleep(0.2)
	
    def create_main_frame(self):
        self.main_frame = QWidget()
        h4box = QHBoxLayout()
        hbox = QHBoxLayout()
		
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.textboxw = QLabel("Waiting for data...")
        self.textboxw.resize(280,200)
        self.textboxw.setFont(font)
        
        h4box.addWidget(self.textboxw)	
        vbox = QVBoxLayout()
        vbox.addLayout(h4box)
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('PumpCTD')

        self.plotAct2 = 0
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        self.ana = ana
        self.dat = dat
        #self.dat = Thread(target=mpiBusSniffer, args=[])
        #self.dat.start()
	
        for x in self.dat.lisName:
            self.cb.addItem(x)
            self.cb2.addItem(x)

        self.ini_plot(1)
        self.plotAct = 1
        self.process = Thread(target=self.on_draw, args=[])
        self.process.start()
        sleep(1)
       # self.on_draw()

    def stop(self):
        if self.plotAct == 0:
            self.draw_button.setText("Stop")
            self.plotAct = 1
            self.plotAct = Thread(target=self.on_draw, args=[])
            self.plotAct.start()
        else:
            self.draw_button.setText("Start")
            self.plotAct = 0
    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"

        path = unicode(QFileDialog.getSaveFileName(self,
                                                   'Save file', '',
                                                   file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)

    def on_about(self):
        msg = """ (c) Soeren Ahmerkamp 2019
        """
        QMessageBox.about(self, "PumpCTD", msg.strip())

    def on_pick(self, event):
        # The event received here is of the type
        # matplotlib.backend_bases.PickEvent

        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on a bar with coords:\n %s" % box_points

        QMessageBox.information(self, "Click!", msg)

    def clear(self):
		#Risky Function
        #self.dat.TERMINATOR = 0
	    self.dat.clear()
    	
    def ini_plot(self,fIni):
        varSel = str(self.cb.currentText())

        #if fIni:
        self.axes.line1, = self.axes.plot(self.dat.lis[self.dat.lisName[varSel]],
                                          self.dat.lisDepth[self.dat.lisName[varSel]],
                                          linewidth=self.slider.value() / 20)

        self.axes.set_xlim([0, 100])
        self.axes.set_ylim([200, -10])
        self.axes.set_ylabel('Depth (m)')
        self.canvas.draw()
        self.plotActTest = 0
		
		
        #self.axes.hline = self.axes.axhline(y=self.ana.waterAge,linestyle='--',linewidth=1, color='g')
        self.axes.line2 = self.axes.axhline(y=self.ana.waterAge ,linestyle='--',linewidth=1, color='g')
		
		#self.axes.set_subplots_adjust(left=0.23, bottom=0.3, right=0.9, top=0.96)

    def ini_plot2(self):
        self.draw_buttonAct.setEnabled(0)

        if self.plotAct2:
            self.axes2.cla()
        else:
            self.axes2 = self.axes.twiny()

        varSel = str(self.cb2.currentText())
        self.axes2.xaxis.set_ticks_position("bottom")
        self.axes2.xaxis.set_label_position("bottom")

        # Offset the twin axis below the host
        self.axes2.spines["bottom"].set_position(("axes", -0.2))

        # Turn on the frame for the twin axis, but then hide all
        # but the bottom spine
        self.axes2.set_frame_on(True)
        self.axes2.patch.set_visible(False)
        for sp in self.axes2.spines.itervalues():
            sp.set_visible(False)
            self.axes2.spines["bottom"].set_visible(True)

        self.axes2.line1, = self.axes2.plot(self.dat.lis[self.dat.lisName[varSel]],
                                          self.dat.lisDepth[self.dat.lisName[varSel]],
                                          linewidth=self.slider.value() / 20,color='r')

        #ax2.set_xticks(new_tick_locations)
        #ax2.set_xticklabels(tick_function(new_tick_locations))
        label = self.axes2.set_xlabel(str(self.cb2.currentText()))
        label.set_color('red')
	
        #self.axes2.set_ylim([1000, 0])
        #self.axes2.set_xlabel(varSel2)
        self.plotAct2 = 1
        #self.canvas.draw()


    def on_draw(self):
        while self.plotAct:
			if self.dat.BUSY == 0:
				#self.axes.clear()
				self.axes.grid(self.grid_cb.isChecked())
				varSel = str(self.cb.currentText())
				varSel2 = str(self.cb2.currentText())

				self.axes.line1.set_xdata(self.dat.lis[self.dat.lisName[varSel]])
				self.axes.line1.set_ydata(self.dat.lisDepth[self.dat.lisName[varSel]])

				if self.plotAct2:
				#    if len(self.dat.lis[self.dat.lisName[varSel2]]) == len(self.dat.lis[self.dat.lisName["Depth"]]):
					self.axes2.line1.set_xdata(self.dat.lis[self.dat.lisName[varSel2]])
					self.axes2.line1.set_ydata(self.dat.lisDepth[self.dat.lisName[varSel2]])
					self.axes2.set_xlabel(str(self.cb2.currentText()))
					col = getp(self.axes2.line1, 'color')
					label = self.axes2.set_xlabel(str(self.cb2.currentText()))
					label.set_color(col)


				if len(self.dat.lisTime[self.dat.lisName["Depth"]]) > 0 and self.ana.waterAge > 0.1:
					self.ana.pumpDepth = interp1d(self.dat.lisTime[self.dat.lisName["Depth"]],self.dat.lisDepth[self.dat.lisName["Depth"]],fill_value="extrapolate")(time()-self.ana.timeEst)
					self.ana.pumpDepth = round(self.ana.pumpDepth,2)
				
				#print self.ana.pumpDepth
				#print self.dat.lisTime[self.dat.lisName["Depth"]][:]
 
					
				self.axes.set_xlabel(str(self.cb.currentText()))
				#self.axes.hline.set_ydata(self.ana.waterAge)
				self.axes.line2.set_ydata(y=self.ana.pumpDepth)
				
				# Update figure
				self.canvas.draw()
				self.canvas.flush_events()

				# Textbox function needs some time!?
				sleep(0.2)
				#"Package: " + self.dat.pkgFinal.encode("hex") + "\n\n" + 
				#self.textboxw.setText("Depth: {0}".format(self.dat.data[2]) + "\nTemperature:{0}".format(self.dat.data[0]) + "\t\tOxygen: {0}".format(self.dat.data[4])+ "\nChlorophyll: {0}".format(self.dat.data[5]) + "\t\tBottom Contact:" + self.dat.BottomContact)
				#+ "\nChlorophyll: {0}".format(self.dat.data[5])
			
    def create_main_frame(self):

        self.main_frame = QWidget()
        # Create the mpl Figure and FigCanvas objects.
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 110
        self.fig = Figure((2.0, 8.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        # Since we have only one plot, we can use add_axes
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111,xmargin=-0.0)
        self.fig.subplots_adjust(left=0.23, bottom=0.3, right=0.9, top=0.96)

        # Bind the 'pick' event for clicking on one of the bars
        #
        self.canvas.mpl_connect('pick_event', self.on_pick)

        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        # Other GUI controls
        #
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(200)
        self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)

        self.cb = QComboBox()
        self.connect(self.cb,SIGNAL('clicked ()'),self.selectionchange)

        self.cb2 = QComboBox()
        self.connect(self.cb,SIGNAL('clicked ()'),self.selectionchange)

        self.draw_button = QPushButton("&Stop")
        self.connect(self.draw_button, SIGNAL('clicked()'), self.stop)

        self.draw_buttonClear = QPushButton("&Clear")
        self.connect(self.draw_buttonClear, SIGNAL('clicked()'), self.clear)

        self.draw_buttonAct = QPushButton("&Activate")
        self.connect(self.draw_buttonAct, SIGNAL('clicked()'), self.ini_plot2)

        self.draw_buttonAlwAct = QPushButton("&Activated")
        self.draw_buttonAlwAct.setEnabled(False)
       # self.connect(self.draw_buttonAct, SIGNAL('clicked()'), self.ini_plot2)

		
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.on_draw)

        self.var1_label = QLabel('Variable 1:')
        self.var2_label = QLabel('Variable 2:')
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(20)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.connect(self.slider, SIGNAL('valueChanged(int)'), self.on_draw)

        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.setRange(1, 100)
        self.slider2.setValue(20)
        self.slider2.setTracking(True)
        self.slider2.setTickPosition(QSlider.TicksBothSides)
        self.connect(self.slider2, SIGNAL('valueChanged(int)'), self.on_draw)

        #
        # Layout with box sizers
        #
        hbox = QHBoxLayout()
        h2box = QHBoxLayout()
        h3box = QHBoxLayout()
        h4box = QHBoxLayout()

        h3box.setContentsMargins(0, 0, 0, 0)
        h3box.setSpacing(0)
		
        self.textboxw = QLabel("Package Received:\n\nDepth:\nTemperature:\n\nOxygen:\nBottom Contact")
        #self.textboxw.move(20, 20)
        self.textboxw.resize(280,200)
        #self.textboxw.setFont('Arial',10) 
        #self.textboxw.setText()

        self.spacer = QLabel(" ")
        #self.textboxw.move(20, 20)
        self.textboxw.resize(5000,2)

		
        for w in [self.grid_cb,
                  self.draw_buttonClear,self.draw_button]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignLeft)

        for w in [self.var1_label,self.cb,self.draw_buttonAlwAct]:
            h2box.addWidget(w)
            h2box.setAlignment(w, Qt.AlignLeft)

        for w in [self.var2_label,self.cb2,self.draw_buttonAct]:
            h3box.addWidget(w)
            h3box.setAlignment(w, Qt.AlignLeft)

        #for w in [self.cb2,self.draw_buttonAct]:
        #    h3box.addWidget(w)
        #    h3box.setAlignment(w, Qt.AlignLeft)

        h4box.addWidget(self.textboxw)	
			
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)
        vbox.addLayout(h2box)
        vbox.addLayout(h3box)
        #vbox.addLayout(h4box)

        self.main_frame.setLayout(vbox)

        self.setCentralWidget(self.main_frame)

    def selectionchange(self, i):
        print "Items in the list are :"

        for count in range(self.cb.count()):
            print self.cb.itemText(count)
        print "Current index", i, "selection changed ", self.cb.currentText()

    def create_status_bar(self):
        #self.status_text = QLabel("PumpCTD: " + "\xAA\x55".encode('Hex'))
        #self.statusBar().addWidget(self.status_text, 1)
        #self.status = QLabel("System Status | Normal")  
        #self.status.setStyleSheet(' QLabel {color: red}')
        #self.statusBar().addWidget(self.status)
        #self.repaint()
		self.status = QStatusBar(self)
		self.statusBar().addWidget(self.status)
		self.status.showMessage("PumpCTD")


    def create_menu(self):
        self.file_menu = self.menuBar().addMenu("&File")

        load_file_action = self.create_action("&Save plot",
                                              shortcut="Ctrl+S", slot=self.save_plot,
                                              tip="Save the plot")
        quit_action = self.create_action("&Quit", slot=self.close,
                                         shortcut="Ctrl+Q", tip="Close the application")

        self.add_actions(self.file_menu,
                         (load_file_action, None, quit_action))

        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About",
                                          shortcut='F1', slot=self.on_about,
                                          tip='About the demo')

        self.add_actions(self.help_menu, (about_action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None,
                      icon=None, tip=None, checkable=False,
                      signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    form2 = AppFormText()
    form2.show()
    app.exec_()


if __name__ == "__main__":
    main()
