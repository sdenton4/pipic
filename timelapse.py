#!/usr/bin/python

import Image
import os
import sys, getopt
import subprocess
import time

usagestring="Usage: timelaspe.py [options]\n"
usagestring+="Options:\n"
usagestring+="-q      : Print this usage screen.\n"
usagestring+="-w 1286 : Set picture width.\n"
usagestring+="-h 972  : Set picture height.\n"
usagestring+="-i 15   : Set photo interval in seconds.  Min recommended: 10\n"
usagestring+="-t 60   : Set maximum duration of program in minutes.  -1 means no limit.\n"
usagestring+="-n 5000 : Set maximum number of pictures to take.\n"
usagestring+="-b 100  : Set target brightness of images (0-255).  Recommended value is 100.\n"
usagestring+="-s 5000 : Initial shutter speed.\n"
usagestring+="-o 100  : Initial ISO.\n"

def avgbrightness(im):
    aa=im.convert('L')
    pixels=(aa.size[0]*aa.size[1])
    h=aa.histogram()
    mu0=sum([i*h[i] for i in range(len(h))])/pixels
    return mu0

def dynamic_adjust(v, delta,target):
    return int( v*(1.0+delta*1.0/target) )

def argassign(var, arg):
    #Assign integer arg to variable, or quit if it fails.
    try:
        var=int(arg)
    except:
       print usagestring
       sys.exit(2)
    return var

def main(argv):
    w=str(int(2592/4))
    h=str(int(1944/4))
    interval=15
    maxtime=60*60*23
    maxshots=5000
    targetBrightness=100
    initialss=10000
    initialiso=100

    brightwidth=4
    thresh=0.01

    brData=[]

    miniso=100
    maxiso=800
    minss=100
    maxss=350000

    try:
       opts, args = getopt.getopt(argv,"whitnbso:", [])
    except getopt.GetoptError:
       print usagestring
       sys.exit(2)

    for opt, arg in opts:
        if opt == '-q':
            print usagestring
            sys.exit()
        elif opt=="-w":
            w=argassign(w,arg)
            w=str(w)
        elif opt=="-h":
            h=argassign(h,arg)
            h=str(h)
        elif opt=="-i":
            interval=argassign(interval,arg)
        elif opt=="-t":
            maxtime=argassign(maxtime,arg)
            maxtime=maxtime*60
        elif opt=="-n":
            maxshots=argassign(maxshots,arg)
        elif opt=="-b":
            targetBrightness=argassign(targetBrightness,arg)
        elif opt=="-s":
            initialss=argassign(initialss,arg)
        elif opt=="-o":
            initialiso=argassign(initialiso,arg)

    currentss=initialss
    currentiso=initialiso
    f=open('/etc/hostname')
    hostname=f.read().strip().replace(' ','')
    f.close()

    start_time=time.time()
    elapsed=time.time()-start_time
    shots_taken=0

    while (elapsed<maxtime or maxtime==-1) and (shots_taken<maxshots or maxshots==-1):
        loopstart=time.time()

        dtime=subprocess.check_output(['date', '+%y%m%d_%T']).strip()
        dtime=dtime.replace(':', '.')
        filename='/home/pi/pictures/'+hostname+'_'+dtime+'.jpg'
        options='-hf -vf -awb off -n'
        options+=' -w '+w+' -h '+h
        options+=' -t 100'
        options+=' -ss '+str(currentss)
        options+=' -ISO '+str(currentiso)
        options+=' -o '+filename
        subprocess.call('raspistill '+options, shell=True)
        im=Image.open(filename)
        br=avgbrightness(im)
        if len(brData)==brightwidth:
            brData[shots_taken%brightwidth]=br
        else:
            brData.append(br)

        #Dynamically adjust ss and iso.
        if shots_taken<brightwidth:
            avgbr=sum(brData)/len(brData)
        else:
            avgbr=sum(brData[len(brData)-brightwidth:])/brightwidth
        delta=targetBrightness-avgbr
        #scale shutter speed and iso relative to delta.
        #prioritize low iso.
        if delta<0:
            #too bright.
            if currentiso>miniso:
                #reduce iso first if possible
                currentiso=dynamic_adjust(currentiso,delta,targetBrightness)
                currentiso=max([currentiso,miniso])
            else:
                currentss=dynamic_adjust(currentss,delta,targetBrightness)
                currentss=max([currentss, minss])
        elif delta>0:
            #too dim.
            if currentss<maxss:
                #increase ss first if possible
                currentss=dynamic_adjust(currentss,delta,targetBrightness)
                currentss=min([currentss, maxss])
            else:
                currentiso=dynamic_adjust(currentiso,delta,targetBrightness)
                currentiso=min([currentiso,maxiso])

        shots_taken+=1
        loopend=time.time()
        elapsed=loopend-start_time

        print 'SS: ', currentss, '\tISO: ', currentiso, '\t', br, '\t', shots_taken, '\t', loopend-loopstart
        maxxedbr=(currentss==maxss and currentiso==maxiso)
        minnedbr=(currentss==minss and currentiso==miniso)
        if abs(delta)>32 and not (maxxedbr or minnedbr):
            #Too far from target brightness.
            shots_taken-=1
            os.remove(filename)
        else:
            #Wait for next shot.
            time.sleep(max([0,interval-(loopend-loopstart)]))


    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
