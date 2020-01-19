# cadviewer
Simple 3D CAD app using PythonOCC and PyQt5

Jan 19, 2020: I think the code is now working pretty much as it was when I
stopped maintaining it back in 2016. I jotted a brief summary and posted a
current screenshot at https://dblanding.github.io/cadviewer/

Jan 17, 2020: Got construction lines (on the toolbar) working.
Also got fillet and shell working. Measure pt_to_pt distance and edge_length
(on the calculator) are now working.

Jan 16, 2020: Updated 'bottle demo' and added it to the menu bar,
enabling step by step building of the OCC Classic Bottle.

Jan 4, 2020:  Progress has been better than I had hoped. 
The basic GUI is all there with all the widgets, 
STEP files can be loaded and they show up both in the display
and with their correct assembly structure in the assembly/parts tree, 
The RMB context menu works, 
Workplanes can be created using three different methods, 
The calculator works and seems to be communicating with the main window. 


This repo is like an old attic in a sense. It contains various code that I have
written as I have experimented with what and how I might go about writing
a CAD application built on PythonOCC.  I decided to post it on GitHub.

I stumbled across some work I did a few years ago, where I started to build a simple
CAD app using PythonOCC running on Python 2.7 using PyQt4. Having not looked at it in
over 3 years, I wasn't sure it would be worth the trouble to get it working again with
PyhonOCC version 7.4.0 while switching to Python 3 and PyQt5 all at once.
A screenshot from some old code posted online:
https://sites.google.com/site/pythonocc/cadviewer
reminds me that I was using PythonOCC version 0.16.3-dev at that time. 
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


Here's my todo list, roughly in order of priority:

	Get Geometry lines (on toolbar) working to make wire profiles.

	Adopt OCAF doc as tree model. Be able to save & load from file

	Clean up code with a linter.

	Assign a version number.

	Add ability to write STEP file of assembly selected from tree.

	Add ability to create, modify and move 3D parts & assemblies.
	checkout links in Jelle's old post:
	https://groups.google.com/forum/#!topic/pythonocc/Ed86PGoNtIs
