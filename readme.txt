This folder is like an old attic in a sense. It contains all sorts of code that I have
written over the years, as I experimented with what and how I might go about writing
a CAD application built on PythonOCC.  Decided to post it on GitHub.

September 2019
Having not looked at my cadViewer code from 2016 in over 3 years, I considered 
dusting it off and giving it a fresh look.
I was disappointed to discover that pythonocc has made almost no progress over this time.
I posted a version of my code online at https://sites.google.com/site/pythonocc/cadviewer
with a screenshot which showed I was using pythonocc version 0.16.3-dev at the time.
It almost seems like PythonOCC has been abandoned. Nontheless, I proceeded to load the latest
conda pyocc installation (version 0.18.1) with various pythons: 2.7, 3.5, 3.6
The only way I could run the 'classic OCC bottle' was by using Python 2.7
In none of the variations was I able to use PyQt4, but instead needed to use PyQt5.
I started but didn't persevere through the challenge of getting my pyocc cad code
to run using pyqt5.

My goal has always been to come up with a CAD app that is capable of directly editing
CAD models, like SolidDesigner. However, I satisfied myself that OCC was not up to 
that task back in 2016 and I think that now it is even further from that goal.

Even if there were a clear path forward w/r/t direct editing, there are many things
that would have to be undertaken:
PyQt
undo/redo
STEP/Iges Load/Save

December 2019
PythonOCC isn't dead after all! Pyocc7.4.0-beta just released, with conda install.
I decided to have another go at getting my old code working on this latest version.
Emailed Thomas Paviot asking for useful resources to help me understand the changes
in the API from version 0.16 to the current version. His advice:

"""
pythonocc-0.16.3 is 4 years old, in the meantime code has changed because of :

* API changes from opencascade. Have a look at the release notes for each release. Most changes occurred when switching to occt7x series (see https://www.opencascade.com/content/previous-releases for an history of opencascascade releases) ;

* changes in pythonocc itself. There have been two major changes that you have to know about while porting your old code to the new release :

1. The package structure has changed. You have to move all 'from OCC.xxx import xxx' to 'from OCC.Core.xxx import xxx'. That's not a big deal.

2. There is not Handle anymore. GetHandle and GetObject methods have disappeared. Just pass the object itself, the wrapper decides wether it has to pass the Handle or the Object to the C++ layer. You can check this commit (https://github.com/tpaviot/pythonocc-demos/commit/e59acdce5720d84ce76134789b48c268e36446d6#diff-68b70730ce65eb74e098809766ab3d0d), where we ported the old 'occ bottle example'.
"""

Here is my initial progress, so far:

cadViewer.py produces the GUI (but it still crashes when any of the buttons are clicked).

import STEP kind of works, but part names don't show up.
