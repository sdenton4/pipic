#!/usr/bin/python

import Image
import os, sys, argparse
import subprocess
import time
import math
import zmq
import io, picamera
from fractions import Fraction

class timelapse_config(object):
  """Config Options:
    `w` : Width of images.
    `h` : Height of images.
    `interval` : Interval of shots, in seconds.  Recommended minimum is 10s.
    `maxtime` : Maximum amount of time, in seconds, to run the timelapse for.
      Set to 0 for no maximum.
    `maxshots` : Maximum number of pictures to take.  Set to 0 for no maximum.
    `targetBrightness` : Desired brightness of images, on a scale of 0 to 255.
    `maxdelta` : Allowed variance from target brightness.  Discards images that 
      are more than `maxdelta` from `targetBrightness`.  Set to 256 to keep
      all images.
    `iso` : ISO used for all images.
    `maxss` : maximum shutter speed
    `minss` : minimum shutter speed
    `maxfr` : maximum frame rate
    `minfr` : minimum frame rate
    `metersite` : Chooses a region of the image to use for brightness
      measurements. One of 'c', 'a', 'l', or 'r', for center, all, left or 
      right.
    `brightwidth` : number of previous readings to store for choosing next 
      shutter speed.
    `gamma` : determines size of steps to take when adjusting shutterspeed.
  """  
  def __init__(self, config_map={}):
    self.w = config_map.get('w', 1296)
    self.h = config_map.get('h', 972)
    self.iso = config_map.get('iso', 100)
    self.interval = config_map.get('interval', 15)
    self.maxtime = config_map.get('maxtime', 0)
    self.maxshots = config_map.get('maxshots', 0)
    self.targetBrightness = config_map.get('targetBrightness', 100)
    self.maxdelta = config_map.get('maxdelta', 100)
    
    # Setting the maxss under one second prevents flipping into a slower camera mode.
    self.maxss = config_map.get('maxss', 999000)
    self.minss = config_map.get('minss', 100)

    self.metersite = config_map.get('metersite', 'c')
    if self.metersite not in ['c', 'a', 'l', 'r']:
      self.metersite = 'c'

    # Note: these should depend on camera model...
    self.max_fr = config_map.get('minfr', 15)
    self.min_fr = config_map.get('maxfr', 1)
    
    # Dynamic adjustment settings.
    self.brightwidth = config_map.get('brightwidth', 20)
    self.gamma = config_map.get('gamma', 0.2)

  def to_dict(self):
    d = {
      'w': self.w,
      'h': self.h,
      'iso': self.iso,
      'interval': self.interval,
      'maxtime': self.maxtime,
      'maxshots': self.maxshots,
      'targetBrightness': self.targetBrightness,
      'maxdelta': self.maxdelta,
      'maxss': self.maxss,
      'minss': self.minss,
      'metersite': self.metersite,
      'max_fr': self.max_fr,
      'min_fr': self.min_fr,
      'brightwidth': self.brightwidth,
      'gamma': self.gamma,
    }

class timelapse:
  """
  Timelapser class.
  Once the timelapser is initialized, use the `findinitialparams` method to find
  an initial value for shutterspeed to match the targetBrightness.
  Then run the `timelapser` method to initiate the actual timelapse.
  EXAMPLE::
    T=timelapse()
    T.run_timelapse()

  The timelapser broadcasts zmq messages as it takes pictures.
  The `listen` method sets up the timelapser to listen for signals from 192.168.0.1,
  and take a shot when a signal is received.
  EXAMPLE::
    T=timelapse()
    T.listen()
  """
  def __init__(self, camera, config=None):
    if config == None:
      config = timelapse_config({})
    self.config = config
    self.camera = camera
    self.camera.framerate = config.max_fr
    self.camera.resolution = (config.w, config.h)
    self.camera.iso = config.iso

    f=open('/etc/hostname')
    hostname = f.read().strip().replace(' ','')
    f.close()
    self.hostname = hostname

    # We consider shutterspeeds as a floating point number between 0 and 1,
    # denoting position between the max and min shutterspeed.
    # These two functions let us convert back and forth between representations.
    self.floatToSS = lambda x : max(min(int(self.config.minss 
                                            + (self.config.maxss - self.config.minss) * x), 
                                        self.config.maxss), self.config.minss)
    self.SSToFloat = lambda ss : max(min((float(ss) - self.config.minss) 
                                         / (self.config.maxss - self.config.minss), 1.0), 
                                     0.0)

    #Brightness data caching.
    self.brData = []
    self.brindex = 0
    self.lastbr = 0
    self.avgbr = 0
    self.shots_taken = 0

    print 'Finding initial SS....'
    # Give the camera's auto-exposure and auto-white-balance algorithms
    # some time to measure the scene and determine appropriate values
    time.sleep(1)
    # This capture discovers initial AWB and SS.
    self.camera.capture('try.jpg')
    self.camera.shutter_speed = self.camera.exposure_speed
    self.currentss=self.camera.exposure_speed
    self.camera.exposure_mode = 'off'
    self.wb_gains = self.camera.awb_gains
    print 'WB: ', self.wb_gains
    self.camera.awb_mode = 'off'
    self.camera.awb_gains = self.wb_gains

    self.findinitialparams()
    print "Set up timelapser with: "
    print "\tmaxtime :\t", config.maxtime
    print "\tmaxshots:\t", config.maxshots
    print "\tinterval:\t", config.interval
    print "\tBrightns:\t", config.targetBrightness
    print "\tSize  :\t", config.w, 'x', config.h    

  def __repr__(self):
    return 'A timelapse instance.'

  def avgbrightness(self, im):
    """
    Find the average brightness of the provided image according to the method
    defined in `self.metersite`.  `im` should be a PIL image.
    """
    meter = self.config.metersite
    aa = im.convert('L') # Converts to greyscale
    (h, w) = aa.size
    if meter == 'c':
      top = int(1.0 * h / 2 - 0.15 * h) + 1
      bottom = int(1.0 * h / 2 + 0.15 * h) - 1
      left = int(1.0 * w / 2 - 0.15 * w) + 1
      right = int(1.0 * w / 2 + 0.15 * w) + 1
    elif meter == 'l':
      top = int(1.0 * h / 2 - 0.15 * h) + 1
      bottom = int(1.0 * h / 2 + 0.15 * h) - 1
      left = 0
      right = int(.3*w)+2
    elif meter == 'r':
      top = int(1.0 * h / 2 - 0.15 * h) + 1
      bottom = int(1.0*w/2+.15*w)-1
      left = h - int(0.3 * w) - 2
      right = w
    else:
      top = 0
      bottom = h
      left = 0
      right = w
    aa = aa.crop((left, top, right, bottom))
    pixels = (aa.size[0] * aa.size[1])
    h = aa.histogram()
    mu0 = 1.0 * sum([i * h[i] for i in range(len(h))]) / pixels
    return round(mu0, 2)

  def dynamic_adjust(self):
    """
    Applies a simple gradient descent to try to correct shutterspeed and
    brightness to match the target brightness.
    """
    delta = self.config.targetBrightness - self.lastbr
    #Adj = lambda v: math.log( math.exp(v)*(1.0+1.0*delta*gamma/self.targetBrightness) )
    Adj = lambda v: v * (1.0 + 1.0 * delta * self.config.gamma 
                         / self.config.targetBrightness)
    x = self.SSToFloat(self.currentss)
    if x <= 0.01: x = 0.01
    x = Adj(x)
    self.currentss = self.floatToSS(x)
    #Find an appropriate framerate.
    #For low shutter speeds, ths can considerably speed up the capture.
    FR = Fraction(1000000, self.currentss)
    if FR > self.config.max_fr: FR = Fraction(self.config.max_fr)
    if FR < self.config.min_fr: FR = Fraction(self.config.min_fr)
    self.camera.framerate = FR

  def capture(self):
    """
    Take a picture, returning a PIL image.
    """
    # Create the in-memory stream
    stream = io.BytesIO()
    self.camera.ISO = self.config.iso
    self.camera.shutter_speed = self.currentss
    x = self.SSToFloat(self.currentss)
    capstart = time.time()
    self.camera.capture(stream, format='jpeg')
    capend = time.time()
    print ('Exp: %d\tFR: %f\t Capture Time: %f' 
           % (self.camera.exposure_speed, 
              round(float(self.camera.framerate),2), 
              round(capend-capstart,2)))
    # "Rewind" the stream to the beginning so we can read its content
    stream.seek(0)
    image = Image.open(stream)
    return image

  def findinitialparams(self):
    """
    Take a number of small shots in succession to determine a shutterspeed
    and ISO for taking photos of the desired brightness.
    """
    killtoken = False
    self.camera.resolution = (64, 48)
    while abs(self.config.targetBrightness - self.lastbr) > 4:
      im = self.capture()
      self.lastbr = self.avgbrightness(im)
      self.avgbr = self.lastbr

      #Dynamically adjust ss and iso.
      self.dynamic_adjust()
      x = self.SSToFloat(self.currentss)
      print ('ss: % 10d\tx: % 5.3f br: % 4d\t' 
             % (self.currentss, round(x, 2), round(self.lastbr, 2)))
      if x >= 1.0:
        x = 1.0
        if killtoken == True:
          break
        else:
          killtoken = True
      elif x <= 0.0:
        x = 0.0
        if killtoken == True:
          break
        else:
          killtoken = True
    self.camera.resolution = (self.config.w, self.config.h)
    return True

  def maxxedbrightness(self):
    """
    Check whether we've reached maximum SS and ISO.
    """
    return (self.currentss == self.config.maxss)

  def minnedbrightness(self):
    """
    Check whether we've reached minimum SS and ISO.
    """
    return (self.currentss == self.config.minss)


  def shoot(self, filename=None, ss_adjust=True):
    """
    Take a photo and save it at a specified filename.
    """
    im=self.capture()
    #Saves file without exif and raster data; reduces file size by 90%,
    if filename!=None:
      im.save(filename)

    if not ss_adjust: return im

    self.lastbr = self.avgbrightness(im)
    if len(self.brData) >= self.config.brightwidth:
      self.brData[self.brindex % self.config.brightwidth] = self.lastbr
    else:
      self.brData.append(self.lastbr)

    #Dynamically adjust ss and iso.
    self.avgbr=sum(self.brData) / len(self.brData)
    self.dynamic_adjust()
    self.shots_taken += 1
    self.brindex = (self.brindex + 1) % self.config.brightwidth

    delta=self.config.targetBrightness - self.lastbr
    if abs(delta) > self.config.maxdelta:
      #Too far from target brightness.
      self.shots_taken -= 1
      os.remove(filename)
    return im

  def print_stats(self):
    tmpl = 'SS: % 10d\tX: % 8.3f\tBR: % 4d\tShots: % 5d'
    x = self.SSToFloat(self.currentss)
    print tmpl % (self.currentss, round(x,2), self.lastbr, self.shots_taken)

  def run_timelapse(self):
    """
    Takes pictures at specified interval.
    """
    start_time = time.time()
    elapsed = time.time() - start_time

    #Set up broadcast for zmq.
    self.context = zmq.Context()
    self.socket = self.context.socket(zmq.PUB)
    self.socket.bind("tcp://*:5556")

    while ((elapsed < self.config.maxtime or self.config.maxtime == -1) 
           and (self.shots_taken < self.config.maxshots
                or self.config.maxshots == -1)):
      loopstart = time.time()
      dtime = subprocess.check_output(['date', '+%y%m%d_%T']).strip()
      dtime = dtime.replace(':', '.')
      #Broadcast options for this picture on zmq.
      command='0 shoot {} {} {} {}'.format(self.config.w, self.config.h, 
                                           self.currentss, dtime)
      self.socket.send(command)

      #Take a picture.
      filename = ('/home/pi/pictures/%s_%s.jpg' % (self.hostname, dtime))
      self.shoot(filename=filename)

      loopend=time.time()
      x=self.SSToFloat(self.currentss)
      self.print_stats()

      #Wait for next shot.
      time.sleep(max([0, self.config.interval - (loopend - loopstart)]))

    self.socket.close()

  def listen(self):
    """
    Run the timelapser in listen mode.  Listens for ZMQ messages and shoots
    accordingly.
    """
    #  Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://192.168.0.1:5556")
    channel = "0"
    socket.setsockopt(zmq.SUBSCRIBE, channel)

    #Get hostname
    f=open('/etc/hostname')
    hostname=f.read().strip().replace(' ','')
    f.close()

    while True:
      command = socket.recv()
      command = command.split(" ")
      print "Message recieved: " + str(command)
      if command[1] == "quit":
        break
      elif command[1] == "shoot":
        # TODO: This is currently ignoring the various config params from
        # the sender...
        [ch, com, w, h, ss, iso, dtime] = command
        filename = ('/home/pi/pictures/%s_%s.jpg' % (hostname, dtime))
        self.shoot(filename)
        self.print_stats

    socket.close()
    return True


#-------------------------------------------------------------------------------


def main(argv):


    parser = argparse.ArgumentParser(description='Timelapse tool for the Raspberry Pi.')
    parser.add_argument( '-W', '--width', default=1286, type=int, help='Set image width.' )
    parser.add_argument( '-H', '--height', default=972, type=int, help='Set image height.' )
    parser.add_argument( '-i', '--interval', default=15, type=int, help='Set photo interval in seconds.  \nRecommended miniumum is 6.' )
    parser.add_argument( '-t', '--maxtime', default=-1, type=int, help='Maximum duration of timelapse in minutes.\nDefault is -1, for no maximum duration.' )
    parser.add_argument( '-n', '--maxshots', default=-1, type=int, help='Maximum number of photos to take.\nDefault is -1, for no maximum.' )
    parser.add_argument( '-b', '--brightness', default=128, type=int, help='Target average brightness of image, on a scale of 1 to 255.\nDefault is 128.' )
    parser.add_argument( '-d', '--delta', default=128, type=int, help='Maximum allowed distance of photo brightness from target brightness; discards photos too far from the target.  This is useful for autmatically discarding late-night shots.\nDefault is 128; Set to 256 to keep all images.' )
    parser.add_argument( '-m', '--metering', default='a', type=str, choices=['a','c','l','r'], help='Where to average brightness for brightness calculations.\n"a" measures the whole image, "c" uses a window at the center, "l" meters a strip at the left, "r" uses a strip at the right.' )
    parser.add_argument( '-L', '--listen', action='store_true', help='Sets the timelapser to listen mode; listens for a master timelapser to tell it when to shoot.' )
    parser.add_argument( '-I', '--iso', default=100, type=int, help='Set ISO.' )

    try:
        os.listdir('/home/pi/pictures')
    except:
        os.mkdir('/home/pi/pictures')

    args=parser.parse_args()
    cfg = {
      'w': args.width,
      'h': args.height,
      'interval': args.interval,
      'maxshots': args.maxshots,
      'maxtime': args.maxtime,
      'targetBrightness': args.brightness,
      'maxdelta': args.delta,
      'iso': args.iso,
    }

    try:
      camera = picamera.PiCamera()
      TL = timelapse(camera, timelapse_config(cfg))
      if args.listen:
        TL.listen()
      else:
        TL.run_timelapse()

    finally:
      camera.close()

    return True

#-------------------------------------------------------------------------------

if __name__ == "__main__":
   main(sys.argv[1:])
