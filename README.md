pipic
=====

Tools for Raspberry Pi photography


This repository contains scripts I am using for timelapse projects with the raspberry pi.
The important parts are:

timelapse.py:
    Takes photos at a specified interval.
    
deflicker.py:
    Touches up timelapsed photos by applying auto-levelling, brightness adjustment, and pixel averaging (if desired).


There are also some tools for getting the Pi ready to roll.

loadOut.py:
    Copy various configuration files onto a disk that will be used with the Pi.
    Also sets hostname, timezone, and does some other housekeeping.

--------------------------------------------------------------

We're also working on building a Django server for managing all your timelapse needs.

There are a couple pre-requisites, though.   Use the python 'pip' installer to make sure you have recent versions of each.  
`sudo apt-get install python-pip`
Then:
`pip install -U django`
`pip install -U south`
`pip install -U django-celery`
