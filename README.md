main.py - Contains 4 test cases for MacSec using IxNetwork 10.02 
testInput.txt - Contains all the information needed to create the stack and run the automation 
- opt-* are optoinal variables
- Global: used by all testcases
  myLib.py - Contain functions to that does most of the work for the test cases 

Sample OUTUPT for Test1 ( man_traffic_pkt_sizes = 64,1482 ) 
2024-11-15 18:35:11 [ixnetwork_restpy.connection tid:29480] [INFO] using python version 3.12.1 (tags/v3.12.1:2305ca5, Dec  7 2023, 22:03:25) [MSC v.1937 64 bit (AMD64)]
2024-11-15 18:35:11 [ixnetwork_restpy.connection tid:29480] [INFO] using ixnetwork-restpy version 1.4.0
2024-11-15 18:35:11 [ixnetwork_restpy.connection tid:29480] [WARNING] Verification of certificates is disabled
2024-11-15 18:35:11 [ixnetwork_restpy.connection tid:29480] [INFO] Determining the platform and rest_port using the localhost address...
2024-11-15 18:35:11 [ixnetwork_restpy.connection tid:29480] [WARNING] Unable to connect to http://localhost:11009.
2024-11-15 18:35:12 [ixnetwork_restpy.connection tid:29480] [INFO] Connection established to `https://localhost:11009 on windows`
2024-11-15 18:35:12 [ixnetwork_restpy.connection tid:29480] [WARNING] Setting the session name is not supported on the windows platform
2024-11-15 18:35:12 [ixnetwork_restpy.connection tid:29480] [INFO] Using IxNetwork api server version 10.00.2312.4
2024-11-15 18:35:12 [ixnetwork_restpy.connection tid:29480] [INFO] User info IxNetwork/5CD151GQKN/crernand
2024-11-15 18:35:19 [ixnetwork_restpy.connection tid:29480] [INFO] Step 1.00 - Init - Rest Session 1 established.
2024-11-15 18:35:20 [ixnetwork_restpy.connection tid:29480] [INFO] Step 2.00 - Init - Add Physical Ports to the session.
2024-11-15 18:35:25 [ixnetwork_restpy.connection tid:29480] [INFO] Adding test port hosts [10.80.81.2]...
2024-11-15 18:35:31 [ixnetwork_restpy.connection tid:29480] [INFO] PortMapAssistant._add_hosts duration: 5.238023519515991secs
2024-11-15 18:35:31 [ixnetwork_restpy.connection tid:29480] [INFO] Connecting virtual ports to test ports using location
2024-11-15 18:35:45 [ixnetwork_restpy.connection tid:29480] [INFO] PortMapAssistant._connect_ports duration: 14.105876922607422secs
2024-11-15 18:35:45 [ixnetwork_restpy.connection tid:29480] [WARNING] Bypassing link state check
2024-11-15 18:36:37 [ixnetwork_restpy.connection tid:29480] [INFO] Step 3.00 - Init - Verify Ports are Up before continuing.
2024-11-15 18:36:59 [ixnetwork_restpy.connection tid:29480] [INFO] Step 4.00 - Init - Create Topologies.
2024-11-15 18:37:00 [ixnetwork_restpy.connection tid:29480] [INFO] Configuring 256 bit - CAK value
2024-11-15 18:37:01 [ixnetwork_restpy.connection tid:29480] [INFO] Configuring 256 bit - CAK value
2024-11-15 18:37:34 [ixnetwork_restpy.connection tid:29480] [INFO] Step 5.00 - Test - Start Protocols and Verify MKA protocol.
2024-11-15 18:38:40 [ixnetwork_restpy.connection tid:29480] [INFO] Step 6.00 - Test - Create Encrypted Traffic.
2024-11-15 18:39:48 [ixnetwork_restpy.connection tid:29480] [INFO] Step 7.00 - Test - Modify Traffic Transmit time to 30 seconds.
2024-11-15 18:39:57 [ixnetwork_restpy.connection tid:29480] [INFO] Step 8.00 - Test - Modify Traffic Transmit Rate to 100% line rate.
2024-11-15 18:40:19 [ixnetwork_restpy.connection tid:29480] [INFO] Step 9.00 - Test - Modify Traffic Packet Size to 64 and applying traffic.
2024-11-15 18:40:32 [ixnetwork_restpy.connection tid:29480] [INFO] Step 10.01 - Test - Modify Traffic line rate to 100 % and applying traffic.
2024-11-15 18:43:01 [ixnetwork_restpy.connection tid:29480] [INFO] Step 10.02 - Test - Starting traffic and waiting to stop after 30 secs.
2024-11-15 18:43:24 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in started state
2024-11-15 18:43:29 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in started state
2024-11-15 18:43:34 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in started state
2024-11-15 18:43:39 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in stopped state
2024-11-15 18:43:45 [ixnetwork_restpy.connection tid:29480] [INFO] Step 10.03 - Test - Recording results.
2024-11-15 18:44:06 [ixnetwork_restpy.connection tid:29480] [INFO] Step 10.04 - Test - No loss detected.
2024-11-15 18:44:11 [ixnetwork_restpy.connection tid:29480] [INFO] Step 11.00 - Test - Modify Traffic Packet Size to 1482 and applying traffic.
2024-11-15 18:44:30 [ixnetwork_restpy.connection tid:29480] [INFO] Step 11.01 - Test - Modify Traffic line rate to 100 % and applying traffic.
2024-11-15 18:46:49 [ixnetwork_restpy.connection tid:29480] [INFO] Step 11.02 - Test - Starting traffic and waiting to stop after 30 secs.
2024-11-15 18:47:09 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in started state
2024-11-15 18:47:14 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in started state
2024-11-15 18:47:19 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in started state
2024-11-15 18:47:24 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in stoppedWaitingForStats state
2024-11-15 18:47:29 [ixnetwork_restpy.connection tid:29480] [INFO] Currently traffic is in stopped state
2024-11-15 18:47:51 [ixnetwork_restpy.connection tid:29480] [INFO] Step 11.03 - Test - Recording results.
2024-11-15 18:47:52 [ixnetwork_restpy.connection tid:29480] [INFO] Step 11.04 - Test - No loss detected.
2024-11-15 18:47:52 [ixnetwork_restpy.connection tid:29480] [INFO] Step 12.00 - Test - Printing out the results.
2024-11-15 18:47:52 [ixnetwork_restpy.connection tid:29480] [INFO] Step 12.00 - Clean up 
2024-11-15 18:47:52 [ixnetwork_restpy.connection tid:29480] [INFO] Step 13.01 - Stopping Protocols 
2024-11-15 18:47:52 [ixnetwork_restpy.connection tid:29480] [INFO] Step 13.02 - Cleaning up session and leaving it up...bye
2024-11-15 18:48:00 [ixnetwork_restpy.connection tid:29480] [INFO] The End
{
    "64": {
        "1": {
            "Frames Delta": "0",
            "Tx Frames": "44642857",
            "Rx Frames": "44642857",
            "Rate": 100
        }
    },
    "1482": {
        "1": {
            "Frames Delta": "0",
            "Tx Frames": "2496671",
            "Rx Frames": "2496671",
            "Rate": 100
        }
    }
}
