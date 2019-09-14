#!/usr/bin/env python
#
# CADvas 
# A 2D CAD application written in Python and based on the Tkinter canvas.
# The latest  version of this file can be found at:
# http://members.localnet.com/~blanding/cadvas
#
# Author: Doug Blanding   <doug dot blanding at localnet dot com>
#
# CADvas is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# CADvas is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with CADvas; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from __future__ import division
import sys
from Tkinter import *
import math

def but(root, text, row, col, com=None, span=2, clr='darkslateblue', pad=1): 
    w = Button(root, text=text, command=com, bg=clr, fg='white', padx=pad)
    w.grid(row=row, column=col, columnspan=span, sticky=E+W)

def ent(root, var, row, col=2, span=10):
    e = Entry(root, textvariable=var, relief=SUNKEN)
    e.grid(row=row, column=col, columnspan=span)

def f2s(f):
    """Convert float to string with 12 significant figures."""
    return '%1.12f' % f

class Calculator(Toplevel):
    """RPN (Reverse Polish Notation) calculator styled after the one
    used in CoCreate SolidDesigner CAD."""
    mem = ''
    keip = False    # Flag set when keyboard entry is in progress
    needrup = False # Flag signaling need to rotate up with next keyboard entry
    def __init__(self, caller=None):
        Toplevel.__init__(self)
        self.caller = caller    # ref to Draw instance
        self.title('RPN Calc')
        self.protocol("WM_DELETE_WINDOW", self.quit)
        #self.resizable(width=0, height=0)
        if caller:
            self.transient(caller)
        
        but(self, 't', 0, 0, lambda r='t': self.pr(r), clr='dimgray')
        but(self, 'z', 1, 0, lambda r='z': self.pr(r), clr='dimgray')
        but(self, 'y', 2, 0, lambda r='y': self.pr(r), clr='dimgray')
        but(self, 'x', 3, 0, lambda r='x': self.pr(r), clr='dimgray')

        self.tdisplay = StringVar()
        self.zdisplay = StringVar()
        self.ydisplay = StringVar()
        self.xdisplay = StringVar()
        ent(self, self.tdisplay, 0)
        ent(self, self.zdisplay, 1)
        ent(self, self.ydisplay, 2)
        ent(self, self.xdisplay, 3)

        but(self, 'mm->in', 4, 0, self.mm2in, span=4, clr='dimgray')
        but(self, 'in->mm', 4, 4, self.in2mm, span=4, clr='dimgray')
        but(self, 'Sto', 4, 8, self.storex, clr='darkgreen')
        but(self, 'Rcl', 4, 10, self.recallx, clr='darkgreen')
        but(self, '7', 5, 0, lambda c='7': self.keyin(c), clr='steelblue')
        but(self, '8', 5, 2, lambda c='8': self.keyin(c), clr='steelblue')
        but(self, '9', 5, 4, lambda c='9': self.keyin(c), clr='steelblue')
        but(self, '+', 5, 6, lambda op='+': self.calc(op))
        but(self, 'Rup', 5, 8, self.rotateup, clr='darkgreen')
        but(self, 'Rdn', 5, 10, self.rotatedn, clr='darkgreen')
        but(self, '4', 6, 0, lambda c='4': self.keyin(c), clr='steelblue')
        but(self, '5', 6, 2, lambda c='5': self.keyin(c), clr='steelblue')
        but(self, '6', 6, 4, lambda c='6': self.keyin(c), clr='steelblue')
        but(self, '-', 6, 6, lambda op='-': self.calc(op))
        but(self, '<-', 6, 8, self.trimx, clr='darkred')
        but(self, 'x<>y', 6, 10, self.swapxy, clr='darkgreen', pad=0)
        but(self, '1', 7, 0, lambda c='1': self.keyin(c), clr='steelblue')
        but(self, '2', 7, 2, lambda c='2': self.keyin(c), clr='steelblue')
        but(self, '3', 7, 4, lambda c='3': self.keyin(c), clr='steelblue')
        but(self, '*', 7, 6, lambda op='*': self.calc(op))
        but(self, 'Clx', 7, 8, self.clearx, clr='darkred')
        but(self, 'Clr', 7, 10, self.clearall, clr='darkred')
        but(self, '0', 8, 0, lambda c='0': self.keyin(c), clr='steelblue', pad=3)
        but(self, '.', 8, 2, lambda c='.': self.keyin(c))
        but(self, '+/-', 8, 4, lambda op='+/-': self.calc(op))
        but(self, ' / ', 8, 6, lambda c='/': self.calc(c), pad=3)
        but(self, 'ENTER', 8, 8, self.enter, span=4, clr='darkgoldenrod')
        but(self, 'Sin', 9, 0, lambda op='math.sin(x)': self.func(op, in_cnvrt=1),
            span=3, clr='darkgoldenrod')
        but(self, 'Cos', 9, 3, lambda op='math.cos(x)': self.func(op, in_cnvrt=1),
            span=3, clr='darkgoldenrod')
        but(self, 'Tan', 9, 6, lambda op='math.tan(x)': self.func(op, in_cnvrt=1),
            span=3, clr='darkgoldenrod')
        but(self, 'Pi', 9, 9, lambda op='math.pi': self.func(op), span=3, clr='darkgoldenrod')
        but(self, 'ASin', 10, 0, lambda op='math.asin(x)': self.func(op, out_cnvrt=1),
            span=3, clr='darkgoldenrod')
        but(self, 'ACos', 10, 3, lambda op='math.acos(x)': self.func(op, out_cnvrt=1),
            span=3, clr='darkgoldenrod')
        but(self, 'ATan', 10, 6, lambda op='math.atan(x)': self.func(op, out_cnvrt=1),
            span=3, clr='darkgoldenrod')
        but(self, '', 10, 9, span=3, clr='darkgoldenrod')
        but(self, 'x^2', 11, 0, lambda op='x**2': self.func(op), span=3, clr='darkgreen')
        but(self, '1/x', 11, 3, lambda op='1/x': self.func(op), span=3, clr='darkgreen')
        but(self, 'e^x', 11, 6, lambda op='math.e**x': self.func(op), span=3, clr='darkgreen')
        but(self, '10^x', 11, 9, lambda op='10**x': self.func(op), span=3, clr='darkgreen')
        but(self, 'Sqrt', 12, 0, lambda op='math.sqrt(x)': self.func(op), span=3, clr='darkgreen')
        but(self, 'y^x', 12, 3, lambda op='y**x': self.func(op), span=3, clr='darkgreen')
        but(self, 'ln', 12, 6, lambda op='math.log(x)': self.func(op), span=3, clr='darkgreen')
        but(self, 'log', 12, 9, lambda op='math.log10(x)': self.func(op), span=3, clr='darkgreen')
        

    def quit(self):
        if self.caller:
            self.caller.calculator = None
        self.destroy()

    def pr(self, val):
        """Send value in register to caller."""
        # There must be a better way to get this value
        str_value = `eval('self.'+val+'display.get()')`.strip("'")
        self.caller.enterfloat(str_value)
        self.keip = False
        self.needrup = True

    def keyin(self, c):
        if self.keip:
            self.xdisplay.set(self.xdisplay.get()+c)
        else:
            self.keip = True
            if self.needrup:
                self.rotateup(loop=0)
            self.clearx()
            self.keyin(c)

    def enter(self):
        self.tdisplay.set(self.zdisplay.get())
        self.zdisplay.set(self.ydisplay.get())
        self.ydisplay.set(self.xdisplay.get())
        self.keip = False
        self.needrup = False

    def calc(self, op):
        """Arithmetic calculations between x and y registers, then rotate down."""
        try:
            if op == '+/-':
                self.xdisplay.set(`eval('-'+self.xdisplay.get())`)
            else:
                x = `eval(self.ydisplay.get()+op+self.xdisplay.get())`
                self.xdisplay.set(x)
                self.ydisplay.set(self.zdisplay.get())
                self.zdisplay.set(self.tdisplay.get())
            self.keip = False
            self.needrup = True
        except:
            self.xdisplay.set("ERROR")


    def func(self, op, in_cnvrt=0, out_cnvrt=0):
        """Evaluate function op then put result in x-register, don't rotate stack.
        if in_cnvrt: convert input value of x-register from degrees to radians.
        if out_cnvrt: convert output value of x-register from radians to degrees."""
        try:
            x = float(self.xdisplay.get())
        except:
            x = 0
        try:
            y = float(self.ydisplay.get())
        except:
            y = 0
        if in_cnvrt:
            x = x * math.pi / 180
        result = eval(op)
        if out_cnvrt:
            result = result * 180 / math.pi
        self.xdisplay.set(f2s(result))
        self.keip = False
        self.needrup = True

    def mm2in(self):
        if self.xdisplay.get():
            self.xdisplay.set(`eval(self.xdisplay.get()+'/25.4')`)
            self.keip = False
            self.needrup = True

    def in2mm(self):
        if self.xdisplay.get():
            self.xdisplay.set(`eval(self.xdisplay.get()+'*25.4')`)
            self.keip = False
            self.needrup = True

    def storex(self):
        self.mem = self.xdisplay.get()
        self.keip = False
        self.needrup = True

    def recallx(self):
        self.rotateup()
        self.xdisplay.set(self.mem)
        self.keip = False
        self.needrup = True

    def rotateup(self, loop=1):
        x = self.tdisplay.get()
        self.tdisplay.set(self.zdisplay.get())
        self.zdisplay.set(self.ydisplay.get())
        self.ydisplay.set(self.xdisplay.get())
        if loop:
            self.xdisplay.set(x)

    def rotatedn(self):
        x = self.xdisplay.get()
        self.xdisplay.set(self.ydisplay.get())
        self.ydisplay.set(self.zdisplay.get())
        self.zdisplay.set(self.tdisplay.get())
        self.tdisplay.set(x)

    def trimx(self):
        self.xdisplay.set(self.xdisplay.get()[:-1])

    def swapxy(self):
        x = self.xdisplay.get()
        y = self.ydisplay.get()
        self.xdisplay.set(y)
        self.ydisplay.set(x)

    def clearx(self):
        self.xdisplay.set('')
        
    def clearall(self):
        self.xdisplay.set('')
        self.ydisplay.set('')
        self.zdisplay.set('')
        self.tdisplay.set('')

    def putx(self, value):
        if self.needrup:
            self.rotateup(loop=0)
        self.xdisplay.set(`value`)
        self.keip = False
        self.needrup = True

if __name__ == '__main__':
    Calculator().mainloop()
