#!/usr/bin/python
from subprocess import Popen
import sys
import os
p1 = Popen("python flight_checker.py")
p2 = Popen("python monitor.py")
p1.wait()
p2.wait()
