import time

from tabulate import tabulate
import pyshark
from collections import Counter
from turtledemo.penrose import start

from IxNetRestApi.IxNetRestApi import IxNetRestApiException
import  json
import os

class Step:
    def __init__(self):
        self.counter = 1.0

    def add(self):
        int_part = int(self.counter)
        if self.counter - int_part > 0 :
           self.counter = int_part
           self.counter += 1
           result = self.counter
        else:
           result = self.counter
           self.counter += 1
        retVal = f"{result:.2f}"
        return retVal

    def add_minor(self):
        self.counter += 0.01
        self.counter = round(self.counter, 2)
        retVal = f"{self.counter:.2f}"
        return retVal

def determine_cak_length(cak_string):
    # Remove '0x' prefix and spaces
    cleaned_cak = cak_string.replace("0x", "").replace(" ", "")
    # Count the number of bytes (each byte is 2 hex characters)
    byte_count = len(cleaned_cak) // 2
    # Determine if it's 128-bit or 256-bit
    if byte_count == 16:
        return "128b"
    elif byte_count == 32:
        return "256b"

    return "Unknown length"

def read_config_file(filename, vars):
    current_section = None
    print(os.getcwd())

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line:  # Ignore comments and empty lines
                continue

            # Check for section headers (lines surrounded by **)
            if line.startswith('**') and line.endswith('**'):
                current_section = line.strip('**').strip()
                vars[current_section] = {}
                continue

            # Split the line into key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Process the value
                if value.lower() == 'none':  # Convert 'None' string to None
                    value = None
                elif ',' in value:  # Convert comma-separated strings to lists
                    value = value.split(',')
                elif value.isdigit():  # Convert numeric strings to integers
                    value = int(value)
                elif value.lower() == 'true':  # Convert 'true' string to boolean True
                    value = True
                elif value.lower() == 'false':  # Convert 'false' string to boolean False
                    value = False
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

                # If current_section is None, initialize it to empty string
                if current_section is None:
                     current_section = ''
                     vars[current_section] = {}

                if current_section in vars:
                     vars[current_section][key] = value


    return True

def create_ixnetwork_session(my_vars):
    session = False
    import traceback
    from ixnetwork_restpy import SessionAssistant, ConnectionError, UnauthorizedError, NotFoundError

    try:
        session = SessionAssistant(
            IpAddress=my_vars['Global']['app_server'],
            UserName=my_vars['Global']['user'],
            Password=my_vars['Global']['password'],
            RestPort=my_vars['Global']['rest_port'],
            SessionId=my_vars['Global']['rest_session'],
            SessionName=my_vars['Global']['unique_name'],
            ClearConfig=True,
            LogLevel='info',
            LogFilename=my_vars['Global']['outlog_file']
        )
    except ConnectionError as conn_err:
        print(f"Connection error: Unable to reach the TestPlatform at {my_vars['Global']['app_server']}")
        print(f"Details: {conn_err}")
    except UnauthorizedError as auth_err:
        print("Authentication failed: Unauthorized access.")
        print(f"Details: {auth_err}")
    except NotFoundError as not_found_err:
        print(f"Session ID not found on the test platform: {my_vars['Global']['rest_session']}")
        print(f"Details: {not_found_err}")
    except ValueError as value_err:
        print(f"Unsupported IxNetwork server version. Minimum version supported is 8.42.")
        print(f"Details: {value_err}")
    except Exception as errMsg:
        # General exception handling for any other unhandled exceptions
        print("An unexpected error occurred:")
        print(traceback.format_exc())

    return session

def add_physical_ports_to_session(my_vars : dict, test_key : str):
    # Map(Location='10.36.74.26;1;1', Name='Tx')
    pmap = my_vars['Global']['port_map'] = my_vars['Global']['session'].PortMapAssistant()
    ix_net = my_vars['Global']['session'].Ixnetwork
    for _index, port in enumerate(my_vars[test_key]['man_test_ports'], start=1):
        my_slot, port_index = port.split("/")
        my_location = my_vars['Global']['test_chassis_ip'] + ";" + my_slot + ";" + port_index
        my_port_name = 'test_port_' + str(_index)
        my_vars[test_key][my_port_name] = pmap.Map(Location=my_location, Name= my_port_name)
    try:
        pmap.Connect(IgnoreLinkUp=True)
    except Exception as errMsg:  # Catch any exception
        formatted_error_msg = 'An error occurred during connection: {0}'.format(errMsg)
        raise IxNetRestApiException(formatted_error_msg)

    # Setting Ports L1 Config
    for _index, port in enumerate(my_vars[test_key]['man_test_ports'], start=1):
        my_port_name = 'test_port_' + str(_index)
        thisPort = ix_net.Vport.find(Name=my_port_name)
        portType = thisPort.Type[0].upper() + thisPort.Type[1:]
        thisPort.TxMode = 'interleaved'
        portObj = getattr(thisPort.L1Config, portType)
        if 'opt_port_media' in my_vars[test_key]:
            portObj.Media = my_vars[test_key]['opt_port_media']
        if 'opt_port_speed' in my_vars[test_key]:
            portObj.SelectedSpeeds = [my_vars[test_key]['opt_port_speed']]

def smart_converter(value):
    try:
        # Check if the value is a decimal (all digits)
        if value.isdigit():
            # Convert decimal to hexadecimal
            decimal_value = int(value)
            return hex(decimal_value)
        else:
            # Convert to decimal first to validate it's a hex input
            int(value, 16)  # This will raise ValueError if not hex
            return value  # Already hex, so return it
    except ValueError:
        return "Invalid input, provide a valid decimal or hexadecimal value."

def add_topologies_to_session(my_vars : dict, test_key : str):
    #print('Creating Topology Group 1')
    ix_net = my_vars['Global']['session'].Ixnetwork

    for _index, port in enumerate(my_vars[test_key]['man_test_ports'], start=1):
        my_name = test_key + '_Topo_' + str(_index)
        my_port_name = 'test_port_' + str(_index)
        topology = ix_net.Topology.add(Name= my_name , Ports= my_vars[test_key][my_port_name])
        if 'opt_stack_multiplier' in my_vars[test_key]:
            multiplier = my_vars[test_key]['opt_stack_multiplier']
        else:
            multiplier = 1
        dg = topology.DeviceGroup.add(Name='MacSec Grp' +  str(_index) , Multiplier= multiplier)

        ether = dg.Ethernet.add(Name='MacSec-Eth_' +  str(_index))
        ether.Mac.Increment()
        if 'opt_vlan' in  my_vars[test_key]:
            ix_net.info('Configuring vlan')
            ether.EnableVlans.Single(True)
            ether.Vlan.find()[0].VlanId.Single(my_vars[test_key]['opt_vlan'])

        if 'mka' in my_vars[test_key]['man_config_stack']:
            mka = ether.Mka.add()
            mka.CakCount = 1
            if 'opt_mka_keyServerPriority' in my_vars[test_key]:
                mka.KeyServerPriority.Single(value= my_vars[test_key]['opt_mka_keyServerPriority'])

            if 'opt_supported_cipher_suites' in my_vars[test_key]:
                _value =  ''
                if isinstance(my_vars[test_key]['opt_supported_cipher_suites'], str):
                    _value = 'selectciphers ' + my_vars[test_key]['opt_supported_cipher_suites']
                elif isinstance(my_vars[test_key]['opt_supported_cipher_suites'], list):
                    _value = 'selectciphers '.join(my_vars[test_key]['opt_supported_cipher_suites'])
                mka.SupportedCipherSuites.Single(value=_value)

            if 'opt_rekey_type' in my_vars[test_key] and 'opt_rekey_value' in my_vars[test_key]: 
                if my_vars[test_key]['opt_rekey_type'] == 'cont_time':
                    mka.update(RekeyMode = 'timerBased', RekeyBehaviour = 'rekeyContinuous' , PeriodicRekeyInterval = my_vars[test_key]['opt_rekey_value'])       
                elif my_vars[test_key]['opt_rekey_type'] == 'fix_time':
                    mka.update(RekeyMode = 'timerBased', RekeyBehaviour = 'rekeyFixedCount' , PeriodicRekeyInterval = my_vars[test_key]['opt_rekey_value'])       
                elif my_vars[test_key]['opt_rekey_type'] == 'pn_base':
                    mka.update(RekeyMode = 'pNBased')
                    _conv_value = smart_converter(my_vars[test_key]['opt_rekey_value'])
                    mka.RekeyThresholdPN.Single(value = _conv_value)
                elif my_vars[test_key]['opt_rekey_type'] == 'xpn_base':
                    mka.update(RekeyMode = 'pNBased')
                    _conv_value = smart_converter(my_vars[test_key]['opt_rekey_value'])
                    mka.RekeyThresholdXPN.Single(value = _conv_value)

            cakCache = mka.find().CakCache
            if determine_cak_length(my_vars[test_key]['opt_cak_value'])  == "128b":
                ix_net.info('Configuring 128 bit - CAK value')
                mka.KeyDerivationFunction.Single(value='aescmac128')
                cakCache.CakValue128.Increment( start_value = my_vars[test_key]['opt_cak_value'] , step_value = '00000000000000000000000000000001')
            elif determine_cak_length(my_vars[test_key]['opt_cak_value'])  == "256b":
                ix_net.info('Configuring 256 bit - CAK value')
                mka.KeyDerivationFunction.Single(value='aescmac256')
                cakCache.CakValue256.Increment( start_value = my_vars[test_key]['opt_cak_value'] , step_value = '00000000000000000000000000000001')
            cakCache.CakName.Increment(start_value = my_vars[test_key]['opt_cak_name'], step_value = '00000000000000000000000000000001')

        if 'static_l2' in my_vars[test_key]['man_config_stack']:
            s_mac = ether.StaticMacsec.add()
            s_mac.EncryptedTrafficType = "statelessL23"

            if 'opt_encrypt_vlan' in my_vars[test_key]:
              s_mac.EnableEncryptedVlans.Single(True)
              s_mac.EncryptedVlanCount = 1
              s_mac.find().InnerVlanList.find().VlanId.Single(my_vars[test_key]['opt_encrypt_vlan'])

            if 'opt_clear_text_vlan' in my_vars[test_key]:
               s_mac.EnableClearTextVlans = True

            if 'opt_incrementing_Pn_Count' in my_vars[test_key]:
               s_mac.IncrementingPn = True
               s_mac.PacketCountPn = my_vars[test_key]['opt_incrementing_Pn_Count']

            if 'opt_end_station' in my_vars[test_key]:
                s_mac.EndStation.Single(True)

            if 'opt_config_ipv4' in my_vars[test_key]:
                my_ip = my_vars[test_key]['opt_config_ipv4'].pop(0)
                s_mac.SourceIp.Increment(start_value= my_ip)

            if 'opt_config_dut_mac' in my_vars[test_key]:
                my_mac = my_vars[test_key]['opt_config_dut_mac'].pop(0)
                s_mac.DutMac.Increment(start_value=my_mac)

            if 'opt_txsak_pool' in my_vars[test_key]:
                _txSakList = process_element(my_vars[test_key]['opt_txsak_pool'])
                _len_key = len(_txSakList[0])
                _count = len(_txSakList)
                s_mac.TxSakPoolSize = _count                
                if _len_key < 33:
                    s_mac.TxSakPool.TxSak128.ValueList(values = _txSakList)
                else:
                    s_mac.TxSakPool.TxSak256.ValueList(values = _txSakList)    

            if 'opt_rxsak_pool' in my_vars[test_key]:
                _rxSakList = process_element(my_vars[test_key]['opt_rxsak_pool'])
                _len_key = len(_rxSakList[0])
                _count = len(_rxSakList)
                s_mac.RxSakPoolSize = _count                
                if _len_key < 33:
                    s_mac.RxSakPool.RxSak128.ValueList(values = _rxSakList)
                else:
                    s_mac.RxSakPool.RxSak256.ValueList(values = _rxSakList)    


        if 'static_l4' in my_vars[test_key]['man_config_stack']:
            s_mac = ether.StaticMacsec.add()
            s_mac.EncryptedTrafficType = "statefulL47"
            my_ip_name = 'StatefullIpv4_' + str(_index) 
            _my_ip = s_mac.Ipv4.add(Name=my_ip_name)
            if 'opt_config_ipv4' in my_vars[test_key]:
                my_ipv4 = my_vars[test_key]['opt_config_ipv4'].pop(0)
                _my_ip.Address.Increment(start_value= my_ipv4, step_value='0.0.0.1')
            if 'opt_config_ipv4_gw' in my_vars[test_key]:
                my_ipv4_gw = my_vars[test_key]['opt_config_ipv4_gw'].pop(0)
                _my_ip.GatewayIp.Increment(start_value=my_ipv4_gw, step_value='0.0.0.1')

            if 'opt_encrypt_vlan' in my_vars[test_key]:
              s_mac.EnableEncryptedVlans.Single(True)
              s_mac.EncryptedVlanCount = 1
              s_mac.find().InnerVlanList.find().VlanId.Single(my_vars[test_key]['opt_encrypt_vlan'])

            if 'opt_clear_text_vlan' in my_vars[test_key]:
               s_mac.EnableClearTextVlans = True

            if 'opt_incrementing_Pn_Count' in my_vars[test_key]:
               s_mac.IncrementingPn = True
               s_mac.PacketCountPn = my_vars[test_key]['opt_incrementing_Pn_Count']

            if 'opt_end_station' in my_vars[test_key]:
                s_mac.EndStation.Single(True)

            if 'opt_txsak_pool' in my_vars[test_key]:
                _txSakList = process_element(my_vars[test_key]['opt_txsak_pool'])
                _len_key = len(_txSakList[0])
                _count = len(_txSakList)
                s_mac.TxSakPoolSize = _count                
                if _len_key < 33:
                    s_mac.TxSakPool.TxSak128.ValueList(values = _txSakList)
                else:
                    s_mac.TxSakPool.TxSak256.ValueList(values = _txSakList)    

            if 'opt_rxsak_pool' in my_vars[test_key]:
                _rxSakList = process_element(my_vars[test_key]['opt_rxsak_pool'])
                _len_key = len(_rxSakList[0])
                _count = len(_rxSakList)
                s_mac.RxSakPoolSize = _count                
                if _len_key < 33:
                    s_mac.RxSakPool.RxSak128.ValueList(values = _rxSakList)
                else:
                    s_mac.RxSakPool.RxSak256.ValueList(values = _rxSakList)    

def process_element(element):
    if isinstance(element, str):
        return [element]  # Return a list with one element if it's a string
    elif isinstance(element, list):
        return element  # Return the list as is
    elif isinstance(element, dict):
        return list(element.values())  # Return a list of all dictionary values
    elif isinstance(element, int):
        return [element]  # Return a list with one element if it's a string
    else:
        return []  # Return an empty list for other types

def create_unidirectional_encrypted_traffic(my_vars : dict, test_key : str):
    ix_net = my_vars['Global']['session'].Ixnetwork
    ix_net.Traffic.Statistics.Latency.Enabled = True
    ix_net.Traffic.Statistics.Latency.update(Mode='cutThrough')
    ix_net.Globals.Statistics.Advanced.PollingSettings.update(PollInterval=1)
    my_vars[test_key]['Traffic_Items'] = list()
    if my_vars[test_key]['man_traffic_type'] == 'ipv4' or my_vars[test_key]['man_traffic_type'] == 'ethernetVlan' :
        src_mac = ix_net.Topology.find(Name= test_key + '_Topo_1').DeviceGroup.find().Ethernet.find().StaticMacsec.find()
        dst_mac = ix_net.Topology.find(Name= test_key + '_Topo_2').DeviceGroup.find().Ethernet.find().StaticMacsec.find()
        traff_item = ix_net.Traffic.TrafficItem.add(Name= test_key + '_Encr_Traff', BiDirectional=False, TrafficType=my_vars[test_key]['man_traffic_type'])
        traff_item.EndpointSet.add(Sources=src_mac, Destinations=dst_mac)
        config_elem = traff_item.ConfigElement.find()[0]
        config_elem.FramePayload.update(Type='custom', CustomPattern='CAFFEC0FFE', CustomRepeat=True)
        traff_item.Generate()
        my_vars[test_key]['Traffic_Items'].append(traff_item)
    elif my_vars[test_key]['man_traffic_type'] == 'appLib_http':
          src_ip = ix_net.Topology.find(Name= test_key + '_Topo_1').DeviceGroup.find().Ethernet.find().StaticMacsec.find().Ipv4.find()
          dst_ip = ix_net.Topology.find(Name= test_key + '_Topo_2').DeviceGroup.find().Ethernet.find().StaticMacsec.find().Ipv4.find()
          l4trafficItem = ix_net.Traffic.TrafficItem.add(Name= test_key + '_Topo_1', TrafficType='ipv4ApplicationTraffic', TrafficItemType = 'applicationLibrary')
          libFlow =  l4trafficItem.AppLibProfile.add()
          libFlow.update( ConfiguredFlows = ["Bandwidth_HTTP"], ObjectiveType = 'throughputMbps', ObjectiveValue = 100 )
          l4trafficItem.EndpointSet.add(Sources=src_ip, Destinations=dst_ip)
          l4trafficItem.Generate()
          my_vars[test_key]['Traffic_Items'].append(l4trafficItem)  
    else:
        ix_net.info('Unknown traffic type - NO TRAFFIC CREATED')

def modify_traffic(my_vars,test_key,what,value):
    ix_net = my_vars['Global']['session'].Ixnetwork
    for traff_item in my_vars[test_key]['Traffic_Items']:
        config_elem = traff_item.ConfigElement.find()[0]
        if what == 'tx_time_in_secs':
            config_elem.TransmissionControl.Type = 'fixedDuration'
            config_elem.TransmissionControl.Duration = value
        if what == 'tx_line_rate':
            config_elem.FrameRate.update(Type='percentLineRate', Rate=value)
        if what == 'fixed_pkt_size':
            config_elem.FrameSize.FixedSize = value
        if what == 'fixed_frame_count':
            config_elem.TransmissionControl.update(Type='fixedFrameCount', FrameCount=value)
        if what == 'tx_pps_rate':
            config_elem.FrameRate.update(Type='framesPerSecond', Rate=value)

        traff_item.Generate()
    #ix_net.Traffic.Apply()

def wait_for_traffic_to_stop(my_vars, send_stop_cmd = False):
    ix_net = my_vars['Global']['session'].Ixnetwork
    if send_stop_cmd: 
        ix_net.Traffic.Stop()
    time.sleep(10)
    start_time = time.time()  # Record the start time
    max_wait_time = 300  # 5 minutes in seconds
    while True:
        currentTrafficState = ix_net.Traffic.State
        ix_net.info('Currently traffic is in ' + currentTrafficState + ' state')
        if currentTrafficState == 'stopped':
            break
        if time.time() - start_time > max_wait_time:
            ix_net.info('Traffic did not stop within the 5-minute timeout.')
            break
        time.sleep(5)
    
    while True:
        _data_is_ready = ix_net.Statistics.find().View.find().Data.find()
        if _data_is_ready.IsReady:
            break
        if time.time() - start_time > max_wait_time:
            ix_net.info('Stats is not ready after 5 mins.')
            break
        time.sleep(5)

def print_results(my_vars, test_key):
    data = my_vars[test_key]['traff_results']
    print(json.dumps(data, indent=4))

# Function to create and print the table with the absolute differences
def create_table_with_diff(headers, data1, data2):
    # Convert numeric strings to integers for correct calculation
    data1_values = [int(val) if val.isdigit() else val for val in data1]
    data2_values = [int(val) if val.isdigit() else val for val in data2]
    
    # Calculate the absolute difference for numeric values
    diff_values = ['Difference'] + [abs(val1 - val2) if isinstance(val1, int) and isinstance(val2, int) else '-' 
                                    for val1, val2 in zip(data1_values[1:], data2_values[1:])]
    
    # Organize the rows
    table_data = [data1_values, data2_values, diff_values]
    
    non_zero_diff_cols = [i for i, diff in enumerate(diff_values) if diff != '-']
    filtered_headers = [headers[i] for i in non_zero_diff_cols]
    filtered_table_data = [[row[i] for i in non_zero_diff_cols] for row in table_data]


    # Print the table using tabulate
    print(tabulate(table_data, headers=headers, tablefmt="pretty"))
       
    # Print the table using tabulate
    print(tabulate(filtered_table_data, headers=filtered_headers, tablefmt="pretty"))

def calculate_jitter_and_latency():
    # Open the pcap file
    capture = pyshark.FileCapture("capfile.cap")

    previous_packet_time = None
    packet_deltas = []

    # Loop through the packets and extract timestamps
    for packet in capture:
        try:
            # Get the timestamp of the packet
            current_packet_time = float(packet.sniff_time.timestamp())

            # If this is not the first packet, calculate the delta
            if previous_packet_time:
                delta = current_packet_time - previous_packet_time
                packet_deltas.append(delta)

            # Update the previous packet time for next iteration
            previous_packet_time = current_packet_time

        except AttributeError:
            # Some packets may not have timestamp info
            continue

    # Calculate latency and jitter
    if len(packet_deltas) > 0:
        average_delta = sum(packet_deltas) / len(packet_deltas)
        jitter = sum(abs(delta - average_delta) for delta in packet_deltas) / len(packet_deltas)
        latency = average_delta

        print(f"Average Latency: {latency} seconds")
        print(f"Jitter: {jitter} seconds")
    else:
        print("No valid packet timestamps found.")

    # Close the capture file
    capture.close()

def create_table_with_diff_v2(headers, data1, data2):
    # Convert numeric strings to integers for correct calculation
    data1_values = [int(val) if val.isdigit() else val for val in data1]
    data2_values = [int(val) if val.isdigit() else val for val in data2]
    
    # Calculate the absolute differences for numeric values
    diff_values = ['Difference'] + [abs(val1 - val2) if isinstance(val1, int) and isinstance(val2, int) else '-' 
                                    for val1, val2 in zip(data1_values[1:], data2_values[1:])]
    
    # Find columns where both data1 and data2 are zeros and store them in a list
    no_data_columns = []
    non_zero_columns = []
    
    for i in range(1, len(data1_values)):
        if data1_values[i] == 0 and data2_values[i] == 0:
            no_data_columns.append(headers[i])
        else:
            non_zero_columns.append(i)
    
    # Filter headers and data based on non-zero columns
    filtered_headers = [headers[i] for i in non_zero_columns]
    filtered_table_data = [[row[i] for i in non_zero_columns] for row in [data1_values, data2_values, diff_values]]
    
    # Print the table using tabulate
    print("Table with data (non-zero columns):")
    print(tabulate(filtered_table_data, headers=filtered_headers, tablefmt="pretty"))
    
    # Print the list of columns with no data
    if no_data_columns:
        print("\nColumns with no data (all zeros):")
        print(", ".join(no_data_columns))