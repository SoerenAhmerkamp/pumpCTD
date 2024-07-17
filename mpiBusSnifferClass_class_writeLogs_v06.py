#!/usr/bin/env python

import math, struct,commands, curses, atexit, socket
from time import *
import datetime
from threading import *
import winsound
#import binascii
#from bitstring import BitArray
#def exit_handler():
#	curses.echo()
#        curses.nocbreak()
 #       curses.endwin()
  #  	print 'MpiBus Monitor Stopped.'


#atexit.register(exit_handler)

#global busPipe
#busPipe = serial.Serial(
#port='/dev/ttyUSB0',
#baudrate=19200,
#timeout=0.05,
#)

class mpiBusSniffer(Thread):
	def __init__(self):
		Thread.__init__(self)
		#self.daemon = True
		
		TCP_IP = 'localhost'
		TCP_PORT = 5555
		BUFFER_SIZE = 1
		#MESSAGE = b'\x55\xaa\x01'

		self.buspipe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.buspipe.connect((TCP_IP, TCP_PORT))
		self.temp = 0
		self.timeDEst = 0		
		#self.stdscr = curses.initscr()
		#stdscr.clear()
		#curses.noecho()
		#curses.cbreak()

		#self.start()
		self.master = 1
		self.loopAct = 1
		self.specStatus = 0
		self.header = "\x55\xaa"
		self.TERMINATOR = 1
		self.BUSY = 0
		self.clear()
		
	def clear(self):
		self.pkgFinal = ""
		self.pkg = ""
		self.masReq = ""
		self.masAdd = ""
		self.insReq = ""
		self.insAdd = ""
		self.insDev = ""
		self.tempBIN = ""
		self.insInterp = ""
		self.pumpErr = "No Data"
		self.BottomContact = "No Contact"
		self.data = ["No Data","No Data",0,"No Data","No Data","No Data","No Data","No Data"]
		self.winchSpeed = 0.5
		self.motorSwitch = "Off"
		self.signal = True
		self.instr = {
			5: "Aanderaa",
			6: "Logger",
			30: "AnalogOut",
			31: "AnalogOut",
			32: "FastCAT",
			40: "PumpMotor",
			41: "Firesting",
			42: "Firesting"
		}
		
		self.lisName = {"Empty":0,
						"Oxygen":1,
						"Salinity":2,
						"Temperature":3,
						"Conductivity":4,
						"Chlorophyll":5,
						"OxygenTrace":6,
						"OxygenAanderaa":7,
						"Depth":8}
		
		self.lis = [[] for i in range(20)]
		self.lisDepth = [[] for i in range(20)]
		self.lisTime = [[] for i in range(20)]
		self.file = [[] for i in range(20)]
		for i, value in self.lisName.iteritems():
			self.file[self.lisName[i]] = open("./Temp/" + str(time()) + "_" + i + ".txt", "w+")
		
		
		#if self.TERMINATOR == 0:
		#	self.run()
		#	self.TERMINATOR = 1
		#self.fHFastCAT = open('./Files/fHFastCat.log','wr')

	def signal_thread(self,freq,duration):
			self.signal = False
			winsound.Beep(freq,duration)
			self.signal = True
		
	def report_progress(self):
		self.stdscr.clear()
		self.stdscr.addstr(1, 0, "{0}".format(self.tempBIN.encode('hex')))
		self.stdscr.addstr(2, 0, "	|---------- MpiBus Monitor v1.0 -----------|")
		self.stdscr.addstr(3, 0, "	Last Package: {0}".format(self.pkg.encode('hex')))
		self.stdscr.addstr(4, 0, "	Status: {0}".format(self.pkgStat))
		self.stdscr.addstr(5, 0, "	|------------- Master inquiry -------------|")
		self.stdscr.addstr(6, 0, "	Address: {0}".format(self.masAdd))
		self.stdscr.addstr(7, 0, "	Request: {0}".format(self.masReq.encode('hex')))
		self.stdscr.addstr(8, 0, "	|------------- Instrument reply -----------|")
		self.stdscr.addstr(9, 0, "	Answer: {0}".format(self.insReq.encode('hex')))
		self.stdscr.addstr(10, 0, "	Status: {0}".format(self.insDev))
		self.stdscr.addstr(11, 0, "	Interp: {0}".format(self.insInterp))
		self.stdscr.addstr(15, 0, "	|----------- Extracted Values -------------|")
		self.stdscr.addstr(16, 0, "	Depth: {0}".format(self.data[2]))
		self.stdscr.addstr(17, 0, "	Temperature: {0}".format(self.data[0]))
		self.stdscr.addstr(18, 0, "	Oxygen: {0}".format(self.data[4]))
		self.stdscr.addstr(19, 0, "	Bottom Contact: " + self.BottomContact)
		self.stdscr.refresh()

	def checksum(self,val):
		return chr(int(math.fmod(sum(map(ord,val)),256)))

	def updateLists(self,val,numb):
			self.lis[self.lisName[val]].extend([self.data[numb]])
			self.lisDepth[self.lisName[val]].extend([self.data[2]])
			self.lisTime[self.lisName[val]].extend([time()])
			self.file[self.lisName[val]].write((str(datetime.datetime.now())) + "\t%.3f" % self.data[numb] + "\t%.3f\n" % self.data[2] + "")
			self.file[self.lisName[val]].flush()
		
	def interpBUS(self,command):
#		if (command == "\x64"): # Version Check is standardized
#			self.insInterp = "Version check"		
#		elif (command == "\x01"):
#			self.insInterp = "Status check"
		if (self.insAdd == 42):
			self.interpFiresting(command)
		elif (self.insAdd == 41):
			self.interpFiresting(command)
		elif (self.insAdd == 32):
			#print ""
			self.interpFastCAT(command)
		elif (self.insAdd == 30):
			self.interpAnalog(command)
		elif (self.insAdd == 31):
			self.interpAnalog(command)
		elif (self.insAdd == 40):
			self.interpMotor(command)
		else:
			self.interpUnknown(command)
	
	def interpUnknown(self,command):
		self.insInterp = "Unknown Data Request."
		
	def interpMotor(self,command):
		if command == "\x01":
			out = struct.unpack('<B',self.insReq[1])
			bit = [format(out[0],'07b')]
			str = bit;
			bits = str[0]
			#print bits
			motorOn = int(bits[6])
			motorSpeed1 = int(bits[3])
			motorSpeed2 = int(bits[2])
			Err = int(bits[1])
			#print motorSpeed1
			if motorOn == 0:
				self.motorSwitch = "Off"	
			elif motorOn == 1 and motorSpeed1 == 1:
				self.motorSwitch = "Slow"
			elif motorOn == 1 and motorSpeed2 == 1:
				self.motorSwitch = "Fast"
			if Err:
				self.pumpErr = "Error"
			else:
				self.pumpErr = "Ok"
			

		
	def interpAnalog(self,command):
	    #self.fHFastCAT.write(datetime.datetime.now().strftime("%Y-%m-%d\t%H:%M:%S.%f\t"))
	    #self.fHFastCAT.write("%d \n" % int(command))
		command = self.insReq[0]
		channel = self.insReq[1]
		
		if self.insReq[4] > '\x7f':
			addByte = '\xff'
		else:
			addByte = '\x00'
		ext = self.insReq[2:5] + addByte
		outputTemp = struct.unpack('<l',ext)
		
		#self.data[0] = self.insReq[0]
		
		self.insInterp = outputTemp[0]
		
		if self.insAdd == 30 and channel == "\x01":
			if self.insInterp > -10000:
				self.BottomContact = 'Contact Contact Contact!!!!'
				if self.signal:
					processThread = Thread(target=self.signal_thread, args=(2000, 1000))  # <- note extra ','
					processThread.start()
			else:
				self.BottomContact = 'No Contact'
				#print self.insInterp
			#self.insInterp = channel
			
		# Zyklops	
		if self.insAdd == 31 and channel == "\x00":	
			#self.insInterp = channel
			self.data[5] = self.insInterp
			self.updateLists("Chlorophyll",5)
		#if self.insAdd == 31 and channel == "\x01":


		
	def interpFastCAT(self,command):
	    #self.fHFastCAT.write(datetime.datetime.now().strftime("%Y-%m-%d\t%H:%M:%S.%f\t"))
	    #self.fHFastCAT.write("%d \n" % int(command))
		#channel = self.insReq[]
		command = self.insReq[0]
		#print len(self.insReq)
		if len(self.insReq) > 4:
			if self.insReq[4] > '\x7f':
				addByte = '\xff'
			else:
				addByte = '\x00'
			ext = self.insReq[2:5] + addByte
			outputTemp = struct.unpack('<l',ext)
			
			# self.data[2] is depth and should always be added to list
			
			if self.insReq[1] == "\x00":
				#Temperature
				self.BUSY = 1
				self.data[0] = round(outputTemp[0]*0.0001,2)
				#self.data[0] = round(self.data[0]*1000)/1000
				self.updateLists("Temperature",0)
				#self.lis[self.lisName["Temperature"]].extend([self.data[0]])
				#self.lisTime[self.lisName["Temperature"]].extend([time()])
				#self.lisDepth[self.lisName["Temperature"]].extend([self.data[2]])
				self.BUSY = 0
				
			elif self.insReq[1] == "\x01":
				#Conductivity
				self.BUSY = 1
				self.data[1] = outputTemp[0]*0.00001
				self.updateLists("Conductivity",1)
				#self.lis[self.lisName["Conductivity"]].extend([self.data[1]])
				#self.lisTime[self.lisName["Conductivity"]].extend([time()])
				#self.lisDepth[self.lisName["Conductivity"]].extend([self.data[2]])
				self.BUSY = 0
				
			elif self.insReq[1]  == "\x02":
				#Pressure
				self.BUSY = 1
				self.data[2] = outputTemp[0]*0.001
				self.depthDiff = self.data[2]-self.temp
				self.timeDiff = time()-self.timeDEst		
				
				self.winchSpeed = self.depthDiff / self.timeDiff / 60
				self.temp = self.data[2]
				self.timeDEst = time()
				self.updateLists("Depth",1)
				
				
				#self.lis[self.lisName["Depth"]].extend([self.data[1]])
				#self.lisTime[self.lisName["Depth"]].extend([time()])
				#self.lisDepth[self.lisName["Depth"]].extend([self.data[2]])
				self.BUSY = 0
		
				
			elif self.insReq[1]  == "\x03":
				#Salinity
				self.BUSY = 1
				self.data[3] = outputTemp[0]*0.0001
				self.updateLists("Salinity",3)
				#self.lis[self.lisName["Salinity"]].extend([self.data[3]])
				#self.lisTime[self.lisName["Salinity"]].extend([time()])
				#self.lisDepth[self.lisName["Salinity"]].extend([self.data[2]])
				self.BUSY = 0
			
			self.insInterp = outputTemp[0]
			#self.insInterp = channel

	def interpFiresting(self,command):
		command = self.insReq[0]
		#print self.insAdd
		
		self.insInterp = "Data Request: "
		leng = len(self.insReq)
		if leng > 25 and self.insAdd == 42:
			outputTemp = struct.unpack('<6B5l',self.insReq)
			output = outputTemp[6:]
			self.BUSY = 1
			self.data[6] = output[1]/1000
			self.insInterp = output
			self.updateLists("OxygenTrace",6)
			#self.lis[self.lisName["OxygenTrace"]].extend([self.data[6]])
			#self.lisTime[self.lisName["OxygenTrace"]].extend([time()])
			#self.lisDepth[self.lisName["OxygenTrace"]].extend([self.data[2]])
			self.BUSY = 0
		
		if leng > 25 and self.insAdd == 41:
			outputTemp = struct.unpack('<6B5l',self.insReq)
			output = outputTemp[6:]
			self.BUSY = 1
			self.data[4] = output[1]/1000
			self.insInterp = output
			self.updateLists("Oxygen",4)
			#self.lis[self.lisName["Oxygen"]].extend([self.data[4]])
			#self.lisTime[self.lisName["Oxygen"]].extend([time()])
			#self.lisDepth[self.lisName["Oxygen"]].extend([self.data[2]])
			self.BUSY = 0
		
	def run(self):
		temp = ""
		receive = ""
		i = 1
		#sleep(1)
		self.pkg = '\x55\xaa'
		self.pkgStat = 'Let us start...'
		#self.report_progress()
		sleep(1)
		while 1:
			sleep(0.1)
			data = self.buspipe.recv(1)
			self.tempBIN += data
			
			if temp+data == self.header:
				try:
					sleep(0.1)
					self.pkg = self.buspipe.recv(1)
					address = int(self.pkg.encode('hex'),16)
					L = self.buspipe.recv(1)
					self.pkg += L
					L = int(L.encode('hex'),16)
					self.pkg += self.buspipe.recv(L)
					chksum = self.buspipe.recv(1)
				except:
					chksum = "\x00"
					self.pkg = "\xff"

				if (self.checksum(self.pkg) == chksum):
					self.pkgStat = 'Package ok.'
					self.BUSY = 1
					self.pkgFinal = self.pkg
					self.BUSY = 0
					if (address > 1) : 
						self.masAdd = address
						self.masReq = self.pkg[2:]
						self.insAdd = address
						self.insInterp = ''
						self.insDev = 'No reply'
						self.insReq = ''
					else:
						self.insAdd = int(self.pkg[2].encode('hex'),16)
						self.insReq = self.pkg[3:]
						self.insDev = self.instr[self.insAdd]
						# Try Interpretation
						#try:
						#	self.insDev = self.instr[self.insAdd]
						self.interpBUS(self.pkg[3])	
						#except:
						#	self.insInterp = 'Unknown Error.'

					#self.report_progress()
					self.pkg = ""
					self.tempBIN = ""
				else:
					self.pkgStat = 'Wrong checksum: Corrupt Package.'
					self.tempBIN = ""
			else:
				temp = data


#busSniffer = mpiBusSniffer()
#busSniffer.run()
