This folder is a copy of "site-packages/OCC/Display".
Having this local copy facilitates changing the navigation controls.
Mouse button navigation controls are defined in the file qtDisplay.py.

Navigation controls have been modified as follows:
Ctrl LMB	Pan
Ctrl MMB	Rotate
Ctrl RMB	Zoom

Using the Ctrl key as a modifier is intended to make it less likely to
accidentally make a screen selection while navigating.
This should reduce the problem of unwanted screen picks being sent to
the registered callback function.
