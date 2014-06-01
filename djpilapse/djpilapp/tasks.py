from __future__ import absolute_import
from celery import shared_task
from djpilapp.models import *
from time import time, sleep
import Image

@shared_task
def add(x, y):
    return x + y

@shared_task
def timelapse():
    T=timelapser.objects.all()[0]
    proj=T.project
    while T.active:
        timelapse_shoot()
        sleep(proj.interval)
    return True

@shared_task
def timelapse_shoot():
    #Exponential dropoff for brightness adjustment.
    alpha=proj.alpha
    print 'Shooting.'
    T=timelapser.objects.all()[0]
    if not T.active: return None
    proj=T.project

    #figure out the filename.
    dtime=subprocess.check_output(['date', '+%y%m%d_%T']).strip()
    dtime=dtime.replace(':', '.')
    filename=proj.folder
    if filename[-1]!='/': filename+='/'
    filename+= proj.project_name + '_' + dtime + '.jpg'
    tempfile='/home/pi/pipic/djpilapse/djpilapp/static/new.jpg'
    print filename

    #Take a picture
    options='-awb auto -n'
    options+=' -w '+str(proj.width)+' -h '+str(proj.height)
    options+=' -t 50'
    options+=' -ss '+str(T.ss)
    options+=' -ISO '+str(T.iso)
    options+=' -o '+tempfile
    try:
        subprocess.call('raspistill '+options, shell=True)
        print 'raspistill ' +options
        im=Image.open(tempfile)
        #Saves file without exif and raster data; reduces file size by 90%,
        if filename!=None:
            im.save(filename)
    except:
        return False

    newbr=T.avgbrightness(im)
    T.lastbr=alpha*newbr+(1-alpha)*T.lastbr
    print newbr, '\t', T.lastbr

    #Dynamically adjust ss and iso.
    T.dynamic_adjust()
    T.shots_taken+=1

    delta=proj.brightness-T.lastbr
    #if abs(delta)>self.maxdelta and not (maxxedbr or minnedbr):
    if abs(delta)>proj.delta:
        #Too far from target brightness.
        T.shots_taken-=1
        os.remove(filename)
    T.save()


