import sys
import time
import inspect
import re
from mylib import *
from ixnetwork_restpy import StatViewAssistant

def my_test_case_1():
    my_vars = dict()
    step = Step()
    test_key = 'Test_X'
    current_function_name = inspect.currentframe().f_code.co_name
    match = re.search(r'(\d+)$', current_function_name)
    if match:
        test_key = f"Test_{match.group(1)}"

    file_path = os.path.join(os.path.dirname(__file__), 'testInput.txt')
    
    if not read_config_file(file_path, my_vars):
        print("Error Reading Input Vars")
        sys.exit()
    for key, value in my_vars.items():
        print(f"Key: {key} -- Value: {value}")

    my_vars['Global']['outlog_file']  = test_key + time.strftime("%Y%m%d-%H%M%S") + '.log'
    my_vars['Global']['unique_name'] = test_key + my_vars['Global']['user'] + time.strftime("%Y%m%d-%H%M")
    my_vars['Global']['session']  = create_ixnetwork_session(my_vars)
    ix_net = my_vars['ix_net_session'] = my_vars['Global']['session'].Ixnetwork
    ix_net.info(f"Step {step.add()} - Init - Rest Session {my_vars['Global']['session'].Session.Id} established.")

    ix_net.info(f"Step {step.add()} - Init - Add Physical Ports to the session.")
    add_physical_ports_to_session(my_vars, test_key)

    ix_net.info(f"Step {step.add()} - Init - Verify Ports are Up before continuing.")
    portStats = StatViewAssistant(ix_net, 'Port Statistics')
    portStats.CheckCondition('Link State', StatViewAssistant.REGEX, 'Link\s+Up')

    ix_net.info(f"Step {step.add()} - Init - Create Topologies.")
    add_topologies_to_session(my_vars,test_key)

    ix_net.info(f"Step {step.add()} - Test - Start Protocols and Verify MKA protocol.")
    ix_net.StartAllProtocols(Arg1='sync')
    protocolsSummary = StatViewAssistant(ix_net, 'Protocols Summary')
    protocolsSummary.AddRowFilter('Protocol Type', StatViewAssistant.REGEX, 'MKA')
    protocolsSummary.CheckCondition('Sessions Down', StatViewAssistant.EQUAL, '0')
    protocolsSummary.CheckCondition('Sessions Not Started', StatViewAssistant.EQUAL, '0')

    ix_net.info(f"Step {step.add()} - Test - Create Encrypted Traffic.")
    create_unidirectional_encrypted_traffic(my_vars, test_key)

    ix_net.info(f"Step {step.add()} - Test - Modify Traffic Transmit time to 30 seconds.")
    modify_traffic(my_vars,test_key,what = 'tx_time_in_secs', value = 30)

    ix_net.info(f"Step {step.add()} - Test - Modify Traffic Transmit Rate to 100% line rate.")
    modify_traffic(my_vars,test_key,what = 'tx_line_rate', value = 100)

    #ix_net.info(f"Step {step.add()} - Test - Enable Capturing on the Test Port 2 .")
    #vport = my_vars[test_key]['test_port_2']
    #vport.RxMode = 'captureAndMeasure'
    #vport.Capture.HardwareEnabled = True

    my_vars[test_key]['traff_results'] = dict()
    for pkt_size in my_vars[test_key]['man_traffic_pkt_sizes']:
        ix_net.info(f"Step {step.add()} - Test - Modify Traffic Packet Size to {pkt_size} and applying traffic.")
        modify_traffic(my_vars, test_key, 'fixed_pkt_size', pkt_size)
        _run_index = 1
        my_vars[test_key]['traff_results'][pkt_size] = dict()
        # Start at 100% rate
        rate = 100
        step_down = 10
        step_up = 5
        _last_run = False
        while True:
            ix_net.info(f"Step {step.add_minor()} - Test - Modify Traffic line rate to {rate} % and applying traffic.")
            modify_traffic(my_vars, test_key, what='tx_line_rate', value=rate)
            try:
                ix_net.Traffic.Apply()
            except:
                time.sleep(240)

            ix_net.info(f"Step {step.add_minor()} - Test - Starting traffic and waiting to stop after 30 secs.")
            ix_net.Traffic.Start()
            time.sleep(5)
            #ix_net.StartCapture()
            wait_for_traffic_to_stop(my_vars)

            #remotePath = ix_net.Globals.PersistencePath
            #captured_file_locations = ix_net.SaveCaptureFiles(remotePath, 'saveFileCap')

            ix_net.info(f"Step {step.add_minor()} - Test - Recording results.")
            my_vars[test_key]['traff_results'][pkt_size][_run_index] = dict()
            traffItemStatistics = StatViewAssistant(ix_net, 'Traffic Item Statistics')
            flowStat = traffItemStatistics.Rows[0]  # Assuming single flow, adjust if multiple flows exist

            # Extract relevant statistics
            my_vars[test_key]['traff_results'][pkt_size][_run_index]['Frames Delta'] = flowStat['Frames Delta']
            my_vars[test_key]['traff_results'][pkt_size][_run_index]['Tx Frames'] = flowStat['Tx Frames']
            my_vars[test_key]['traff_results'][pkt_size][_run_index]['Rx Frames'] = flowStat['Rx Frames']

            if 'Cut-Through Avg Latency (ns)' in flowStat:
                my_vars[test_key]['traff_results'][pkt_size][_run_index]['Cut-Through Avg Latency (ns)'] = flowStat[
                    'Cut-Through Avg Latency (ns)']

            my_vars[test_key]['traff_results'][pkt_size][_run_index]['Rate'] = rate

            if _last_run:
                ix_net.info(f"Step {step.add_minor()} - Test - Last run done.")
                break

            # Check for packet loss (Frames Delta > 2)
            if int(flowStat['Frames Delta']) > 2:
                rate -= step_down
                ix_net.info(f"Step {step.add_minor()} - Test - Some pkt loss detected - Lowering rate to {rate}.")
            elif int(flowStat['Frames Delta']) == 0 and rate == 100:
                ix_net.info(f"Step {step.add_minor()} - Test - No loss detected.")
                break
            else:
                rate += step_up
                ix_net.info(f"Step {step.add_minor()} - Test - No loss detected. Starting last run - Setting rate to {rate}.")
                _last_run = True
            _run_index += 1

    ix_net.info(f"Step {step.add()} - Test - Printing out the results.")
    print_results(my_vars, test_key)

    if 'opt_dont_cleanup' in my_vars[test_key]:
        if my_vars[test_key]['opt_dont_cleanup']:
            ix_net('Leaving Config Up and running')
            sys.exit()

    ix_net.info(f"Step {step.add()} - Clean up ")
    ix_net.info(f"Step {step.add_minor()} - Stopping Protocols ")
    ix_net.StopAllProtocols()

    if my_vars['Global']['rest_session'] == None:
        ix_net.info(f"Step {step.add_minor()} - Removing Session we created...bye")
        my_vars['Global']['session'].Session.remove()
    else:
        ix_net.info(f"Step {step.add_minor()} - Cleaning up session and leaving it up...bye")
        ix_net.NewConfig()

    ix_net.info("The End")

def my_test_case_2():
    my_vars = dict()
    step = Step()
    test_key = 'Test_X'
    current_function_name = inspect.currentframe().f_code.co_name
    match = re.search(r'(\d+)$', current_function_name)
    if match:
        test_key = f"Test_{match.group(1)}"

    file_path = os.path.join(os.path.dirname(__file__), 'testInput.txt')
    
    if not read_config_file(file_path, my_vars):
        print("Error Reading Input Vars")
        sys.exit()
    for key, value in my_vars.items():
        print(f"Key: {key} -- Value: {value}")

    my_vars['Global']['outlog_file']  = test_key + time.strftime("%Y%m%d-%H%M%S") + '.log'
    my_vars['Global']['unique_name'] = test_key + my_vars['Global']['user'] + time.strftime("%Y%m%d-%H%M")
    my_vars['Global']['session']  = create_ixnetwork_session(my_vars)
    ix_net = my_vars['ix_net_session'] = my_vars['Global']['session'].Ixnetwork
    ix_net.info(f"Step {step.add()} - Init - Rest Session {my_vars['Global']['session'].Session.Id} established.")

    ix_net.info(f"Step {step.add()} - Init - Add Physical Ports to the session.")
    add_physical_ports_to_session(my_vars, test_key)

    ix_net.info(f"Step {step.add()} - Init - Verify Ports are Up before continuing.")
    portStats = StatViewAssistant(ix_net, 'Port Statistics')
    portStats.CheckCondition('Link State', StatViewAssistant.REGEX, 'Link\s+Up')

    ix_net.info(f"Step {step.add()} - Init - Create Topologies.")
    add_topologies_to_session(my_vars,test_key)

    ix_net.info(f"Step {step.add()} - Test - Start Protocols and Verify Static MACsec protocol.")
    ix_net.StartAllProtocols(Arg1='sync')
    protocolsSummary = StatViewAssistant(ix_net, 'Protocols Summary')
    protocolsSummary.AddRowFilter('Protocol Type', StatViewAssistant.REGEX, 'Static MACsec')
    protocolsSummary.CheckCondition('Sessions Down', StatViewAssistant.EQUAL, '0')
    protocolsSummary.CheckCondition('Sessions Not Started', StatViewAssistant.EQUAL, '0')

    ix_net.info(f"Step {step.add()} - Test - Create Encrypted Traffic.")
    create_unidirectional_encrypted_traffic(my_vars, test_key)

    _pkt_size = process_element(my_vars[test_key]['man_traffic_pkt_sizes'])[0]
    ix_net.info(f"Step {step.add()} - Test - Modify Traffic set pkt size to {_pkt_size}.")
    modify_traffic(my_vars, test_key, 'fixed_pkt_size', _pkt_size)

    ix_net.info(f"Step {step.add()} - Test - Modify Traffic Transmit Rate to 10% line rate.")
    modify_traffic(my_vars,test_key,what = 'tx_line_rate', value = 10)

    _num_pkts = 5000
    if 'opt_num_pkts_to_send' in my_vars[test_key]:
        _num_pkts = int(my_vars[test_key]['opt_num_pkts_to_send'])
    ix_net.info(f"Step {step.add()} - Test - Modify Traffic Num of pkts to transmit - setting to {_num_pkts}.")
    modify_traffic(my_vars,test_key,what = 'fixed_frame_count', value = _num_pkts)
    try:
        ix_net.Traffic.Apply()
    except:
        time.sleep(240)

    ix_net.info(f"Step {step.add_minor()} - Test - Starting traffic and waiting to stop.")
    ix_net.Traffic.Start()
    time.sleep(5)
    #ix_net.StartCapture()
    wait_for_traffic_to_stop(my_vars)

    ix_net.info(f"Step {step.add()} - Test - Recording results.")
    my_vars[test_key]['traff_results'] = dict()
    traffItemStatistics = StatViewAssistant(ix_net, 'Traffic Item Statistics')
    flowStat = traffItemStatistics.Rows[0]  # Assuming single flow, adjust if multiple flows exist
    
    test_result = 'PASS'
    
    my_vars[test_key]['traff_results']['Frames Delta'] = flowStat['Frames Delta']
    my_vars[test_key]['traff_results']['Tx Frames'] = flowStat['Tx Frames']
    my_vars[test_key]['traff_results']['Rx Frames'] = flowStat['Rx Frames']

    ix_net.info(f"Step {step.add_minor()} - Verify results.")
    if int(flowStat['Rx Frames']) < 1: 
         test_result = 'FAIL'
         ix_net.info(f"Verify results - RX Frames {flowStat['Rx Frames']} should be greater than ZERO")
        
    if int(flowStat['Frames Delta']) > 2: 
         test_result = 'FAIL'
         ix_net.info(f"Verify results - TX - RX frames shuold be at most 2 but it found  {flowStat['Frames Delta']}")


    macsec_stats = StatViewAssistant(ix_net, 'Static MACsec Per Port')
    macsec_stats.AddRowFilter('Port', macsec_stats.REGEX, 'test_port_2')
    macsec_data = macsec_stats.Rows[0]
    _check_data = ['Invalid ICV Rx', 'Bad Tag/ICV Discarded', 'Out of Window Discarded', 'Unknown SCI Discarded', 'Invalid ICV Discarded', 'Invalid ICV Rx']
    for label in _check_data:
        if int(macsec_data[label]) == 0:
             ix_net.info(f"Verify results - {label} equals ZERO")
        elif int(macsec_data[label]) > 0:
                test_result = 'FAIL'
                ix_net.info(f"Verify results - {label} should be ZERO but got {macsec_data[label]}") 


    print_results(my_vars, test_key)

    print(f"*** TEST 2 {test_result} ***")

    if 'opt_dont_cleanup' in my_vars[test_key]:
        if my_vars[test_key]['opt_dont_cleanup']:
            ix_net('Leaving Config Up and running')
            sys.exit()

    ix_net.info(f"Step {step.add()} - Clean up ")
    ix_net.info(f"Step {step.add_minor()} - Stopping Protocols ")
    ix_net.StopAllProtocols()

    if my_vars['Global']['rest_session'] == None:
        ix_net.info(f"Step {step.add_minor()} - Removing Session we created...bye")
        my_vars['Global']['session'].Session.remove()
    else:
        ix_net.info(f"Step {step.add_minor()} - Cleaning up session and leaving it up...bye")
        ix_net.NewConfig()

    ix_net.info("The End")

def my_test_case_3():
    my_vars = dict()
    step = Step()
    test_key = 'Test_X'
    current_function_name = inspect.currentframe().f_code.co_name
    match = re.search(r'(\d+)$', current_function_name)
    if match:
        test_key = f"Test_{match.group(1)}"

    file_path = os.path.join(os.path.dirname(__file__), 'testInput.txt')
    
    if not read_config_file(file_path, my_vars):
        print("Error Reading Input Vars")
        sys.exit()
    for key, value in my_vars.items():
        print(f"Key: {key} -- Value: {value}")

    my_vars['Global']['outlog_file']  = test_key + time.strftime("%Y%m%d-%H%M%S") + '.log'
    my_vars['Global']['unique_name'] = test_key + my_vars['Global']['user'] + time.strftime("%Y%m%d-%H%M")
    my_vars['Global']['session']  = create_ixnetwork_session(my_vars)
    ix_net = my_vars['ix_net_session'] = my_vars['Global']['session'].Ixnetwork
    ix_net.info(f"Step {step.add()} - Init - Rest Session {my_vars['Global']['session'].Session.Id} established.")

    ix_net.info(f"Step {step.add()} - Init - Add Physical Ports to the session.")
    add_physical_ports_to_session(my_vars, test_key)

    ix_net.info(f"Step {step.add()} - Init - Verify Ports are Up before continuing.")
    portStats = StatViewAssistant(ix_net, 'Port Statistics')
    portStats.CheckCondition('Link State', StatViewAssistant.REGEX, 'Link\s+Up')

    ix_net.info(f"Step {step.add()} - Init - Create Topologies.")
    add_topologies_to_session(my_vars,test_key)

    ix_net.info(f"Step {step.add()} - Test - Start Protocols and Verify MKA protocol.")
    ix_net.StartAllProtocols(Arg1='sync')

    protocolsSummary = StatViewAssistant(ix_net, 'Protocols Summary')
    protocolsSummary.AddRowFilter('Protocol Type', StatViewAssistant.REGEX, 'MKA')
    protocolsSummary.CheckCondition('Sessions Down', StatViewAssistant.EQUAL, '0')
    protocolsSummary.CheckCondition('Sessions Not Started', StatViewAssistant.EQUAL, '0')

    ix_net.info(f"Step {step.add()} - Test - Create Encrypted Traffic.")
    create_unidirectional_encrypted_traffic(my_vars, test_key)

    ix_net.info(f"Step {step.add()} - Test - Modify Traffic Transmit Rate to 100% line rate.")
    modify_traffic(my_vars,test_key,what = 'tx_line_rate', value = 100)

    _pkt_size = process_element(my_vars[test_key]['man_traffic_pkt_sizes'])[0]
    ix_net.info(f"Step {step.add()} - Test - Modify Traffic set pkt size to {_pkt_size}.")
    modify_traffic(my_vars, test_key, 'fixed_pkt_size', _pkt_size)
    try:
        ix_net.Traffic.Apply()
    except:
        time.sleep(240)

    ix_net.info(f"Step {step.add()} - Test - Start traffic.")
    ix_net.Traffic.Start()
    time.sleep(5)

    ix_net.info(f"Step {step.add()} - Test - Collect SAK and AN about 5 times.")
    my_vars['test_resuts'] = dict()
    my_vars['test_resuts']['keys_used'] = list()
    for value in range(1, 6):
        _sak =  ix_net.Topology.find().DeviceGroup.find(Name='MacSec Grp1').Ethernet.find().Mka.find().Sak
        _an =  ix_net.Topology.find().DeviceGroup.find(Name='MacSec Grp1').Ethernet.find().Mka.find().AssociationNumber
        key_in_use = _sak[0] + ':' + _an[0]
        my_vars['test_resuts']['keys_used'].append(key_in_use)  
        # This can be improved and it might not get re-keying....
        time.sleep(60)

    ix_net.info(f"Step {step.add()} - Verify  - Re-Keying is happening...")
    num_unique_keys_used  = len(set(my_vars['test_resuts']['keys_used']))
    if num_unique_keys_used > 2: 
        ix_net.info(f"Step {step.add_minor()} - PASS - Re-Key occured at least {num_unique_keys_used} times in 5 minutes.")
    else:
        ix_net.info(f"Step {step.add_minor()} - FAILED - Re-Key DID no occured -- Expected more than 2 times and got {num_unique_keys_used} times.")

    
    wait_for_traffic_to_stop(my_vars, True)

    my_vars[test_key]['traff_results'] = dict()
    traffItemStatistics = StatViewAssistant(ix_net, 'Traffic Item Statistics')
    flowStat = traffItemStatistics.Rows[0]  # Assuming single flow, adjust if multiple flows exist
    
    test_result = 'PASS'
    
    my_vars[test_key]['traff_results']['Frames Delta'] = flowStat['Frames Delta']
    my_vars[test_key]['traff_results']['Tx Frames'] = flowStat['Tx Frames']
    my_vars[test_key]['traff_results']['Rx Frames'] = flowStat['Rx Frames']

    ix_net.info(f"Step {step.add()} - Verify results.")
    if int(flowStat['Rx Frames']) < 1: 
         test_result = 'FAIL'
         ix_net.info(f"Verify results - RX Frames {flowStat['Rx Frames']} should be greater than ZERO")
        
    if int(flowStat['Frames Delta']) > 2: 
         test_result = 'FAIL'
         ix_net.info(f"Verify results - TX - RX frames shuold be at most 2 but it found  {flowStat['Frames Delta']}")

    print_results(my_vars, test_key)

    print(f"*** TEST 3 {test_result} ***")

    if 'opt_dont_cleanup' in my_vars[test_key]:
        if my_vars[test_key]['opt_dont_cleanup']:
            ix_net('Leaving Config Up and running')
            sys.exit()

    ix_net.info(f"Step {step.add()} - Clean up ")
    ix_net.info(f"Step {step.add_minor()} - Stopping Protocols ")
    ix_net.StopAllProtocols()

    if my_vars['Global']['rest_session'] == None:
        ix_net.info(f"Step {step.add_minor()} - Removing Session we created...bye")
        my_vars['Global']['session'].Session.remove()
    else:
        ix_net.info(f"Step {step.add_minor()} - Cleaning up session and leaving it up...bye")
        ix_net.NewConfig()

    ix_net.info("The End")

def my_test_case_4():
    my_vars = dict()
    step = Step()
    test_key = 'Test_X'
    current_function_name = inspect.currentframe().f_code.co_name
    match = re.search(r'(\d+)$', current_function_name)
    if match:
        test_key = f"Test_{match.group(1)}"
    
    file_path = os.path.join(os.path.dirname(__file__), 'testInput.txt')
    
    if not read_config_file(file_path, my_vars):
        print("Error Reading Input Vars")
        sys.exit()
    for key, value in my_vars.items():
        print(f"Key: {key} -- Value: {value}")

    my_vars['Global']['outlog_file']  = test_key + time.strftime("%Y%m%d-%H%M%S") + '.log'
    my_vars['Global']['unique_name'] = test_key + my_vars['Global']['user'] + time.strftime("%Y%m%d-%H%M")
    my_vars['Global']['session']  = create_ixnetwork_session(my_vars)
    ix_net = my_vars['ix_net_session'] = my_vars['Global']['session'].Ixnetwork
    ix_net.info(f"Step {step.add()} - Init - Rest Session {my_vars['Global']['session'].Session.Id} established.")

    ix_net.info(f"Step {step.add()} - Init - Add Physical Ports to the session.")
    add_physical_ports_to_session(my_vars, test_key)

    ix_net.info(f"Step {step.add()} - Init - Verify Ports are Up before continuing.")
    portStats = StatViewAssistant(ix_net, 'Port Statistics')
    portStats.CheckCondition('Link State', StatViewAssistant.REGEX, 'Link\s+Up')

    ix_net.info(f"Step {step.add()} - Init - Create Topologies.")
    add_topologies_to_session(my_vars,test_key)

    ix_net.info(f"Step {step.add()} - Test - Start Protocols and Verify MKA protocol.")
    ix_net.StartAllProtocols(Arg1='sync')

    protocolsSummary = StatViewAssistant(ix_net, 'Protocols Summary')
    protocolsSummary.AddRowFilter('Protocol Type', StatViewAssistant.REGEX, 'MKA')
    protocolsSummary.CheckCondition('Sessions Down', StatViewAssistant.EQUAL, '0')
    protocolsSummary.CheckCondition('Sessions Not Started', StatViewAssistant.EQUAL, '0')
    if 'opt_stack_multiplier' in my_vars[test_key]:
        expected_num_sessions = int(my_vars[test_key]['opt_stack_multiplier'] * 2)
        protocolsSummary.CheckCondition('Sessions Up', StatViewAssistant.EQUAL, expected_num_sessions)

    ix_net.info(f"Step {step.add()} - Test - Create Encrypted Traffic.")
    create_unidirectional_encrypted_traffic(my_vars, test_key)

    ix_net.info(f"Step {step.add()} - Test - Apply  L4 Traffic.")
    ix_net.Traffic.ApplyStatefulTraffic()

    ix_net.info(f"Step {step.add()} - Test - Start traffic.")
    ix_net.Traffic.StartStatefulTraffic()
    time.sleep(10)
    ix_net.info(f"Step {step.add()} - Test - Clear Ports and Traffic stats and wait 3 minutes.")
    ix_net.ClearPortsAndTrafficStats()
    time.sleep(180)
    ix_net.info(f"Step {step.add()} - Test - Stopping traffic and checking stats.")
    ix_net.Traffic.StopStatefulTraffic()

    my_vars[test_key]['traff_results'] = dict()
    traffItemStatistics = StatViewAssistant(ix_net, 'Static MACsec Per Port')
    flowStat = traffItemStatistics.Rows[0]  # Assuming single flow, adjust if multiple flows exist
    
    #create_table_with_diff(flowStat.Columns, flowStat.RawData[0],flowStat.RawData[1])
    create_table_with_diff_v2(flowStat.Columns, flowStat.RawData[0],flowStat.RawData[1])

    test_result = 'Complete'
    
    print(f"*** TEST 4 {test_result} ***")

    if 'opt_dont_cleanup' in my_vars[test_key]:
        if my_vars[test_key]['opt_dont_cleanup']:
            ix_net('Leaving Config Up and running')
            sys.exit()

    ix_net.info(f"Step {step.add()} - Clean up ")
    ix_net.info(f"Step {step.add_minor()} - Stopping Protocols ")
    ix_net.StopAllProtocols()

    if my_vars['Global']['rest_session'] == None:
        ix_net.info(f"Step {step.add_minor()} - Removing Session we created...bye")
        my_vars['Global']['session'].Session.remove()
    else:
        ix_net.info(f"Step {step.add_minor()} - Cleaning up session and leaving it up...bye")
        ix_net.NewConfig()

    ix_net.info("The End")
    

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    my_test_case_1()
    my_test_case_2()
    my_test_case_3()
    my_test_case_4()
    #calculate_jitter_and_latency()
    

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

'''
The test or script was validated againts a Cisco Switch and here are the relevant configs 
!   Ixia Port 1 ----------- TwoGigabitEthernet1/0/11
!   Ixia Port 2 ----------- TwoGigabitEthernet1/0/12
!
!useful commands
!#show mka session interface <INTERFACE> detail
!#show macsec summary
!#show macsec interface <INTERFACE>
!
key chain cf-mka-key macsec
 key F123456789ABCDEF
   cryptographic-algorithm aes-256-cmac
  key-string f123456789abcdef0123456789abcdeff123456789abcdef0123456789abcdef
!
!
mka policy cf-policy
 macsec-cipher-suite gcm-aes-xpn-256
!
!
interface TwoGigabitEthernet1/0/11
 switchport mode trunk
 macsec replay-protection window-size 4294967295
 macsec network-link
 mka policy cf-policy
 mka pre-shared-key key-chain cf-mka-key
!
interface TwoGigabitEthernet1/0/12
 switchport mode trunk
 macsec replay-protection window-size 4294967295
 macsec network-link
 mka policy cf-policy
 mka pre-shared-key key-chain cf-mka-key
!

!
end


'''
