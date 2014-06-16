# Create your views here.

import subprocess, json
from time import time, strftime
from os import statvfs, stat
from django.http import HttpResponse
from django.template import Context
from django.template.loader import get_template
<<<<<<< HEAD
from django.utils import simplejson
from django import forms

from django.forms.extras.widgets import SelectDateWidget
=======
from django.views.decorators.csrf import csrf_exempt
>>>>>>> celery

from djpilapp.models import *
from djpilapp.tasks import *


basedir='/home/pi/pipic/djpilapse/djpilapp/'
staticdir='static/'


def index(request):
    s = get_template('index.html')
    try:    
        P = pilapse_project.objects.all()[0]
    except:
        pass #to do: create an entry in the database
    try:
        Q = timelapser.objects.all()[0]
    except:
        pass #to do: create an entry in the database
    R = pilapse_project.objects.all()
    c=Context({
        'project': P,
        'pilapse': Q,
<<<<<<< HEAD
        'project_list': R,
    })    
=======
    })
>>>>>>> celery
    html=s.render(c)
    return HttpResponse(html)

def shoot(request, ss=50000, iso=100):
    """
    Take a photo and save it as new.jpg.
    """
    #Check that camera is available.
    Q=timelapser.objects.all()[0]
    if Q.active: return HttpResponse(location)
    Q.set_active(True)
    Q.set_status('Taking manual photo')
    ss=int(ss)
    iso=int(iso)
    if ss<0: ss=0
    if ss>2000000: ss=2000000
    if iso>800: iso=800
    if iso<100: iso=100
    filename=basedir+staticdir+'new.jpg'
    options='-awb auto -n'
    options+=' -w 640 -h 480'
    options+=' -t 100'
    options+=' -ss '+str(ss)
    options+=' -ISO '+str(iso)
    options+=' -o ' + filename
    subprocess.call('raspistill '+options, shell=True)
    #Saves file without exif and raster data; reduces file size by 90%,
    #im=Image.open(filename)
    #im.save(filename)
    location='static/new.jpg'
    Q.set_status('idle')
    Q.set_active(False)
    return HttpResponse(location)
    
    
def newProjectSubmit(request):
    print request.body
    
    params = json.loads( request.body )
    print params
    
    Q=pilapse_project(
        project_name = str(params["projectName"]),
        folder = str(params["folder"]),
        keep_images = bool(params["keepImages"]),

        #Timelapser settings
        brightness = int(params["brightness"]),
        interval = int(params["interval"]),
        width =  int(params["width"]),
        height = int(params["height"]),
        maxtime= int(params["maxTime"]),
        maxshots = int(params["maxShots"]),
        delta = int(params["width"]),
        listen = int(params["listen"]),
    )
    Q.save()
    return HttpResponse(Q.project_name)

def findinitialparams(request):
    Q=timelapser.objects.all()[0]
    Q.findinitialparams()
    return HttpResponse('')
    

def startlapse(request):
    Q=timelapser.objects.all()[0]
    Q.findinitialparams()
    Q.set_active(True)
    timelapse.delay()
    return HttpResponse('')

def deactivate(request):
    Q=timelapser.objects.all()[0]
    Q.set_active(False)
    Q.set_status('idle')
    Q.set_active(False)
    Q.set_status('idle')
    return HttpResponse('')

def reboot(request):
    subprocess.call('sudo reboot', shell=True)
    return HttpResponse('')

def poweroff(request):
    subprocess.call('sudo poweroff', shell=True)
    return HttpResponse('')

def deleteall(request):
    Q=timelapser.objects.all()[0]
    proj=Q.project
    folder=proj.folder
    if folder[-1]!='/': folder+='/'
    subprocess.call('sudo rm '+folder+'*.jpg', shell=True)
    Q.shots_taken=0
    Q.save()
    return HttpResponse('')

#We would like a nice way to run this at startup time....
#Add something to crontab like `sleep(10); wget 192.168.0.5:8000/boot_timelapse/`
def boot_timelapse():
    T=timelapser.objects.all()[0]
    if T.boot or T.active:
        T.set_active(True)
        timelapse()
    else:
        T.set_active(False)
    return True

@csrf_exempt
def jsonupdate(request):
    Q=timelapser.objects.all()[0]
    P=Q.project
    s=statvfs('/')
    df=s.f_bsize*s.f_bavail
    try:
        size=stat(Q.lastshot).st_size
        remaining=int(float(df)/size)
    except:
        remaining=''
    free=str(df/(1024*1024))+' Mb'
    jsondict={
        'time'  : strftime('%H:%M:%S--%m-%d-%y'),
        'diskfree'  : free,
        'remaining' : remaining,

        'ss'    : Q.ss,
        'iso'   : Q.iso,
        'boot'  : Q.boot,
        'active': Q.active,
        'shots' : Q.shots_taken,
        'lastshot': Q.lastshot,
        'lastbr': Q.lastbr,
        'status': Q.status,
        'avgbr' : Q.avgbr,

        'alpha' : P.alpha,
        'brightness' : P.brightness,
        'delta' : P.delta,
        'folder' : P.folder,
        'height' : P.height,
        'width' : P.width,
        'listen' : P.listen,
        'interval' : P.interval,
        'project_name': P.project_name,
    }
    J=json.dumps(jsondict)
    return HttpResponse(J)

<<<<<<< HEAD
=======
@csrf_exempt
def saveProjectSettings(request):
    vals=request.POST.dict()
    Q=timelapser.objects.all()[0]
    P=Q.project
    P.delta=int(vals[u'projdelta'])
    P.brightness=int(vals[u'projbrightness'])
    P.height=int(vals[u'projheight'])
    P.width=int(vals[u'projwidth'])
    P.interval=int(vals[u'projinterval'])
    #Project name and folder should be immutable.
    #P.project_name=vals[u'projname']
    #P.folder=vals[u'projfolder']
    P.save()
    return HttpResponse('')

@csrf_exempt
def newProjectSubmit(request):
    jdict=json.dumps( request.body )
    print jdict
    return HttpResponse('')
>>>>>>> celery

