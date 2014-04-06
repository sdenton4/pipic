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
Here's a list of prerequisites to install on your pi for use with the django interface:
- python-django-celery
- python-django-south

