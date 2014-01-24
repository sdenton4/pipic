#!/usr/bin/python

import Image
import os
import sys, getopt
import subprocess
import time
import zmq

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
usagestring+="-m c    : Determines where to meter brightness.  (c)enter,(l)eft,(r)ight, or (a)ll.\n"
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
        T.timelapser()

    The timelapser broadcasts zmq messages as it takes pictures.
    The `listen` method sets up the timelapser to listen for signals from 192.168.0.1,
    and take a shot when a signal is received.

    EXAMPLE::
        T=timelapse()
        T.listen()
    """
    def __init__(self,w=1296,h=972,interval=15,maxtime=0,maxshots=0,targetBrightness=100,maxdelta=256):

        self.w=w
        self.h=h
        self.interval=interval
        self.maxtime=maxtime
        self.maxshots=maxshots
        self.targetBrightness=targetBrightness
        self.maxdelta=maxdelta

        #metersite is one of 'c', 'a', 'l', or 'r', for center, all, left or right.
        #Chooses a region of the image to use for brightness measurements.
        self.metersite='c'

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
        self.brindex=0
        self.lastbr=0
        self.avgbr=0

        self.shots_taken=0

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
        meter=self.metersite
        aa=im.convert('L')
        (h,w)=aa.size
        if meter=='c':
            top=int(1.0*h/2-.15*h)+1
            bottom=int(1.0*h/2+.15*h)-1
            left=int(1.0*w/2-.15*w)+1
            right=int(1.0*w/2+.15*w)+1
        elif meter=='l':
            top=int(1.0*h/2-.15*h)+1
            bottom=int(1.0*h/2+.15*h)-1
            left=0
            right=int(.3*w)+2
        elif meter=='r':
            top=int(1.0*h/2-.15*h)+1
            bottom=int(1.0*w/2+.15*w)-1
            left=h-int(.3*w)-2
            right=w
        else:
            top=0
            bottom=h
            left=0
            right=w
        aa=aa.crop((left,top,right,bottom))
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
            options='-awb off -n'
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
        """
        Check whether we've reached maximum SS and ISO.
        """
        return (self.currentss==self.maxss and self.currentiso==self.maxiso)

    def minnedbrightness(self):
        """
        Check whether we've reached minimum SS and ISO.
        """
        return (self.currentss==self.minss and self.currentiso==self.miniso)


    def shoot(self,filename=None,ssiso_adjust=True):
        """
        Take a photo and save it at a specified filename.
        """
        options='-awb off -n'
        options+=' -w '+str(self.w)+' -h '+str(self.h)
        options+=' -t 50'
        options+=' -ss '+str(self.currentss)
        options+=' -ISO '+str(self.currentiso)
        options+=' -o new.jpg'
        subprocess.call('raspistill '+options, shell=True)
        im=Image.open('new.jpg')
        #Saves file without exif and raster data; reduces file size by 90%,
        if filename!=None:
            im.save(filename)

        if not ssiso_adjust: return None

        self.lastbr=self.avgbrightness(im)
        if len(self.brData)==self.brightwidth:
            self.brData[self.brindex%self.brightwidth]=self.lastbr
        else:
            self.brData.append(self.lastbr)

        #Dynamically adjust ss and iso.
        self.avgbr=sum(self.brData)/len(self.brData)
        self.dynamic_adjust()
        self.shots_taken+=1
        self.brindex=(self.brindex+1)%self.brightwidth

        delta=self.targetBrightness-self.lastbr
        #if abs(delta)>self.maxdelta and not (maxxedbr or minnedbr):
        if abs(delta)>self.maxdelta:
            #Too far from target brightness.
            self.shots_taken-=1
            os.remove(filename)


    def timelapser(self):
        """
        Takes pictures at specified interval.
        """
        start_time=time.time()
        elapsed=time.time()-start_time

        #Set up broadcast for zmq.
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5556")

        while (elapsed<self.maxtime or self.maxtime==0) and (self.shots_taken<self.maxshots or self.maxshots==0):
            loopstart=time.time()

            dtime=subprocess.check_output(['date', '+%y%m%d_%T']).strip()
            dtime=dtime.replace(':', '.')

            #Broadcast options for this picture.
            command='0 shoot {} {} {} {} {}'.format(self.w, self.h, self.currentss, self.currentiso, dtime)
            self.socket.send(command)

            #Take a picture.
            filename='/home/pi/pictures/'+self.hostname+'_'+dtime+'.jpg'
            self.shoot(filename=filename)

            loopend=time.time()
            elapsed=loopend-start_time

            print 'SS: ', self.currentss, '\tISO: ', self.currentiso, '\t', self.lastbr, '\t', self.shots_taken, '\t', loopend-loopstart

            #Wait for next shot.
            time.sleep(max([0,self.interval-(loopend-loopstart)]))

        self.socket.close()

    def listen(self):
        #  Socket to talk to server
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://192.168.0.1:5556")
        channel = "0"
        socket.setsockopt(zmq.SUBSCRIBE, channel)

        #Get hostname
        f=open('/etc/hostname')
        hostname=f.read().strip().replace(' ','')
        f.close()

        while True:
            command = socket.recv()
            command=command.split(" ")
            print "Message recieved: " + str(command)
            if command[1]=="quit":
                break
            elif command[1]=="shoot":
                [ch,com,w,h,ss,iso,dtime]=command
                filename='/home/pi/pictures/'+hostname+'_'+dtime+'.jpg'
                self.shoot(filename)
                print 'SS: ', self.currentss, '\tISO: ', self.currentiso, '\t', self.lastbr, '\t', self.shots_taken

        socket.close()
        return True


#-------------------------------------------------------------------------------


def main(argv):


    TL = timelapse()

    listen=False

    try:
       opts, args = getopt.getopt(argv,"qLw:h:i:t:n:b:s:o:m:", [])
    except getopt.GetoptError:
       print usagestring
       sys.exit(2)

    for opt, arg in opts:
        if opt == '-q':
            print usagestring
            sys.exit()
        elif opt=="-w":
            TL.w=argassign(arg,'int')
        elif opt=="-h":
            TL.h=argassign(arg,'int')
        elif opt=="-i":
            TL.interval=argassign(arg,'int')
        elif opt=="-t":
            maxtime=argassign(arg,'int')
            TL.maxtime=maxtime*60
        elif opt=="-n":
            TL.maxshots=argassign(arg,'int')
        elif opt=="-m":
            TL.metersite=argassign(arg,'str')
        elif opt=="-b":
            TL.targetBrightness=argassign(arg,'int')
        elif opt=="-L":
            listen=True

    if listen:
        TL.listen()
    else:
        TL.timelapser()

    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
