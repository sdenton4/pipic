# Create your views here.

import subprocess, json
import Image
import time
from django.http import HttpResponse
from django.template import Template, Context
from django.template.loader import get_template
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt

from djpilapp.models import *
from djpilapp.tasks import *

basedir='/home/pi/pipic/djpilapse/djpilapp/'
staticdir='static/'

def index(request):
    s=get_template('index.html')
    P=pilapse_project.objects.all()[0]
    Q=timelapser.objects.all()[0]
    c=Context({
        'project': P,
        'pilapse': Q,
    })
    html=s.render(c)
    return HttpResponse(html)

def shoot(request, ss=50000, iso=100):
    """
    Take a photo and save it as new.jpg.
    """
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
    return HttpResponse(location)

def findinitialparams(request):
    Q=timelapser.objects.all()[0]
    Q.findinitialparams()
    return HttpResponse('')

def startlapse(request):
    Q=timelapser.objects.all()[0]
    Q.set_active(True)
    timelapse.delay()
    return HttpResponse('')

def deactivate(request):
    Q=timelapser.objects.all()[0]
    Q.set_active(False)
    return HttpResponse('')

def reboot(request):
    subprocess.call('sudo reboot', shell=True)
    return HttpResponse('')

def poweroff(request):
    subprocess.call('sudo poweroff', shell=True)
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
    jsondict={
        'time'  : time.strftime('%H:%M:%S--%m-%d-%y'),
        'ss'    : Q.ss,
        'iso'   : Q.iso,
        'boot'  : Q.boot,
        'active': Q.active,
        'shots' : Q.shots_taken,
        'lastshot': Q.lastshot,
        'lastbr': Q.lastbr,

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

