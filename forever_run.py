#!/usr/bin/python3
from multiprocessing import Process
from flight_checker import NA1
from monitor import run
import time

if __name__ == '__main__':
    while True:
        p1 = Process(target = NA1)
        p2 = Process(target = run)
        p1.start()
        p2.start()
        while p1.is_alive() and p2.is_alive():
            time.sleep(1)
        print("Restart process")
        p1.terminate()
        p2.terminate()
        p1.join()
        p2.join()

     

