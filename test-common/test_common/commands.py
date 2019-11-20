# Command structure
command_table = { "Testbed.Install_0": {"command_type": "shell",
                 "endpoint": "gateway", 
                 "program": "apt-get", 
                 "app": "jumpnet-client", 
                 "package_list":"jumpnet-gateway_4.0.4.0.40078_amd64",
                 "other_arguments":"sudo apt-get update; sudo apt-get -f -y install; sudo apt-get -y --allow-downgrades install"
                 },

                "Testbed.Install_1": {"command_type": "shell", 
                 "endpoint": "client",
                 "program": "apt-get", 
                 "app": "jumpnet-gateway", 
                 "package_list":"jumpnet-client_4.0.4.0.40078_amd64",
                 "other_arguments":"sudo apt-get update; sudo apt-get -f -y install; sudo apt-get -y --allow-downgrades install"
                 },

                "Testbed.Sleep_2": { "command_type": "function",
                                "duration": "15",
                                "endpoint": "local",
                },

                "Testbed.JumpnetClient_3": {  "command_type": "shell",
                                         "endpoint": "client",
                                         "program": "jumpnet-client",
                                         "gateway": "tsdn.io",
                                         "tier": "tsdn.io",
                                         "encryption": "ON",
                                         "user": "testbed",
                                         "other_arguments":""
                   
                },

                "Testbed.Sleep_4": { "command_type": "function",
                                "duration": "10",
                                "endpoint": "local"
                },

                "Testbed.SubflowEnable_5": {  "command_type": "control_socket",
                                         "endpoint": "client",
                                         "interface_op": "Interface.Enable",
                                         "type": "Cell" 

                },

                "Testbed.Sleep_6": { "command_type": "function",
                                "duration": "10",
                                "endpoint": "local"
                },

                "Testbed.UsageStats_7": {  "command_type": "control_socket",
                                      "endpoint": "gateway",
                                      "interface_op": "Usage.StatsRequested"

                },

                "Testbed.UsageStats_8": {  "command_type": "control_socket",
                                      "endpoint": "client",
                                      "interface_op": "Usage.StatsRequested"

                },

                "Testbed.Sleep_9": { "command_type": "function",
                                "duration": "10",
                                "endpoint": "local"
                },

                "Testbed.PolicySet_10": {   "command_type": "dump_socket",
                                      "endpoint": "gateway",
                                      "interface_op": "Policy.Set",
                                      "counter": "1",
                                      "client": "WifiFirst",
                                      "gw": "WifiFirst",
                                      "policy": "RoundRobin",
                                      "version": "1"
                },

                "Testbed.Wait_11": { "command_type": "function",
                    "wait_operation": "PolicySet",
                    "max_duration": "10",
                    "endpoint": "local"
                },

                "Testbed.TrafficControl_12": { "command_type": "dump_socket",
                    "endpoint": "gateway",
                    "interface_op": "Subflow.TCSet",
                    "counter": "1",
                    "subflow": "Cell",
                    "settings": "baseline",

                   
                },

              
                "Testbed.DeviceStatus_13": {  "command_type": "control_socket",
                    "endpoint": "gateway",
                    "interface_op": "Device.HostStatusRequested"

                },

                "Testbed.DeviceStatus_14": {  "command_type": "dump_socket",
                    "endpoint": "client",
                    "interface_op": "Device.HostStatusRequested"

                },

                "Testbed.IperfClient_15": { "command_type": "shell",
                    "endpoint": "server",
                    "program": "iperf3",
                    "other_arguments": "-J -V -s -1"

                   
                },

                "Testbed.Sleep_16": { "command_type": "function",
                                "duration": "10",
                                "endpoint": "local"
                },


                "Testbed.IperfClient_17": {  "command_type": "shell",
                    "endpoint": "client",
                    "program": "iperf3",
                    "test_mode": "download",
                    "duration": "60",
                    "protocol": "tcp" ,
                    "other_arguments": "-J -V"

                   
                },

                "Testbed.Sleep_18": { "command_type": "function",
                                "duration": "75",
                                "endpoint": "local"
                },


                "Testbed.Stop_19": {  "command_type": "function",
                    "counter": "1",
                    "endpoint": "endpoints"
                },

                "Testbed.Sleep_20": { "command_type": "function",
                                "duration": "7",
                                "endpoint": "local"
                },

                "Testbed.Exit_21": { "command_type": "function",
                    "endpoint": "local"   
                }

            }

            

# registered commands
registeredClientTask = {"JumpnetClient": "test_ixendpoint.tasks.startClientd",
                        "Start": "test_ixendpoint.tasks.start",
                        "Client": "test_ixendpoint.tasks.start",
                        "SubflowEnable": "test_ixendpoint.tasks.sendAction",
                        "Stop": "test_ixendpoint.tasks.stop",
                        "S3cmd": "test_ixendpoint.tasks.start",
                        "Install": "test_ixendpoint.tasks.startApp",
                        "UsageStats": "test_ixendpoint.tasks.sendControlSocket",
                        "UsageRaw": "test_ixendpoint.tasks.sendControlSocket",
                        "DeviceStatus": "test_ixendpoint.tasks.sendControlSocket",
                        "IperfClient": "test_ixendpoint.tasks.start"
                        }

registeredServerTask = {"Start": "test_ixendpoint.tasks.startApp",
                        "Stop": "test_ixendpoint.tasks.stop",
                        "S3cmd": "test_ixendpoint.tasks.startApp",
                        "IperfServer": "test_ixendpoint.tasks.start"
                        }

registeredOrchestratorTask = {"start": "test_orchestrator.tasks.start",
                              "registerClient": "test_orchestrator.tasks.registerClient"
                              }

registeredGatewayTask = {"UsageStats": "test_ixendpoint.tasks.sendControlSocket",
                         "UsageRaw": "test_ixendpoint.tasks.sendControlSocket",
                         "Install": "test_ixendpoint.tasks.startApp",
                         "Stop": "test_ixendpoint.tasks.stop",
                         "PolicySet": "test_ixendpoint.tasks.sendControlSocket",
                         "PolicyWait": "test_ixendpoint.tasks.WaitforReplyDumpSocket",
                         "TrafficControl": "test_ixendpoint.tasks.sendControlSocket",
                         "DeviceStatus": "test_ixendpoint.tasks.sendControlSocket"

                         }


registeredTask = {'client': registeredClientTask, 'server': registeredServerTask, 'orchestrator': registeredOrchestratorTask, 'gateway': registeredGatewayTask}

command_jumpnet_client = ' '.join([
    """sudo -E /opt/trinity/{client_name} --verbosity debug""",
    """--config-merge-patch '{{"builder":{{"gateway":{{"address":"{gateway_ip}"}}}}}}'""",
    """--config-merge-patch '{{"builder":{{"device":{{"key":"{dev_key}"}}}}}}'""",
    """--config-merge-patch '{{"builder":{{"gateway":{{"discovery":{{"enable":false}}}}}}}}'""",
    """--config-merge-patch '{{"builder":{{"user":"{jumpnet_user}@jumpnet.com"}}}}'""",
    """--config-merge-patch '{{"builder":{{"password":""}}}}'""",
    """--config-merge-patch '{{"builder":{{"api_key":"{api_key}"}}}}'""",
    """--config-merge-patch '{{"routing":{{"tunnel":{{"v4":{{"routes":[{{"address":"{route_ip}","prefix":32}}]}}}}}}}}'""",
    """--config-merge-patch '{{"builder":{{"routing":{{"jdp":{{"Cell":{{"interface":"eth0"}}}}}}}}}}'""",
    """--config-merge-patch '{{"builder":{{"routing":{{"jdp":{{"Wifi":{{"interface":"eth0"}}}}}}}}}}'""",
])

command_jumpnet_client_encryption = """--config-merge-patch '{{"builder":{{"routing":{{"jdp":{{"encryption_protocol":"dtls1.2"}}}}}}}}' """


command_iperf_udp = '/usr/bin/iperf3 -J -u -b 1000m -V {download} -c {server} -t {duration} | {module} -a 1 -i {test_id} -h {host_id} -n {test_name} -c {num_clients} -t {tier}'

command_iperf_tcp = '/usr/bin/iperf3 -J -V {download} -c {server} -t {duration} | {module} -a 1 -i {test_id} -h {host_id} -n {test_name} -c {num_clients} -t {tier}'

command_addroute = 'sudo ip route add {0}/32 dev tun0'

command_s3cmd = '{0} put {1} {2}/{3}/{4}'

command_install_package_version = 'sudo apt-get update; sudo apt-get -f -y install; sudo apt-get -y --allow-downgrades install {0}={1}'

command_install_package = 'sudo apt-get update; sudo apt-get -f -y install; sudo apt-get -y --allow-downgrades install {0}/development'

command_iperf_server = '/usr/bin/iperf3 -J -V -s -1 | {module} -a 2 -i {test_id} -h {host_id} -n {test_name} -c {num_clients} -t {tier}'

command_kill_iperf = 'sudo pkill -9 iperf3'

command_clean = """sudo pkill -9 -f openvpn; sudo pkill -9 -f iperf3; sudo pkill -9 -f jumpnet-client; sudo kill -9 $(ps -A -ostat,ppid | awk '/[zZ]/ && !a[$2]++ {print $2}')"""

# gateway commands
command_stop_gateway = 'sudo service jumpnet-gateway stop'
command_start_gateway = 'sudo service jumpnet-gateway start'
command_ip_forward_gateway = 'sudo sysctl -w net.ipv4.ip_forward=1'
command_ip_table_forward = 'sudo iptables -A FORWARD -d 10.33.0.0/16 -i eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT'
command_ip_table_postrouting = 'sudo iptables -t nat -A POSTROUTING -o eth0 -s 10.33.0.0/16 -j MASQUERADE'
command_cp_default_gateway = 'sudo /trinity/config-gen'

Command_forward_all_gateway = '{0}; {1}; {2}; {3}; {4}; {5}'.format(command_stop_gateway,
                                                                    command_ip_forward_gateway,
                                                                    command_ip_table_forward,
                                                                    command_ip_table_postrouting,
                                                                    command_cp_default_gateway,
                                                                    command_start_gateway)

# client commands
command_stop_client = 'sudo service jumpnet-client stop'
command_start_client = 'sudo service jumpnet-client start'
command_ip_forward_client = 'sudo sysctl -w net.ipv4.ip_forward=0'
command_exit_jumpnet_client = 'sudo pkill -9 -f jumpnet-client'
command_clean_defunc = 'sudo kill -9 $(ps -A -ostat,ppid | awk \'/[zZ]/ && !a[$2]++ {print $2}\')'
command_kill_iperf = 'sudo pkill -9 -f iperf3'

Command_forward_all_client = '{0}; {1} '.format(command_stop_gateway,
                                                command_ip_forward_client)

Command_stop_all_client = '{0}; {1}; {2}'.format(command_exit_jumpnet_client,
                                                 command_kill_iperf,
                                                 command_clean_defunc)

Command_forward_all_client = '{0}; {1} '.format(command_stop_gateway,
                                                command_ip_forward_client)


Command_stop_all_client = '{0}; {1}; {2}'.format(command_exit_jumpnet_client,
                                                 command_kill_iperf,
                                                 command_clean_defunc)

Command_stop_all_server = '{0}; {1} '.format(command_kill_iperf,
                                             command_clean_defunc)

Command_stop_all_gateway = '{0}'.format(command_stop_gateway)

command_get_candidate_version = 'apt-cache policy {0} | grep -i candidate'

Command_stop_all_gateway = '{0}'.format(command_stop_gateway)
