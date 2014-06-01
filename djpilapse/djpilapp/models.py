from django.db import models
import os, subprocess, Image
from datetime import datetime


class pilapse_project(models.Model):
    #Project settings
    project_name = models.CharField(max_length=200)
    folder = models.CharField(max_length=200)
    keep_images=models.BooleanField(verbose_name="Keep images?", name='Keep images')

    #Timelapser settings
    brightness = models.IntegerField(verbose_name="Target brightness", name='brightness')
    interval = models.IntegerField(verbose_name="Shot interval in seconds", name='interval')
    width =  models.IntegerField(verbose_name="Image width", name='width')
    height = models.IntegerField(verbose_name="Image height", name='height')
    maxtime= models.IntegerField(verbose_name="Maximum time in minutes", name='maxtime')
    maxshots=models.IntegerField(verbose_name="Maximum shots", name='maxshots')
    delta = models.IntegerField(verbose_name="Allowed brightness variance", name='delta')
    alpha = models.FloatField(verbose_name="Exponential averaging constant for brightness smoothing", name='alpha')
    listen=models.BooleanField(verbose_name="Listen mode?", name='listen')

    def __unicode__(self):
        return self.project_name

    def make_folder(self):
        """
        Create the project folder.
        """
        try:
            os.listdir(self.folder)
        except:
            os.mdir(self.folder)

    def validator(self):
        """
        Validate data in each of the user-defined fields.  Returns a dict of booleans
        for the results.
        """
        valid={}
        valid['brightness']=(0<=self.brightness<256)
        valid['interval']=(0<self.interval)
        valid['width']=(1<=self.width<2592)
        valid['height']=(1<=self.height<1944)
        valid['maxtime']=(-1<=self.maxtime)
        valid['maxshots']=(-1<=self.maxshots)
        valid['delta']=(0<=self.delta)
        try:
            os.listdir(self.folder)
            valid['folder']=True
        except:
            valid['folder']=False
        return valid

#-------------------------------------------------------------------------------

class timelapser(models.Model):
    """
    We construct a timelapser as a Django model.  There should be only a single instance
    in the database table; we will only ever use the first instance.
    """

    uid = models.CharField(max_length=200)
    project = models.ForeignKey(pilapse_project)
    currentss = models.IntegerField(verbose_name="Shutter Speed", name='ss')
    currentiso = models.IntegerField(verbose_name="ISO", name='iso')
    lastbr = models.IntegerField(verbose_name="Last shot brightness", name='lastbr')
    shots_taken = models.IntegerField(verbose_name="Shots taken", name='shots_taken')
    start_on_boot=models.BooleanField(verbose_name="Start on boot?", name='boot')
    active=models.BooleanField(verbose_name="Tracks whether currently taking photos", name='active')
    metersite='a'
    minss=100
    maxss=2000000
    miniso=100
    maxiso=800

    def __unicode__(self):
        return "Pilapser with prefix "+self.project.project_name

    def time_elapsed(self):
        return self.shots_taken*self.project.interval

    def set_active(self, state=True):
        """
        Set the camera's `active` variable.  Used to claim the resource.
        """
        self.active=state
        self.save()

    def set_start_on_boot(self, state=True):
        """
        Configure the pi to start shooting on boot.
        TODO: make this actually do things.
        """
        self.start_on_boot=state
        self.save()

    def avgbrightness(self, im):
        """
        Find the average brightness of the provided image according to the method
        defined in `self.metersite`
        """
        aa=im.convert('L')
        (h,w)=aa.size
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
        targetBrightness=self.project.brightness
        delta=targetBrightness-self.lastbr
        Adj = lambda v: int( v*(1.0+delta*1.0/self.project.brightness) )
        newss=self.ss
        newiso=self.iso
        if delta<0:
            #too bright.
            if self.iso>self.miniso:
                #reduce iso first if possible
                newiso=Adj(self.iso)
                newiso=max([newiso,self.miniso])
            else:
                newss=Adj(self.ss)
                newss=max([newss, self.minss])
        elif delta>0:
            #too dim.
            if self.ss<self.maxss:
                #increase ss first if possible
                newss=Adj(self.ss)
                newss=min([newss, self.maxss])
            else:
                newiso=Adj(self.iso)
                newiso=min([newiso,self.maxiso])
        self.ss=newss
        self.iso=newiso

    def maxxedbrightness(self):
        """
        Check whether we've reached maximum SS and ISO.
        """
        return (self.ss==self.maxss and self.iso==self.maxiso)

    def minnedbrightness(self):
        """
        Check whether we've reached minimum SS and ISO.
        """
        return (self.ss==self.minss and self.iso==self.miniso)

    def findinitialparams(self):
        """
        Take a number of small shots in succession to determine a shutterspeed
        and ISO for taking photos of the desired brightness.
        """
        if self.active:
            return False
        self.set_active(True)
        killtoken=False
        targetBrightness=self.project.brightness
        self.lastbr=-128
        while abs(targetBrightness-self.lastbr)>4:
            options='-awb auto -n'
            options+=' -w 64 -h 48'
            options+=' -t 10'
            options+=' -ss '+str(self.ss)
            options+=' -ISO '+str(self.iso)
            options+=' -o new.jpg'
            subprocess.call('raspistill '+options, shell=True)
            im=Image.open('new.jpg')
            self.lastbr=self.avgbrightness(im)
            self.avgbr=self.lastbr

            #Dynamically adjust ss and iso.
            self.dynamic_adjust()
            print self.ss, self.iso, self.lastbr
            #We use a killtoken so that the while loop runs one extra time before
            #deciding to quit because the max/min iso and ss have been reached.
            if self.ss==self.maxss and self.iso==self.maxiso: 
                if killtoken==True:
                    break
                else:
                    killtoken=True
            elif self.ss==self.minss and self.iso==self.miniso:
                if killtoken==True:
                    break
                else:
                    killtoken=True
        self.save_base()
        self.set_active(False)
        return True

#-------------------------------------------------------------------------------


