import Image
import subprocess
import random
import os, sys, getopt

usagestring="Usage: brightData.py [options]\n"
usagestring+="Options:\n"
usagestring+="-q      : Print this usage screen.\n"
usagestring+="-n      : Numbe of shots to take.  Best not to mix with manual ss/iso.\n"
usagestring+="-s 5000 : Manually set shutter speed.\n"
usagestring+="-o 100  : Manually set ISO.\n"

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


def main(argv):

    w=str(64)
    h=str(48)
    initialss=10000
    initialiso=100

    miniso=100
    maxiso=800
    minss=100
    maxss=350000

    ss=None
    iso=None
    nshots=1

    try:
       opts, args = getopt.getopt(argv,"qn:s:o:", [])
    except getopt.GetoptError:
       print usagestring
       sys.exit(2)

    for opt, arg in opts:
        if opt == '-q':
            print usagestring
            sys.exit()
        elif opt=="-n":
            nshots=argassign(arg,'int')
        elif opt=="-s":
            ss=argassign(arg,'int')
        elif opt=="-o":
            iso=argassign(arg,'int')

    if ss==None: ss=random.randint(minss, maxss)
    if iso==None: iso=random.randint(miniso, maxiso)

    f=open('/etc/hostname')
    hostname=f.read().strip().replace(' ','')
    f.close()

    try:
        os.listdir('/home/pi/brdata/')
    except:
        os.mkdir('/home/pi/brdata/')

    for i in range(nshots):
        dtime=subprocess.check_output(['date', '+%y%m%d_%T']).strip()
        dtime=dtime.replace(':', '.')
        filename1='/home/pi/brdata/'+hostname+'_'+dtime+'_'+'base.jpg'
        filename2='/home/pi/brdata/'+hostname+'_'+dtime+'_'+str(ss)+'_'+str(iso)+'.jpg'

        #Take the picture with base ss and iso.
        options='-hf -vf -awb off -n'
        options+=' -w '+w+' -h '+h
        options+=' -t 100'
        options+=' -ss '+str(initialss)
        options+=' -ISO '+str(initialiso)
        options+=' -o new.jpg'
        subprocess.call('raspistill '+options, shell=True)
        im1=Image.open('new.jpg')

        #Take the picture with new ss and iso.
        options='-hf -vf -awb off -n'
        options+=' -w '+w+' -h '+h
        options+=' -t 100'
        options+=' -ss '+str(ss)
        options+=' -ISO '+str(iso)
        options+=' -o new.jpg'
        subprocess.call('raspistill '+options, shell=True)
        im2=Image.open('new.jpg')
        histogram=im2.convert('L').histogram()
        #Ignore mostly-black and mostly-white images.
        if histogram[0]<64*16 and histogram[-1]<64*16:
            im1.save(filename1)
            im2.save(filename2)

        ss=random.randint(minss, maxss)
        iso=random.randint(miniso, maxiso)

    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
