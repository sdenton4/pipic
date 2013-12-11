#!/usr/bin/env python
import os
import time
from decimal import Decimal

# Return CPU temperature as a character string                                     
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

# Return RAM information (unit=kb) in a list                                       
# Index 0: total RAM                                                               
# Index 1: used RAM                                                                 
# Index 2: free RAM                                                                 
def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])

# Return % of CPU used by user as a character string                               
def getCPUuse():
    return(str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip(\
)))

# Return information about disk space as a list (unit included)                     
# Index 0: total disk space                                                         
# Index 1: used disk space                                                         
# Index 2: remaining disk space                                                     
# Index 3: percentage of disk used                                                 
def getDiskSpace():
    p = os.popen("df -h /")
    i = 0
    while 1:
        i = i +1
        line = p.readline()
        if i==2:
            return(line.split()[1:5])

maxtemp=0
mintemp=10000
elapsed=0
interval=5
while True:
	[totalram, usedram, freeram] = getRAMinfo()
	temp=Decimal(getCPUtemperature())
	if temp<mintemp: mintemp=temp
	if temp>maxtemp: maxtemp=temp
	print 'elapsed:   ', elapsed
	print 'cpu temp:  ', temp, '\t', (mintemp, maxtemp)
	print 'free ram:  ', freeram, ':',totalram , '\n'
	time.sleep(interval)
	elapsed=elapsed+interval
