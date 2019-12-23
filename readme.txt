September 2019
Having not looked at my pythonOCC code from 2016 in over  3 years, I decided to
dust it off and give it a fresh look.
I was disappointed to discover that pyocc has made almost no progress over this time.
It almost seems like it's been abandoned. Nontheless, I proceeded to load the latest
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