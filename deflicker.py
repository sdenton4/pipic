#!/usr/bin/python

import Image
import os
import sys, getopt
import subprocess
import random

usagestring="Usage: deflicker.py [options]\n"
usagestring+="For fixing up timelapse photos.\n"
usagestring+="Options:\n"
usagestring+="-h       : Print this usage screen.\n"
usagestring+="-i pipic : File prefix.\n"
usagestring+="-b 10    : Number of pictures to use in brightness correction.\n"
usagestring+="-p 3     : Number of pictures to use for pixel averaging.\n"
usagestring+="-t 0.05  : Auto-level threshold.\n"


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
        im=self.image.copy()
        (w,h)=self.size
        n=len(I)
        for x in range(w):
            for y in range(h):
                p=im.getpixel((x,y))
                avgpixel=list(p)
                count=1
                for t in I:
                    q=t.getpixel((x,y))
                    if (abs(q[0]-p[0])<cutoff) and (abs(q[1]-p[1])<cutoff) and (abs(q[2]-p[2])<cutoff):
                        avgpixel=[avgpixel[i]+q[i] for i in range(3)]
                        count+=1
                avgpixel=tuple( (int(avgpixel[i]*1.0/count) for i in range(3) ) )
                im.putpixel((x,y), avgpixel)
        return im

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

    #default values.
    brightwidth=10
    pixelavgwidth=1
    thresh=0.05
    prefix='pipic'

    try:
       opts, args = getopt.getopt(argv,"hi:b:t:p:", [])
    except getopt.GetoptError:
       print usagestring
       sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print usagestring
            sys.exit()
        elif opt=="-b":
            brightwidth=argassign(arg,'int')
        elif opt=="-t":
            thresh=argassign(arg,'float')
        elif opt=="-p":
            pixelavgwidth=argassign(arg,'int')
        elif opt=="-i":
            prefix=argassign(arg,'str')

    image_list=[ x for x in os.listdir('.') if x[:len(prefix)].lower()==prefix and x[-3:].lower()=='jpg']
    image_list.sort()
    N=len(image_list)
    print 'Number of images: ', N

    print 'Running with:'
    print '\tprefix     :\t',prefix
    print '\tbrightwidth:\t',brightwidth
    print '\tpixelavg   :\t',pixelavgwidth
    print '\tthresh     :\t',thresh

    print 'Pre-processing...'
    bright=[]
    for x in image_list:
        try:
            im=lapseimage(x)
            if brightwidth>1:
                br=im.brightness()
                bright.append(br)
        except:
            image_list.remove(x)


    print 'Running image processing...'
    for i in range(N):
        if i%100==0: print i, '\t', image_list[i]
        im=lapseimage(image_list[i])

        #brightness correction
        if brightwidth>1:
            I=range(max(i-brightwidth,0), min(i+brightwidth, N))
            target=sum([bright[j] for j in I])/len(I)
            k=float(target)/bright[i]
            im.image=im.image.point(lambda p: p*k)

        #pixel average
        if pixelavgwidth>1:
            I=range(max(i-pixelavgwidth,0), min(i+pixelavgwidth, N))
            I.remove(i)
            I=[Image.open(image_list[x]) for x in I]
            im.image=im.pixel_average(I, cutoff=32)

        #auto-levels
        if thresh>0:
            (a,b)=im.find_level_bounds(thresh)
            im.image=im.level_adjust(a,b)

        im.image.save('mod'+image_list[i][len(prefix):])

    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
