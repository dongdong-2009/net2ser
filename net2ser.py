#!/usr/bin/python
import serial
import serial.tools.list_ports
import sys
import os
import re
import socket
import binascii
from scanf import scanf


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
    if(color=='white'):
        sys.stdout.write('\033[1;37;40m');
    elif(color=='green'):
        sys.stdout.write('\033[1;32;40m');
    sys.stdout.write(text);
    sys.stdout.write('\033[0m');
        
      
class Config:
    k = None
    v = None
    def __init__(self,key,value):
        self.k = key
        self.v = value
        
class Rule:
    k = None
    v = None
    p = None
    def __init__(self,key,value,process=None):
        self.k = key
        self.v = value
        self.p = process

        
def get_init_param(module,key):
    for r in module:
        if(isinstance(r, Config)):
            if r.k==key:return r.v;
            

def get_local_ip():
        ip=''
        try:
            frame = os.popen("""route|awk 'BEGIN{m="65535";frame=""}{if(index($4,"U")>0&&$5<m){m=$5;frame=$8}}END{print frame}'""")
            nic = frame.read().strip()
            frame.close()
            frame = os.popen("ifconfig " + nic + "| grep 'inet addr' | sed 's/^.*addr://g' | sed 's/Bcast.*$//g'")
            ip = frame.read().strip()
            frame.close()
            return ip
        except:
            return '0.0.0.0'
        
sock_dict={}
def do_socket_connect(param):
    global sock_dict
    force_rm_ip = param['force_rm_ip']
    force_rm_port = param['force_rm_port']
    if(force_rm_ip!=None):param['rm_ip']=force_rm_ip
    if(force_rm_port!=None):param['rm_port']=force_rm_port
    rm_ip = param['rm_ip']
    rm_port = param['rm_port']
    sock_id = param['sock_id']
    
    s = socket.socket()
    s.setblocking(False)
    s.settimeout(0.1)
    try:
        s.connect((rm_ip,rm_port))
        if(sock_dict.has_key(sock_id)):
            sock_dict.get(sock_id).close()
        sock_dict[sock_id] = s
    except:
        s=None
    param['sock_state'] = 1 if s!=None else 0
    param['sock_state_n'] = 0 if param['sock_state']==1 else 1
    param['net_connect_flag_str'] = '' if param['sock_state']==0 else param['net_connect_flag_str']
    return True

def do_socket_close(param):
    sock_id = param['sock_id']
    try:
        if(sock_dict.has_key(sock_id)):
            sock_dict.get(sock_id).close()
    except:
        pass
    param['sock_state'] = 0
    param['sock_state_n'] = 0 if param['sock_state']==1 else 1
    param['net_connect_flag_str'] = '' if param['sock_state']==0 else param['net_connect_flag_str']
    return True

def do_socket_send(param):
    global sock_dict
    sock_id = param['sock_id']
    try:
        if(sock_dict.has_key(sock_id)):
            s = sock_dict[sock_id]
            send_dat_asc = param['send_dat_asc']
            s.send(binascii.a2b_hex(send_dat_asc))
            param['at_return'] = 'OK'
        else:
            param['at_return'] = 'NOTCONNECT'
        return
    except:
        param['at_return'] = 'ERROR'
    return True

def do_socket_recv(param):
    for i in sock_dict.keys():
        sock = sock_dict[i]
        try:
            r = sock.recv(4096)
            if(len(r)>0):
                ipport = sock.getpeername()
                param['sock_id'] = i
                param['recv_dat_asc'] = binascii.b2a_hex(r)
                param['recv_len'] = len(r)
                param['rm_ip'] = ipport[0]
                param['rm_port'] = ipport[1]
                return True
        except:
            pass
    return False  

#########################
#default params
param = {}
param['local_ip'] = get_local_ip()
param['net_state'] = 0 if param['local_ip']=='0.0.0.0' else 1
param['net_connect_flag_str'] = 'CONNECT'
param['rm_ip'] = '0.0.0.0'
param['rm_port'] = '1000'
param['force_rm_ip'] = None
param['force_rm_port'] = None
param['send_dat_bin'] = ''
param['send_dat_asc'] = ''
param['send_len'] = 0
param['recv_dat_bin'] = ''
param['recv_dat_asc'] = ''
param['recv_len'] = 0
param['at_return'] = 'OK'

#############################################################################################
param['imei'] = '123456789012345'   #imei
param['ismi'] = '123456789012345'   #sim no
param['force_rm_ip'] = '180.89.58.27'
param['force_rm_port'] = 9020
mg3732_module = (
    Config('rule_name',                       'mg3732(wcdma)'),
    Config('at_endline',                      '\r\n'),
    Config('init_max_framsize',               4096),
    Config('init_serial_baudrate',            115200),
    Config('init_serial_datafram_timeout',    0.5),#5k byte datafram @115kbps
    Config('init_serial_databyte_timeout',    0.001), 
    
    Rule('TK+RESET',                        'OK'),
    Rule('ATE0',                            'OK'),
    Rule('AT',                              'OK'),
    Rule('AT+CGSN',                         ('+CGSN:%s','imei')),
    Rule(('AT+ZIPCFG=%s','apn'),            'OK'),
    Rule('AT+CIMI',                         ('+CIMI:%s','ismi')),
    Rule('AT+ZIPCALL=1',                    ('OK\r\n+ZIPCALL: %d,%s','net_state','local_ip')),
    Rule(('AT+ZIPOPEN=%d,0,%s,%d,%d','sock_id','rm_ip','rm_port','lc_port'),
                                            ('OK\r\n+ZIPSTAT: %d,%d','sock_id','sock_state'),
                                                                    do_socket_connect),
    Rule(('AT+ZIPCLOSE=%d','sock_id'),      'OK',                   do_socket_close),
    Rule(('AT+ZIPSEND=%d,%s','sock_id','send_dat_asc'),
                                            ('%s','at_return'),     do_socket_send),
    
    Rule(None,   ('+ZIPRECV: %d,%s,%d,%i,%s','sock_id','rm_ip','rm_port','recv_len','recv_dat_asc'),
                                                                    do_socket_recv),
    )



modules = (
    mg3732_module,
    )

if __name__ == '__main__':
    #select a module
    for i in range(len(modules)):
        print '%d. %s'%(i,get_init_param(modules[i],'rule_name'))
    print 'please select a module modules:'
    input = sys.stdin.readline().strip()
    idx = int(input) if input.isdigit() else -1
    while(idx<0 or idx>=len(modules)):
        print 'please select a module modules(%d~%d):'%(0,len(modules)-1)
        input = sys.stdin.readline().strip()
        idx = int(input) if input.isdigit() else -1
    module = tuple(modules[idx])
    
    #select a serial
    port = ser_select()
    ser = ser_open(port,
                   get_init_param(module,'init_serial_baudrate'),
                   get_init_param(module,'init_serial_datafram_timeout'),
                   get_init_param(module,'init_serial_databyte_timeout'))
    max_framsize = get_init_param(module,'init_max_framsize')
    at_endline = get_init_param(module,'at_endline')
            
    #process   
    ser.flush()
    at_talk_run = True
    while(at_talk_run):    
        rule = None
        frame = ser.read(max_framsize)
        if(len(frame)>0):
            #put('+++['+frame+']+++','white')
            put(frame,'white')
            frame = frame.strip()
            for item in module:
                if(isinstance(item, Config)):
                    continue
                if(isinstance(item, Rule)):
                    key = item.k
                    value = item.v
                    tx=''
                    if(isinstance(key, str) and key==frame):
                        rule = item
                        break
                    elif(isinstance(key, tuple)):
                        res = scanf(key[0],frame)
                        if(res!=None and len(res)==len(key)-1):
                            for i in range(len(res)):
                                param[key[i+1]]=res[i]
                                rule = item
                            break
                    else:
                        continue
        else:
            for item in module:
                if(item.k==None):
                    rule = item

        if(rule!=None):
            value = rule.v
            if rule.p!=None:
                res = rule.p(param)
                if(res==False): continue
            if(isinstance(value, str)):
                tx = value + at_endline
                ser.write(tx)
            elif(isinstance(value, tuple)):
                plist = list(value[1:])
                for i in range(len(plist)):
                    try:
                        plist[i] = param[plist[i]]
                    except:
                        print 'get param error: key=%s'%plist[i]
                        exit(-1)
                tx = value[0]%tuple(plist) + at_endline
                ser.write(tx)
            else:
                continue
            #put('---['+tx+']---','green')
            put(tx,'green')
                
                
    print 'end.'
    exit(0)
    
