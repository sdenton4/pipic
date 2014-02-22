#!/usr/bin/python

import Image
import os, sys, argparse
import subprocess
import time
import zmq

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
        """
        Find the average brightness of the provided image according to the method
        defined in `self.metersite`
        """

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
        """
        Applies a simple gradient descent to try to correct shutterspeed and
        brightness to match the target brightness.
        """
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
        """
        Take a number of small shots in succession to determine a shutterspeed
        and ISO for taking photos of the desired brightness.
        """
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

        while (elapsed<self.maxtime or self.maxtime==-1) and (self.shots_taken<self.maxshots or self.maxshots==-1):
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
        """
        Run the timelapser in listen mode.  Listens for ZMQ messages and shoots
        accordingly.
        """
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


    parser = argparse.ArgumentParser(description='Timelapse tool for the Raspberry Pi.')
    parser.add_argument( '-W', '--width', default=1286, type=int, help='Set image width.' )
    parser.add_argument( '-H', '--height', default=972, type=int, help='Set image height.' )
    parser.add_argument( '-i', '--interval', default=15, type=int, help='Set photo interval in seconds.  \nRecommended miniumum is 6.' )
    parser.add_argument( '-t', '--maxtime', default=-1, type=int, help='Maximum duration of timelapse in minutes.\nDefault is -1, for no maximum duration.' )
    parser.add_argument( '-n', '--maxshots', default=-1, type=int, help='Maximum number of photos to take.\nDefault is -1, for no maximum.' )
    parser.add_argument( '-b', '--brightness', default=128, type=int, help='Target average brightness of image, on a scale of 1 to 255.\nDefault is 128.' )
    parser.add_argument( '-d', '--delta', default=128, type=int, help='Maximum allowed distance of photo brightness from target brightness; discards photos too far from the target.  This is useful for autmatically discarding late-night shots.\nDefault is 128; Set to 256 to keep all images.' )
    parser.add_argument( '-m', '--metering', default='a', type=str, choices=['a','c','l','r'], help='Where to average brightness for brightness calculations.\n"a" measures the whole image, "c" uses a window at the center, "l" meters a strip at the left, "r" uses a strip at the right.' )
    parser.add_argument( '-L', '--listen', action='store_true', help='Sets the timelapser to listen mode; listens for a master timelapser to tell it when to shoot.' )

    args=parser.parse_args()
    TL = timelapse(w=args.width, h=args.height, interval=args.interval, maxshots=args.maxshots, maxtime=args.maxtime, targetBrightness=args.brightness, maxdelta=args.delta)

    if args.listen:
        TL.listen()
    else:
        TL.timelapser()

    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
