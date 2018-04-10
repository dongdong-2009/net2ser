#!/usr/bin/python
import serial
import serial.tools.list_ports
import sys
import os
from samba.dcerpc.xattr import sys_acl_hash_wrapper
from array import array
from pip._vendor.requests.api import put
from time import sleep

def ser_select():
    lst = list(serial.tools.list_ports.comports())
    if len(lst) <= 0:
        print('no serial port found.')
    else:
        print('found %d ports .'%(len(lst)))
        for i in range(len(lst)):
            p = lst[i]
            print('%d. %s - %s (%s)'%(i,p.device,p.description,p.manufacturer))
        print 'please select:'
        input = sys.stdin.readline().strip()
        idx = int(input) if input.isdigit() else -1
        while(idx<0 or idx>=len(lst)):
            print 'please select a port(%d~%d):'%(0,len(lst)-1)
            input = sys.stdin.readline().strip()
            idx = int(input) if input.isdigit() else -1
        return lst[idx].device
    return None

def ser_open(port,baudrate,read_timeout,read_inter_byte_timeout=None,bytesize=8,parity='N',stopbits=1):
    try:
        s = serial.Serial();
        s.port = port
        s.baudrate = baudrate
        s.bytesize = bytesize
        s.parity = parity
        s.stopbits = stopbits
        s.timeout = read_timeout
        s.inter_byte_timeout = read_inter_byte_timeout
    #    s.write_timeout = 1
        s.dsrdtr = False
        s.rtscts = False
        s.xonxoff = False
        s.open()
        if s.isOpen():
            return s
        else:
            return None
    except:
        return None

def put(text,color):
#     if(color=='white'):
#         sys.stdout.write('\033[1,47,40m');
#     elif(color=='green'):
#         sys.stdout.write('\033[1,32,40m');
    sys.stdout.write(text);
#     sys.stdout.write('\033[0m');
        

mg3732_rules = {
    '@!rule_name':'mg3732(wcdma)',
    '@!at_endline':'\r\n',
    '@!at_delay':1,
    '@!init_max_framsize':4096,
    '@!init_serial_baudrate':115200,
    '@!init_serial_datafram_timeout':0.5,#5k byte datafram @115kbps
    '@!init_serial_databyte_timeout':0.001, 
    
    'TK+RESET':'OK',
    'ATE0':'OK',
    'AT':'OK',
    'AT+CGSN':'CGSN:123456789012345',
    }
rules = (
    mg3732_rules,
    )

if __name__ == '__main__':
    for i in range(len(rules)):
        print '%d. %s'%(i,rules[i].get('@!rule_name'))
    print 'please select a module rules:'
    input = sys.stdin.readline().strip()
    idx = int(input) if input.isdigit() else -1
    while(idx<0 or idx>=len(rules)):
        print 'please select a module rules(%d~%d):'%(0,len(rules)-1)
        input = sys.stdin.readline().strip()
        idx = int(input) if input.isdigit() else -1
    rule = dict(rules[idx])
    port = ser_select()
    ser = ser_open(port,
                   rule.get('@!init_serial_baudrate'),
                   rule.get('@!init_serial_datafram_timeout'),
                   rule.get('@!init_serial_databyte_timeout'))
    max_framsize = rule.get('@!init_max_framsize')
    at_endline = rule.get('@!at_endline')
    at_delay = rule.get('@!at_delay')
    ser.flush()
    at_talk_run = True
    while(at_talk_run):
        f = ser.read(max_framsize)
        if(len(f)==0):continue;
        put('+++['+f+']+++','white')
        #lines = f.strip().split('\r\n')
        #f = lines[len(lines)-1]
        #put('++['+f+']++','white')
        for k in rule:
            if(k.startswith('@!')):continue
            if(f.find(k+at_endline)>=0):
                v = rule[k]
                if isinstance(v, str):
                    tx = v + at_endline
                    ser.write(tx)
                    put('---['+tx+']---','blue')
                elif isinstance(v, tuple):
                    for i in v:
                        tx = i + at_endline
                        ser.write(tx)
                        put('---['+tx+']---','blue')
                elif isinstance(v, function):
                    print 'sss'
                else:
                    print ''
        
        sleep(at_delay)    
    print 'end.'
    exit(0)
    
