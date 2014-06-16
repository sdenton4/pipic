#!/usr/bin/python

import Image
import os
import sys, argparse
import subprocess
import datetime
import random

def pixel_level(p,a,b):
    if p<a: return 0
    if p>b: return 255
    return (p-a)*255/(b-a)

class lapseimage:
    def __init__(self, filename):
        self.filename=filename
        self.image=Image.open(filename)
        self.size=self.image.size
        self.pixels=self.size[0]*self.size[1]
        self.modified=None

    def __repr__(self):
        return "Timelapse image "+self.filename

    def show(self):
        return self.image.show()

    def greyscale(self):
        return self.image.convert('L')

    def greyhistogram(self):
        #return [(h[i]+h[i+256]+h[i+512])/3 for i in range(256) ]
        return self.greyscale().histogram()

    def brightness(self):
        h=self.greyhistogram()
        return sum([i*h[i] for i in range(len(h))])/self.pixels

    def variance(self):
        h=self.greyhistogram()
        return sum([h[i]*(i-mu)**2 for i in range(256)])/self.pixels

    def localmaxima(self, width=5, lowerbound=1.0/256):
        h=self.greyhistogram()
        maxima=[]
        for i in range(256):
            if h[i]>self.pixels*lowerbound:
                comp=[h[i]>=h[j] for j in range(max(0,i-width), min(256,i+width))]
                ismax=True
                for j in comp: ismax*=j
                if ismax: maxima.append(i)
        return maxima

    #--------Auto-Levelling---------------------------------------------------------

    def find_level_bounds(self, thresh=0.005):
        h=self.greyhistogram()
        #Find lower boundary a.
        a=0; t=0
        while a<255 and t<thresh*self.pixels:
            a+=1
            t+=h[a]
        #Find upper boundary b.
        b=255; t=0
        while b>0 and t<thresh*self.pixels:
            b-=1
            t+=h[b]
        #Avoid crushing the image too much.
        a=min(a,64)
        b=max(b,256-64)
        return (a,b)

    def level_adjust(self,a,b):
        im=self.image.copy()
        return im.point( lambda p: pixel_level(p,a,b) )

    #--------Pixel averaging----------------------------------------------------

    def getpixel(self, (x,y)):
        return self.image.getpixel( (x,y) )

    def pixel_average(self, I, cutoff=32):
        """
        Perform pixel averaging of self against a set of images I.
        I a list of images to be averaged against.
        """
        im=self.image
        ll=im.load()
        (w,h)=self.size
        n=len(I)
        Ims=[t.load() for t in I]
        for x in range(w):
            for y in range(h):
                p=ll[x,y]
                avgpixel=list(p)
                count=1
                for t in Ims:
                    q=t[x,y]
                    if (abs(q[0]-p[0])<cutoff) and (abs(q[1]-p[1])<cutoff) and (abs(q[2]-p[2])<cutoff):
                        avgpixel=[avgpixel[i]+q[i] for i in range(3)]
                        count+=1
                avgpixel=tuple( (int(avgpixel[i]*1.0/count) for i in range(3) ) )
                ll[x,y]= avgpixel 
        return im

    #-------------------------------------------------------------------------------
    #Filename annotation
    def annotate(self, parsedate=False, gravity='SouthWest'):
        """
        Add text indicating the filename to the image.
        parsedate: Try to extract a timestamp from the filename and print that instead.
        gravity: Gravity option to pass to imagemagick; determines text placement position.
        """
        self.image.save('tmp.jpg')
        command = 'convert tmp.jpg '
        command += ' -gravity '+gravity
        if parsedate:
            try:
                d=self.filename.split('_')
                t=d[2].split('.')
                dt=(d[1][:2], d[1][2:4], d[1][4:], t[0],t[1],t[2])
                dt=tuple( (int(x) for x in dt) )
                ann=str(datetime.datetime(*dt))
            except:
                ann=self.filename
        else:
            ann=self.filename
        command+= ' -font Ubuntu-Bold -pointsize 24 -annotate 0 "'+ann+'" tmp.jpg'
        subprocess.call( command, shell=True )
        self.image=Image.open('tmp.jpg')

#-------------------------------------------------------------------------------

def argassign(arg, typ='int'):
    #Assign integer arg to variable, or quit if it fails.
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

#-------------------------------------------------------------------------------

def main(argv):

    parser = argparse.ArgumentParser(description='Postprocessing for timelapse images.')
    parser.add_argument( '-b', '--bright', default=128, type=int, help='Target brightness for images, from 1 to 256.  Default: 128' )
    parser.add_argument( '-p', '--pixelavg', default=1, type=int, help='Number of images to use for pixel averaging.  Default: 1 (no pixel averaging.)' )
    parser.add_argument( '-t', '--thresh', default=0.05, type=float, help='Threshold between 0 and 1 for auto-levelling.  Higher numbers mean more stretching of the color palette.  Default: 0.05.' )
    parser.add_argument( '-a', '--annotate', default=0, type=int, help='Whether to annotate images.  0->no annotation, 1->filename, 2->date' )
    parser.add_argument( '-i', '--infix', default='pipic', type=str, help='Prefix for raw files.' )
    parser.add_argument( '-c', '--compare', default=False, type=int, help='Place original and modified images side-by-side for comparison. (0 no, 1 yes.) Default: 0' )
    parser.add_argument( '-o', '--outfix', default='mod', type=str, help='Prefix for modified files.' )

    args=parser.parse_args()


    image_list=[ x for x in os.listdir('.') if x[:len(args.infix)].lower()==args.infix and x[-3:].lower()=='jpg']
    image_list.sort()
    N=len(image_list)
    print 'Number of images: ', N

    print 'Running with:'
    print '\tinput      :\t',args.infix
    print '\tbrightness :\t',args.bright
    print '\tpixelavg   :\t',args.pixelavg
    print '\tthresh     :\t',args.thresh
    print '\tannotate   :\t',args.annotate
    print '\tcompare    :\t',args.compare
    print '\toutput     :\t',args.outfix

    if args.outfix==args.infix:
        print 'We will not overwrite original images; choose an output prefix different from the input prefix.'
        return False

    print 'Pre-processing...'
    bright=[]
    for x in image_list:
        try:
            im=lapseimage(x)
        except:
            image_list.remove(x)


    print 'Running image processing...'
    #pixel average
    if args.pixelavg>1:
        for i in range(N):
            I=range(max(i-args.pixelavg,0), min(i+args.pixelavg, N))
            I.remove(i)
            I=[Image.open(image_list[x]) for x in I]
            im.image=im.pixel_average(I, cutoff=16)
            modname='mod'+image_list[i][len(args.infix):]
            im.image.save(modname)
            image_list[i]=modname

    bright=float(args.bright)
    for i in range(N):
        if i%100==0: print i, '\t', image_list[i]
        modname=args.outfix+image_list[i][len(args.infix):]
        im=lapseimage(image_list[i])

        #brightness correction
        if bright>0:
            b=im.brightness()
            k=bright/b
            im.image=im.image.point(lambda p: p*k)

        #auto-levels
        if args.thresh>0:
            (a,b)=im.find_level_bounds(args.thresh)
            im.image=im.level_adjust(a,b)

        if args.annotate==1:
            im.annotate(parsedate=False)
        elif args.annotate==2:
            im.annotate(parsedate=True)

        if args.compare==1:
            im.image.save(modname)
            command='convert '+im.filename+' '+modname+' +append '+modname
            subprocess.call( command, shell=True )
        else:
            im.image.save(modname)

    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
