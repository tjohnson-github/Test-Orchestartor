# Test Orchestrator


To configure test edit the test script "test.txt" file that is in the home directory of this python script


The test script is just a list of commands that will be sent to the  different clients and endpoints
depending on the registered clients that register to test-orchestrator

**List of commands:**

**sleep**       - Sleeps for x number of seconds
                  Example: sleep 10 will sleep for 10 seconds
          
**clients**     - Number of clients in the test
                  Example: clients 10 
                  * can also be overiden in the test
              
**install**     - Installs a package
                  Example: install clientd
              
**startapp**    - Starts up an application. Originally for clientd 
                  Example: startapp clientd test.v6.tsdn.io


**command**     - Sends Commands to clientd. Originally for clientd
                  Example: command Cell Enable

**start**       - Generic start up an app. Originally made for iperf.
                  Arg1: iperf
                  Arg2: client or server
                  Example: start iperf server or start iperf client 60
              
                  * more generic way can pass anything over with the command
                  * just specify start client process
                  Example: This start
                    start client process sudo openvpn --script-security 2 --config /home/ubuntu/client.ovpn              


**s3cmd**       - Run an s3cmd for AWS copy files
                  Example: s3cmd 
              
**stop**        - Stops test

**exit**        - Exits test



# Example test script:

**sleep 2**					# will cause the application to sleep for x amount of seconds

startapp clientd		# will start clientd in all of the list of clients registered with the orchestrator

start iperf server		# will start the iperf service on all the ixendpoints registered with the orchestrator

start iperf client		# will start the iperf client on all the clients registered with the orchestrator

sleep 5

command cell up			# will send a command of 'cell up' to the clients registered with the orchestrator

sleep 10

command cell down		# will send a command of 'cell down' to the clients registered with the orchestrator

sleep 10

exit					# will send command to all clients to shutdown there apps
