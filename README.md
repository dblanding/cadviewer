# cadviewer
Simple 3D CAD app using PythonOCC and PyQt5

This repo is like an old attic in a sense. It contains various code that I have
written as I have experimented with what and how I might go about writing
a CAD application built on PythonOCC.  I decided to post it on GitHub.

I stumbled across some work I did a few years ago, trying to build a simple CAD app
using PythonOCC. Having not looked at it in over 3 years, I wasn't sure it would be
worth the trouble to get it running on the latest version of PyhonOCC and Python 3.
A screenshot from some old code posted online:
https://sites.google.com/site/pythonocc/cadviewer
reminds me that I was using PythonOCC version 0.16.3-dev at the time. 
With the recent release of PyOCC version7.4.0-beta, I decided to give it a go.
I asked Thomas Paviot for useful resources to help me understand the changes
in the API from version 0.16 to the current version. His advice was very helpful:

"""
pythonocc-0.16.3 is 4 years old, in the meantime code has changed because of :

* API changes from opencascade. Have a look at the release notes for each release. Most changes occurred when switching to occt7x series (see https://www.opencascade.com/content/previous-releases for an history of opencascascade releases) ;

* changes in pythonocc itself. There have been two major changes that you have to know about while porting your old code to the new release :

1. The package structure has changed. You have to move all 'from OCC.xxx import xxx' to 'from OCC.Core.xxx import xxx'. That's not a big deal.

2. There is not Handle anymore. GetHandle and GetObject methods have disappeared. Just pass the object itself, the wrapper decides wether it has to pass the Handle or the Object to the C++ layer. You can check this commit (https://github.com/tpaviot/pythonocc-demos/commit/e59acdce5720d84ce76134789b48c268e36446d6#diff-68b70730ce65eb74e098809766ab3d0d), where we ported the old 'occ bottle example'.
"""

Here is my progress (so far) on getting it running again:

cadViewer.py produces the main GUI (but still crashes when the buttons are clicked).

got import STEP kind of working, but part names are still broken.

