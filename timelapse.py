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
    ``disable_led` : Whether to disable the LED. 
  """  
  def __init__(self, config_map={}):
    self.w = config_map.get('w', 1296)
    self.h = config_map.get('h', 972)
    self.iso = config_map.get('iso', 100)
    self.interval = config_map.get('interval', 15)
    self.maxtime = config_map.get('maxtime', -1)
    self.maxshots = config_map.get('maxshots', -1)
    self.targetBrightness = config_map.get('targetBrightness', 128)
    self.maxdelta = config_map.get('maxdelta', 100)
    
    # Setting the maxss under one second prevents flipping into a slower camera mode.
    self.maxss = config_map.get('maxss', 999000)
    self.minss = config_map.get('minss', 100)

    # Note: these should depend on camera model...
    self.max_fr = config_map.get('minfr', 15)
    self.min_fr = config_map.get('maxfr', 1)
    
    # Dynamic adjustment settings.
    self.brightwidth = config_map.get('brightwidth', 20)
    self.gamma = config_map.get('gamma', 0.2)

    self.disable_led = config_map.get('disable_led', False)

  def floatToSS(self, x):
    base = int(self.minss + (self.maxss - self.minss) * x)
    return max(min(base, self.maxss), self.minss)
  
  def SSToFloat(self, ss):
    base = (float(ss) - self.minss) / (self.maxss - self.minss)
    return max(min(base, 1.0), 0.0)
    
  def to_dict(self):
    return {
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
      'max_fr': self.max_fr,
      'min_fr': self.min_fr,
      'brightwidth': self.brightwidth,
      'gamma': self.gamma,
      'disable_led': self.disable_led,
    }

class timelapse_state(object):
  """Container class for timelapser state, to allow easy testing.
  """
  def __init__(self, config, state_map={}):
    # List of average brightness of recent images.
    self.brData = state_map.get('brData', [])
    # List of shutter speeds for recent images.
    self.xData = state_map.get('xData', [])
    # Number of pictures taken 
    self.shots_taken = state_map.get('shots_taken', 0)
    # Current framerate
    self.framerate = state_map.get('max_fr', config.max_fr)
    # White balance
    self.wb = state_map.get('wb', (Fraction(337, 256), Fraction(343, 256)))


class timelapse(object):
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
    self.camera.resolution = (config.w, config.h)
    self.camera.iso = config.iso
    if config.disable_led:
      try:
        camera.led = False
      except Exception as e:
        print "Failed to disable LED: " + e

    f=open('/etc/hostname')
    hostname = f.read().strip().replace(' ','')
    f.close()
    self.hostname = hostname

    # We consider shutterspeeds as a floating point number between 0 and 1,
    # denoting position between the max and min shutterspeed.
    # These two functions let us convert back and forth between representations.
    
    self.state = timelapse_state(config)
    self.camera.framerate = self.state.framerate

    print 'Finding initial SS....'
    # Give the camera's auto-exposure and auto-white-balance algorithms
    # some time to measure the scene and determine appropriate values
    time.sleep(2)
    # This capture discovers initial AWB and SS.
    self.camera.capture('try.jpg')
    self.camera.shutter_speed = self.camera.exposure_speed
    self.state.currentss=self.camera.exposure_speed
    self.camera.exposure_mode = 'off'
    self.state.wb_gains = self.camera.awb_gains
    print 'WB: ', self.state.wb_gains
    self.camera.awb_mode = 'off'
    self.camera.awb_gains = self.state.wb_gains

    self.findinitialparams(self.config, self.state)
    print "Set up timelapser with: "
    print "\tmaxtime :\t", config.maxtime
    print "\tmaxshots:\t", config.maxshots
    print "\tinterval:\t", config.interval
    print "\tBrightns:\t", config.targetBrightness
    print "\tSize  :\t", config.w, 'x', config.h    

  def __repr__(self):
    return 'A timelapse instance.'

  def avgbrightness(self, im, config=None):
    """
    Find the average brightness of the provided image according to the method
    
    Args:
      im: A PIL image.
      config: A timelapseConfig object.  Defaults to self.config.
    Returns:
      Average brightness of the image.
    """
    if config is None: config = self.config
    aa = im.copy()
    if aa.size[0] > 128:
      aa.thumbnail((128, 96), Image.ANTIALIAS)
    aa = im.convert('L') # Converts to greyscale
    (h, w) = aa.size
    pixels = (aa.size[0] * aa.size[1])
    h = aa.histogram()
    mu0 = 1.0 * sum([i * h[i] for i in range(len(h))]) / pixels
    return round(mu0, 2)

  def dynamic_adjust(self, config=None, state=None):
    """
    Applies a simple gradient descent to try to correct shutterspeed and
    brightness to match the target brightness.
    """
    if config is None: config = self.config
    if state is None: state = self.state

    delta = config.targetBrightness - state.brData[-1]
    Adj = lambda v: v * (1.0 + 1.0 * delta * config.gamma 
                         / config.targetBrightness)
    x = config.SSToFloat(state.currentss)
    x = Adj(x)
    if x < 0: x = 0
    if x > 1: x = 1
    state.currentss = config.floatToSS(x)
    #Find an appropriate framerate.
    #For low shutter speeds, ths can considerably speed up the capture.
    FR = Fraction(1000000, state.currentss)
    if FR > config.max_fr: FR = Fraction(config.max_fr)
    if FR < config.min_fr: FR = Fraction(config.min_fr)
    state.framerate = FR

  def capture(self, config=None, state=None):
    """
    Take a picture, returning a PIL image.
    """
    if config is None: config = self.config
    if state is None: state = self.state

    # Create the in-memory stream
    stream = io.BytesIO()
    self.camera.ISO = config.iso
    self.camera.shutter_speed = state.currentss
    self.camera.framerate = state.framerate
    self.camera.resolution = (config.w, config.h)
    x = config.SSToFloat(state.currentss)
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

  def findinitialparams(self, config=None, state=None):
    """
    Take a number of small shots in succession to determine a shutterspeed
    and ISO for taking photos of the desired brightness.
    """
    if config is None: config = self.config
    if state is None: state = self.state
    killtoken = False

    # Find init params with small pictures and high gamma, to work quickly.
    cfg = config.to_dict()
    cfg['w'] = 128
    cfg['h'] = 96
    cfg['gamma'] = 2.0
    init_config = timelapse_config(cfg)
    
    state.brData = [0]
    state.xData = [0]

    while abs(config.targetBrightness - state.brData[-1]) > 4:
      im = self.capture(init_config, state)
      state.brData = [self.avgbrightness(im)]
      state.xData = [self.config.SSToFloat(state.currentss)]

      #Dynamically adjust ss and iso.
      self.dynamic_adjust(init_config, state)
      print ('ss: % 10d\tx: % 6.4f br: % 4d\t' 
             % (state.currentss, round(state.xData[-1], 4), round(state.brData[-1], 4)))
      if state.xData[-1] >= 1.0:
        if killtoken == True:
          break
        else:
          killtoken = True
      elif state.xData[-1] <= 0.0:
        if killtoken == True:
          break
        else:
          killtoken = True
    return True

  def shoot(self, filename=None, ss_adjust=True, config=None, state=None):
    """
    Take a photo and save it at a specified filename.
    """
    if config is None: config = self.config
    if state is None: state = self.state
    im = self.capture(config, state)
    #Saves file without exif and raster data; reduces file size by 90%,
    if filename != None:
      im.save(filename)

    if not ss_adjust: return im

    state.lastbr = self.avgbrightness(im)
    if len(state.brData) >= config.brightwidth:
      state.brData = state.brData[1:]
      state.xData = state.xData[1:]
    state.xData.append(self.config.SSToFloat(state.currentss))
    state.brData.append(state.lastbr)

    #Dynamically adjust ss and iso.
    state.avgbr = sum(state.brData) / len(state.brData)
    self.dynamic_adjust(config, state)
    state.shots_taken += 1

    delta = config.targetBrightness - state.lastbr
    if abs(delta) > config.maxdelta:
      #Too far from target brightness.
      state.shots_taken -= 1
      os.remove(filename)
    return im

  def print_stats(self):
    tmpl = 'SS: % 10d\tX: % 8.3f\tBR: % 4d\tShots: % 5d'
    state = self.state
    x = self.config.SSToFloat(state.currentss)
    print tmpl % (state.currentss, round(x,2), state.lastbr, state.shots_taken)

  def run_timelapse(self, config=None, state=None):
    """
    Takes pictures at specified interval.
    """
    if config is None: config = self.config
    if state is None: state = self.state
    start_time = time.time()
    elapsed = time.time() - start_time

    #Set up broadcast for zmq.
    self.context = zmq.Context()
    self.socket = self.context.socket(zmq.PUB)
    self.socket.bind("tcp://*:5556")

    while ((elapsed < config.maxtime or config.maxtime == -1) 
           and (state.shots_taken < config.maxshots
                or config.maxshots == -1)):
      loopstart = time.time()
      dtime = subprocess.check_output(['date', '+%y%m%d_%T']).strip()
      dtime = dtime.replace(':', '.')
      #Broadcast options for this picture on zmq.
      command='0 shoot {} {} {} {}'.format(config.w, config.h, 
                                           state.currentss, dtime)
      self.socket.send(command)

      #Take a picture.
      filename = ('/home/pi/pictures/%s_%s.jpg' % (self.hostname, dtime))
      self.shoot(filename=filename)

      loopend = time.time()
      x = config.SSToFloat(state.currentss)
      self.print_stats()

      #Wait for next shot.
      time.sleep(max([0, config.interval - (loopend - loopstart)]))

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
      # Add more configuration options here, if desired.
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
