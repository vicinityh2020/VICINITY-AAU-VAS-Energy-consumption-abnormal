# VICINITY-AAU-VAS-Energy-consumption-abnormal
This documentation describes the adapter of AAU VAS - Energy consumption abnormal.

# Infrastructure overview

The energy consumption data is collected through an emulated residential microgrid which includes PV, wind turbine and battery, and GORENJE smart oven and refrigerator in AAU IoT-microgrid Lab. An energy cost alarm will be triggered by Energy consumption abnormal VAS if the energy consumption exceeds desired thresholds, for instance continuously baking.
Adapter serves as the interface between VICINITY and LabVIEW enabling to use all required interaction patterns.

![Image text](https://github.com/YajuanGuan/pics/blob/master/EnergyConsumptionAbnormal.png)

# Configuration and deployment

Adapter runs on Python 3.6.

# Adapter changelog by version
Adapter releases are as aau_adapter_x.y.z.py

## 1.0.0
Start version, it works with agent-service-full-0.6.3.jar, and it subscribes to the event of GORENJE oven #7 device status and publishes an event with energy consumption abnormal notification. 

# Functionality and API
## User can read the energy consumption. 
### Endpoint:
            GET : /remote/device/{oid}/properties/{pid}
### Return:
After executing GET method, a response can be received, for instance:
properties/Load_ActivePower
{  
    "value": "5",  
    "time": "2018-11-10 11:30:29"  
}

## Publish an event to the subscribers. 
### Endpoint:
            PUT : /remote/objects/{oid}/events/{eid}
Publish the cleaning request and current time. 
### Return:
After subscribing the VAS successfully, the subscriber receives a response for instance:  
{  
    "state": "alarm",  
    "time": "2018-11-10 11:30:29"  
}
