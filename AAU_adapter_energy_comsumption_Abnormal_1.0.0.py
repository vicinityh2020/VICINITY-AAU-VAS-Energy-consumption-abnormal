from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse
import requests
import socket   
import json
import time
import threading

#define global vars default state
Global_state_oven_device_status = b'I'
stopflag = 0

#define global OID of devices
OID_Oven_7 = '9b4f2d11-addf-46b0-bec5-0773f5763612'
 
#Enquire data and state from EMS
#Publish events to subscribers through VICINITY agnet
def timerfun_publishevent():
   
   global handel_timer_publishevent
   global stopflag
   
   #Inquire state data from Labview for Charging price
   handel_TCPclient_interruptthread.send(b'Read_EMSstat_NNN') 
   responsestring = handel_TCPclient_interruptthread.recv(10) 

   #Rearrange received data from EMS
   OverPowerComsumption = responsestring[9:10]

   #Derive System time
   ISOTIMEFORMAT = '%Y-%m-%d %X'        
   systemtime = time.strftime(ISOTIMEFORMAT,time.localtime())
   systemtime = str(systemtime)
   systemtime = bytes(systemtime, encoding = "utf8")
   
   if (OverPowerComsumption == b'1'):
       
       print('The over power comsumption alarm should be published here!')  
       
       #Publish the Abnormal Energy Comsumption Alarm event
       hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_ECA'}
       url = 'http://localhost:9997/agent/events/AbnormalEnergyComsumptionAlarm'     
       payload = b'{' + b'"state":"alarm",' + b'"time":"'+ systemtime +b'"}'
       r=requests.request('PUT',url,headers=hd,data = payload)
       print(r.text)     
   
   handel_timer_publishevent = threading.Timer(5,timerfun_publishevent,())         
   
   if stopflag==1:
        handel_timer_publishevent.cancel()
   else:
        handel_timer_publishevent.start()
   

#Handle the http requests from VICINITY agent 
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
 
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
 
        querypath = urlparse(self.path)
        path = str(querypath.path)
        
        Name_startnum = path.find('properties/')##
        queryitemName = path[Name_startnum+10:];
        
        ISOTIMEFORMAT = '%Y-%m-%d %X'        
        systemtime = time.strftime(ISOTIMEFORMAT,time.localtime())
        systemtime = str(systemtime)
        systemtime = bytes(systemtime, encoding = "utf8")

        if (queryitemName=='/Load_ActivePower'):
           senddata = b'Read_Load_AP_NNN'  
           handel_TCPclient_mainthread.send(senddata) 
           data=handel_TCPclient_mainthread.recv(4)
          
           self.wfile.write(b'{')  
           
           self.wfile.write(b'"value":"')  
           self.wfile.write(data)
           self.wfile.write(b'"')    

           self.wfile.write(b',')  

           self.wfile.write(b'"time":"')  
           self.wfile.write(systemtime)
           self.wfile.write(b'"')  
           
           self.wfile.write(b'}')          
            
        else:
            self.wfile.write(b'HTTP/1.1 406 Failed')             
 
    def do_POST(self):
        
        global stopflag
        
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        self.send_response(200)
        self.end_headers()
                  
        string = body.decode() #encode()
        string = json.loads(string)
        
        control_ID=string['control_ID']
        control_val=string['value']
        
        if (control_ID=='shutdown' and control_val=='1'):
            response = BytesIO()
            response.write(b'HTTP/1.1 200 OK/Server is shutdown successfully')
            self.wfile.write(response.getvalue())   
            httpd.shutdown
            httpd.socket.close()            
            print('AAU adapter is shutdown successfully!')
            stopflag = 1
    
        else:
            response = BytesIO()
            response.write(b'HTTP/1.1 406 Failed')
            self.wfile.write(response.getvalue())   
 
    def do_PUT(self):
        
        global Global_state_oven_device_status
        global OID_Oven_7
        
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        self.send_response(200)
        self.end_headers()     
                    
        if (self.path.count(OID_Oven_7) == 1):  #Oven   
            string = body.decode() #encode()
            print(string)                           
                
            if (string.count('device_status') == 1 and string.count('RUNNING') == 1):
                Global_state_oven_device_status = b'R'  
                
            elif (string.count('device_status') == 1 and string.count('PAUSE') == 1):
                Global_state_oven_device_status = b'I'  
                
            elif (string.count('device_status') == 1 and string.count('IDLE') == 1):
                Global_state_oven_device_status = b'I'  
          
            else:
                response = BytesIO()
                response.write(b'HTTP/1.1 406 Failed')
                self.wfile.write(response.getvalue())                       
                   
            Finalsenddata = b'USet_OvenSta_' + b'N' + Global_state_oven_device_status + b'N'   
            handel_TCPclient_mainthread.send(Finalsenddata)        

if __name__ == '__main__':
     #Create handel for TCP client to connect to Labview (main)  
     address = ('17486633in.iask.in', 31127)  
     handel_TCPclient_mainthread = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
     handel_TCPclient_mainthread.connect(address) 

     #Create handel for TCP client to connect to Labview (interrupt)
     address = ('17486633in.iask.in', 36539 )  
     handel_TCPclient_interruptthread = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
     handel_TCPclient_interruptthread.connect(address)     
     
     #Open the channel for publishing the Abnormal Energy Comsumption Alarm event of AAU
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_ECA'}
     url = 'http://localhost:9997/agent/events/AbnormalEnergyComsumptionAlarm'
     r=requests.request('POST',url,headers=hd)
     print(r.text)
     
     #subscribe to the event of oven 7 (device statusr)            
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_ECA'}
     url = 'http://localhost:9997/agent/objects/' + OID_Oven_7 + '/events/device_status'
     r=requests.request('POST',url,headers=hd)
     print(r.text)

     #start thread for publish event
     handel_timer_publishevent = threading.Timer(5,timerfun_publishevent,())  
     handel_timer_publishevent.start()

     #start main http server
     print('AAU Server is working!')
     httpd = HTTPServer(('localhost', 9995), SimpleHTTPRequestHandler)
     httpd.serve_forever()

  

