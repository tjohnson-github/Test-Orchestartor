# control socket stuff
server_addr = "/var/run/{0}/control.sock"
client_addr = "/var/run/{0}/client.sock"
dump_addr = "/var/run/{0}/dump.sock"


InterfaceEnable = '{{"op": "Interface.Enable","payload": {{"type": "{payload}"}}}}'
InterfaceDisable = '{{"op": "Interface.Disable","payload": {{"type": "{payload}"}}}}'
SessionInfo = '{"op": "Session.InfoRequested","payload": {} }'
InterfaceInfo = '{{"op": "Interface.InfoRequested","payload": {{"type": "{payload}"}}}}'
StatsRequest = '{{"op": "Usage.StatsRequested","payload": {{"session": [{payload}]}}}}'
StatsRawRequest = '{{"op": "Usage.RawRequested","payload": {{"session": [{payload}]}}}}'
InterfaceExit = '{"op": "Control.Exit","payload": {}}'
PolicySet = '{{"op": "Policy.Set", "session": "{session}", "payload": {{"counter" : "{counter_id}" , "client" : "{client_scheduler}", "gw" : "{gateway_scheduler}", "policy":"{policy}","version":{version}}}}}'  # noqa
TrafficControl = '{{"op": "Subflow.TCSet", "session": "{session}", "payload": {payload}}}'
DeviceStatusRequest = '{"op": "Device.HostStatusRequested","payload": {}}'


command = {
    "Interface.Enable": InterfaceEnable,
    "Interface.Disable": InterfaceDisable
}

# iperf module
ixcassModule = "test-iperf"

messageTypes = {
    "interface": InterfaceInfo,
    "session": SessionInfo,
    "UsageStats": StatsRequest,
    "UsageRaw": StatsRawRequest,
    "PolicySet": PolicySet,
    "TrafficControl": TrafficControl,
    "DeviceStatus": DeviceStatusRequest
}


# REST API Calls
RestAPI = {  
           "update":{  
              "endpoint": "/testbed/test/update/",
              "payload": { 
                 "api_key": "", 
                 "key": "",
                 "status": {  
                    "state": "",
                    "source": "",
                    "message": ""
                 }
              }
           },
           "get": {
              "endpoint": "/testbed/test/raw/",
              "payload": {
                 "api_key": "", 
                 "key": ""
              }

           }

        }
