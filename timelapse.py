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
usagestring+="-i 15   : Set photo interval in seconds.  Min recommended: 5\n"
usagestring+="-t 60   : Set maximum duration of program in minutes.  -1 means no limit.\n"
usagestring+="-n 5000 : Set maximum number of pictures to take.\n"
usagestring+="-b 100  : Set target brightness of images (0-255).  Recommended value is 100.\n"
usagestring+="-d 256  : Maximum allowed distance from target brightness.  Discards too bright/dark.\n"
usagestring+="        : Set -d to 256 to keep all images.\n"
def argassign(arg, typ='int'):
    """
    A small routine for taking arguments and modifying their type to 
    int, str, or float.
    """
    try:
        if typ=='float':
            return float(arg)
        elif typ=='int':
            return int(arg)
        else:
            return str(arg)
    except:
       print usagestring
       sys.exit(2)
    return False

class timelapse:
    """
    Timelapser class.

    Options:
        `w` : Width of images.
        `h` : Height of images.
        `interval` : Interval of shots, in seconds.  Recommended minimum is 10s.
        `maxtime` : Maximum amount of time, in seconds, to run the timelapse for.
            Set to 0 for no maximum.
        `maxshots` : Maximum number of pictures to take.  Set to 0 for no maximum.
        `targetBrightness` : Desired brightness of images, on a scale of 0 to 255.
        `maxdelta` : Allowed variance from target brightness.  Discards images that 
            are more than `maxdelta` from `targetBrightness`.  Set to 256 to keep
            all images.

    Once the timelapser is initialized, use the `findinitialparams` method to find
    an initial value for shutterspeed and ISO, to match the targetBrightness.

    Then run the `timelapser` method to initiate the actual timelapse.

    EXAMPLE::
        T=timelapse()
        T.findinitialparams()
        T.timelapser()
    """
    def __init__(self,w=1296,h=972,interval=15,maxtime=0,maxshots=0,targetBrightness=100,maxdelta=256):

        self.w=w
        self.h=h
        self.interval=interval
        self.maxtime=maxtime
        self.maxshots=maxshots
        self.targetBrightness=targetBrightness
        self.maxdelta=maxdelta

        f=open('/etc/hostname')
        hostname=f.read().strip().replace(' ','')
        f.close()
        self.hostname=hostname

        self.miniso=100
        self.maxiso=800
        self.minss=100
        self.maxss=1500000

        #Brightness data caching.
        self.brightwidth=4
        self.brData=[]
        self.lastbr=0
        self.avgbr=0

        #Get initial ss and iso
        print 'Finding initial SS and ISO....'
        self.currentss=(self.minss+self.maxss)/2
        self.currentiso=100
        self.findinitialparams()

        print "Set up timelapser with: "
        print "\tmaxtime :\t", self.maxtime
        print "\tmaxshots:\t", self.maxshots
        print "\tinterval:\t", self.interval
        print "\tBrightns:\t", self.targetBrightness
        print "\tSize    :\t", self.w, 'x', self.h

    def __repr__(self):
        return 'A timelapse instance.'

    def avgbrightness(self, im):
        aa=im.convert('L')
        pixels=(aa.size[0]*aa.size[1])
        h=aa.histogram()
        mu0=sum([i*h[i] for i in range(len(h))])/pixels
        return mu0

    def dynamic_adjust(self):
        delta=self.targetBrightness-self.lastbr
        Adj = lambda v: int( v*(1.0+delta*1.0/self.targetBrightness) )
        newss=self.currentss
        newiso=self.currentiso
        if delta<0:
            #too bright.
            if self.currentiso>self.miniso:
                #reduce iso first if possible
                newiso=Adj(self.currentiso)
                newiso=max([newiso,self.miniso])
            else:
                newss=Adj(self.currentss)
                newss=max([newss, self.minss])
        elif delta>0:
            #too dim.
            if self.currentss<self.maxss:
                #increase ss first if possible
                newss=Adj(self.currentss)
                newss=min([newss, self.maxss])
            else:
                newiso=Adj(self.currentiso)
                newiso=min([newiso,self.maxiso])
        self.currentss=newss
        self.currentiso=newiso

    def findinitialparams(self):
        killtoken=False
        while abs(self.targetBrightness-self.lastbr)>4:
            options='-hf -vf -awb off -n'
            options+=' -w 64 -h 48'
            options+=' -t 10'
            options+=' -ss '+str(self.currentss)
            options+=' -ISO '+str(self.currentiso)
            options+=' -o new.jpg'
            subprocess.call('raspistill '+options, shell=True)
            im=Image.open('new.jpg')
            self.lastbr=self.avgbrightness(im)
            self.avgbr=self.lastbr

            #Dynamically adjust ss and iso.
            self.dynamic_adjust()
            print self.currentss, self.currentiso, self.lastbr
            if self.currentss==self.maxss and self.currentiso==self.maxiso: 
                if killtoken==True:
                    break
                else:
                    killtoken=True
            elif self.currentss==self.minss and self.currentiso==self.miniso:
                if killtoken==True:
                    break
                else:
                    killtoken=True
        return True

    def maxxedbrightness(self):
        return (self.currentss==self.maxss and self.currentiso==self.maxiso)

    def minnedbrightness(self):
        return (self.currentss==self.minss and self.currentiso==self.miniso)

    def timelapser(self):
        start_time=time.time()
        elapsed=time.time()-start_time
        shots_taken=0
        index=0

        while (elapsed<self.maxtime or self.maxtime==0) and (shots_taken<self.maxshots or self.maxshots==0):
            loopstart=time.time()

            dtime=subprocess.check_output(['date', '+%y%m%d_%T']).strip()
            dtime=dtime.replace(':', '.')
            filename='/home/pi/pictures/'+self.hostname+'_'+dtime+'.jpg'
            options='-hf -vf -awb off -n'
            options+=' -w '+str(self.w)+' -h '+str(self.h)
            options+=' -t 50'
            options+=' -ss '+str(self.currentss)
            options+=' -ISO '+str(self.currentiso)
            options+=' -o new.jpg'
            subprocess.call('raspistill '+options, shell=True)
            im=Image.open('new.jpg')
            #Saves file without exif and raster data; reduces file size by 90%,
            im.save(filename)

            self.lastbr=self.avgbrightness(im)
            if len(self.brData)==self.brightwidth:
                self.brData[index%self.brightwidth]=self.lastbr
            else:
                self.brData.append(self.lastbr)

            #Dynamically adjust ss and iso.
            self.avgbr=sum(self.brData)/len(self.brData)

            self.dynamic_adjust()

            shots_taken+=1
            index=(index+1)%self.brightwidth
            loopend=time.time()
            elapsed=loopend-start_time

            print 'SS: ', self.currentss, '\tISO: ', self.currentiso, '\t', self.lastbr, '\t', shots_taken, '\t', loopend-loopstart
            delta=self.targetBrightness-self.lastbr
            #if abs(delta)>self.maxdelta and not (maxxedbr or minnedbr):
            if abs(delta)>self.maxdelta:
                #Too far from target brightness.
                shots_taken-=1
                os.remove(filename)
            #Wait for next shot.
            time.sleep(max([0,self.interval-(loopend-loopstart)]))


#-------------------------------------------------------------------------------


def main(argv):


    TL = timelapse()

    try:
       opts, args = getopt.getopt(argv,"qw:h:i:t:n:b:s:o:", [])
    except getopt.GetoptError:
       print usagestring
       sys.exit(2)

    for opt, arg in opts:
        if opt == '-q':
            print usagestring
            sys.exit()
        elif opt=="-w":
            TL.w=argassign(arg,'int')
            w=str(w)
        elif opt=="-h":
            TL.h=argassign(arg,'int')
            h=str(h)
        elif opt=="-i":
            TL.interval=argassign(arg,'int')
        elif opt=="-t":
            maxtime=argassign(arg,'int')
            TL.maxtime=maxtime*60
        elif opt=="-n":
            TL.maxshots=argassign(arg,'int')
        elif opt=="-b":
            TL.targetBrightness=argassign(arg,'int')

    TL.timelapser()

    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
