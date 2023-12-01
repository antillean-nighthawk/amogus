import socket, time, statistics, sys

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

# read the mp3 file
with open('file.mp3', 'rb') as f:
    data = f.read()

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start_time = time.time()
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)
    
    # variable declaration
    cwnd = 1 # window size starts at 1
    ssthresh = 64 # starts as 64 per specification
    cur_seq_id = 0
    messages, packet_delays, ack_count = {}, {}, {}
    slow_start = True # True = slow start, False = aimd
    
    # create all messages and assign a seq id to each
    while cur_seq_id < sys.getsizeof(data):
        msg = int.to_bytes(cur_seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[cur_seq_id : cur_seq_id + MESSAGE_SIZE]
        messages[cur_seq_id] = msg
        # setup packet delay dict
        packet_delays[cur_seq_id] = {'sent': 0, 'received': 0}
        cur_seq_id += MESSAGE_SIZE
        
    # loop while still unreceived acks pending
    while len(messages) != 0:
        # send msgs in cwnd
        for i in list(messages.keys())[:cwnd]:
            udp_socket.sendto(messages[i], ('localhost', 5001))
            packet_delays[i]['sent'] = time.time()

            try:    
                # get ack and its id
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                print(ack_id, ack[SEQ_ID_SIZE:])

                # record ack counts
                if ack_id not in ack_count:
                    ack_count[ack_id] = 1
                else:
                    ack_count[ack_id] += 1

                # remove packet from dictionary if ack is recieved in order
                # automatically takes care of dupe acks since it's already removed from dict
                if len(messages) == 1 or ack_id == list(messages.keys())[1]:
                    packet_delays[min(messages.keys())]['received'] = time.time()
                    messages.pop(min(messages.keys()))     

                # check if phases need to be switched 
                if cwnd >= ssthresh: # slow start => aimd
                    slow_start = False
                elif ack_count[ack_id] >= 3: # fast recovery => aimd
                    # 3 dupes (packet loss) => continue aimd
                    ssthresh = cwnd / 2 
                    cwnd = ssthresh # new cwnd set at ssthresh
                    udp_socket.sendto(messages[ack_id], ('localhost', 5001))

                # implement congestion control according to phase
                if slow_start: # slow start 
                    cwnd *= 2
                else: # aimd
                    cwnd += 1

            except socket.timeout:
                # timeout (packet loss) => slow start
                slow_start = True
                ssthresh = cwnd / 2
                cwnd = 1

    # send final closing message
    packet_delays['fin'] = {'sent': 0, 'received': 0}
    packet_delays['fin']['sent'] = time.time()
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    packet_delays['fin']['received'] = time.time()

    # calculate throughput
    end_time = time.time()
    throughput = len(data) / (end_time - start_time)
    print(f"Throughput: {throughput:.2f} bytes per second")

    # calculate avg packet delay
    delays = []
    for k in packet_delays.keys():
        delays.append(packet_delays[k]['received'] - packet_delays[k]['sent'])
    avg_packet_delay = statistics.mean(delays)
    print(f"Average packet delay: {avg_packet_delay:.2f} seconds")

    # calculate performance metric
    performance = throughput / avg_packet_delay
    print(f"Performance metric: {performance:.2f}")