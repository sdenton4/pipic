# Create your views here.

import subprocess, json
import Image
import time
from django.http import HttpResponse
from django.template import Template, Context
from django.template.loader import get_template
from django.utils import simplejson
from django import forms

from django.forms.extras.widgets import SelectDateWidget

from djpilapp.models import *
from djpilapp.forms import *

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
        'project_list': R,
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
    if ss>200000: ss=200000
    if iso>800: iso=800
    if iso<0: iso=0
    filename=basedir+staticdir+'new.jpg'
    options='-awb off -n'
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

    return HttpResponse('cool!')

def findinitialparams(request):
    Q=timelapser.objects.all()[0]
    Q.findinitialparams()
    return HttpResponse('')
    

def jsonupdate(request):
    Q=timelapser.objects.all()[0]
    jsondict={
        'time': time.strftime('%H:%M:%S--%m-%d-%y'),
        'ss' : Q.ss,
        'iso' : Q.iso,
        'boot' : Q.boot,
        'active': Q.active,
    }
    J=json.dumps(jsondict)
    return HttpResponse(J)


