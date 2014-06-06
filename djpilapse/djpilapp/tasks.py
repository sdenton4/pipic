from __future__ import absolute_import
from celery import shared_task
from celery.signals import worker_ready
from djpilapp.models import *
from time import sleep
import Image

@shared_task
def add(x, y):
    return x + y

@shared_task
def timelapse():
    try:
        T=timelapser.objects.all()[0]
        while T.active:
            T=timelapser.objects.all()[0]
            proj=T.project
            timelapse_shoot()
            if not T.active: break
            sleep(proj.interval)
    except:
        T.set_active(False)
        return False
    return True

@shared_task
def timelapse_shoot():
    T=timelapser.objects.all()[0]
    if not T.active: return None
    proj=T.project
    #Exponential dropoff for brightness adjustment.
    alpha=proj.alpha

    #figure out the filename.
    dtime=subprocess.check_output(['date', '+%y%m%d_%T']).strip()
    dtime=dtime.replace(':', '.')
    filename=proj.folder
    if filename[-1]!='/': filename+='/'
    filename+= proj.project_name + '_' + dtime + '.jpg'
    tempfile='/home/pi/pipic/djpilapse/djpilapp/static/new.jpg'

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
        print filename
    except:
        return False

    newbr=T.avgbrightness(im)
    T.lastbr=alpha*newbr+(1-alpha)*T.lastbr

    #Dynamically adjust ss and iso.
    (T.ss, T.iso)=T.dynamic_adjust(target=proj.brightness, lastbr=T.lastbr)
    print str(newbr)+'\t'+str(T.lastbr)+'\t'+str(T.ss)+'\t'+str(T.iso)
    T.shots_taken+=1

    delta=proj.brightness-newbr
    #if abs(delta)>self.maxdelta and not (maxxedbr or minnedbr):
    if abs(delta)>proj.delta:
        #Too far from target brightness.
        T.shots_taken-=1
        os.remove(filename)
    else:
        T.lastshot=filename
    T.save()


