import Decoder as NECD
import RPi.GPIO as gpio
import pigpio
from os import system


system("sudo pigpiod")


while(1):
    b = NECD.necd()
    i=0
    pi = pigpio.pi()
    pin = 14
    b.init(pi,pin)

    b.enable()
    a = b._analyse_ir_pulses()
    while(i<=30000):
        i=i+1

    if a == 1:
        break
    

 
