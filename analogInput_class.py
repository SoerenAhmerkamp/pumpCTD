#!/usr/bin/env python

import nidaqmx.system, nidaqmx
from time import *
import datetime
from nidaqmx.types import CtrTime
from threading import *
from scipy.interpolate import interp1d
import numpy as np

system = nidaqmx.system.System.local()
#system.driver_version
#DriverVersion(major_version=16L, minor_version=0L, update_version=0L)

#for device in system.devices:
#    print(device)


class analogInput(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.instVol = 0
		
		self.timeSeries = []
		self.volumeSeries = []
		self.intVol = 0
		self.instVol = 0
		#self.tubeVol = 6.12
		self.tubeVol = 6.335
		self.intTime = 0
		self.timeEst = 0
		self.waterAge = 0
		self.pumpDepth = 0
		self.file1 = open("./Temp/" + str(time()) + "AnalogInput.txt", "w+")
		
		
	def run(self):
		t0 = time()
		with nidaqmx.Task() as task:
			task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
			self.analog = []
			while 1:
				dt = (time()-t0) / 3600 * 60
				t0 = time()
				temp = 0
				for n in range(10):
					temp = temp + task.read(number_of_samples_per_channel=1)[0]
					sleep(0.2)
				temp = temp/(n+1)*1.6
				self.instVol = round(temp,2)
				#self.analog.extend([self.instVal])
				
				self.intVol = self.instVol*dt + self.intVol
				self.intTime = dt + self.intTime
				
				self.timeSeries.extend([self.intTime])
				self.volumeSeries.extend([self.intVol])
				
				self.file1.write((str(datetime.datetime.now())) + "\t%.3f" % (self.instVol) + "\n")
				self.file1.flush()
				
				if self.intVol > self.tubeVol:
					volEst = self.intVol-self.tubeVol
					#print self.tubeVol
					#print volEst
					##print self.volumeSeries
					#print self.timeSeries
					timeEst = interp1d(np.asarray(self.volumeSeries),np.asarray(self.timeSeries))(volEst)
					self.timeEst = timeEst
					timeEst = self.intTime-timeEst
					self.waterAge = round(timeEst,2)

				
				
				
				
				
				
				
				
				
				
