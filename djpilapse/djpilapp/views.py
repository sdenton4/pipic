# Create your views here.

import subprocess, json
import Image
import time
from django.http import HttpResponse
from django.template import Template, Context
from django.template.loader import get_template
from django.utils import simplejson

from djpilapp.models import *

basedir='/home/pi/pipic/djpilapse/djpilapp/'
staticdir='static/'

def index(request):
    s=get_template('overview.html')
    P=pilapse_project.objects.all()[0]
    Q=timelapser.objects.all()[0]
    c=Context({
        'project': P,
        'pilapse': Q,
    })    
    body=s.render(c)
    t=get_template('index.html')
    d=Context({
        'body' : body,
    })
    html=t.render(d)
    return HttpResponse(html)

def overview(request):
    s=get_template('overview.html')
    P=pilapse_project.objects.all()[0]
    Q=timelapser.objects.all()[0]
    c=Context({
        'project': P,
        'pilapse': Q,
    })    
    body=s.render(c)
    return HttpResponse(body)

def newProject(request):
    s=get_template('newProject.html')
    c=Context({
    })    
    body=s.render(c)
    return HttpResponse(body)

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

def newProjectSubmit(request):
    jdict=json.dumps( request.body )
    print jdict

