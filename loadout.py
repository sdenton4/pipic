#!/usr/bin/python

import sys, getopt
import subprocess
import random
import os, shutil

usageString='loadOut.py -r <target root directory> -n <hostname>'

def placefile( filename, targetdir ):
    command='cp '+filename+' '+targetdir
    subprocess.call(command, shell=True)

hostcolors=['red','blue','green','yellow','orange','purple','brown',]
hostcolors+=['white','black','cyan','burgundy','vermillion','aqua','maroon',]
hostcolors+=['teal','taupe','neon']

def main(argv):
    try:
       opts, args = getopt.getopt(argv,"hr:n:", ["root=", "hostname=",])
    except getopt.GetoptError:
       print usageString
       sys.exit(2)

    #default value for pi root is None
    piroot=None
    hostname=""
    for opt, arg in opts:
        if opt == '-h':
            print usageString
            sys.exit()
        elif opt in ("-r", "--root"):
            print opt, arg.strip()
            piroot = arg.strip()
            if piroot[-1]!='/': piroot.append('/')
            try:
                os.listdir(piroot)
            except:
                print "Root directory not found."
                sys.exit(2)
        elif opt in ("-n", "--hostname"):
          hostname = arg.strip()
          if hostname not in hostcolors:
            print "Not a defined hostname.  Try one of these, or specify none and I'll pick one at random:"
            print hostcolors
            return False
    if hostname=="": hostname=hostcolors[random.randint(0,len(hostcolors))]

    #Place configuration files and scripts.
    files={
        'config/crontab': 'etc/crontab',
        'config/networks': 'etc/networks',
        'config/bash.bashrc': 'etc/bash.bashrc',
        'config/wpa_supplicant.conf': 'etc/wpa_supplicant/wpa_supplicant.conf',
        'photoscript.py': 'home/pi/photoscript.py',
        'timelapse.py': 'home/pi/timelapse.py',
        'deflicker.py': 'home/pi/deflicker.py',
        'tempgauge.py': 'home/pi/tempgauge.py',
    }
    for f in files.keys():
        placefile(f, piroot + files[f])

    #Copy over program archives.
    for x in os.listdir('archives'):
        shutil.copy('archives/'+x, piroot+'var/cache/apt/archives/')


    #Write network config for eth0.
    f=open(piroot+'etc/networks', 'a')
    f.write('\n\n    iface eth0 inet static\n')
    f.write('    address 192.168.0.'+str(hostcolors.index(hostname))+'\n')
    f.write('    netmask 255.255.255.0\n')
    f.write('    gateway 192.168.0.254\n')
    f.close()

    #Change time zone.
    f=open(piroot+'etc/timezone', 'w')
    f.write('America/Toronto\n')
    f.close()

    #Change hostname.
    f=open(piroot+'etc/hostname', 'w')
    f.write(hostname+'\n')
    f.close()

    #Make pictures directory.
    try:
        subprocess.call('mkdir '+piroot+'home/pi/pictures', shell=True)
    except:
        pass

if __name__ == "__main__":
   main(sys.argv[1:])
