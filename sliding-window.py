import socket, time, statistics, sys

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
WINDOW_SIZE = 100

# read the song
with open('file.mp3', 'rb') as f:
    data = f.read()
 
# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start_time = time.time()
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)
    
    cur_seq_id = 0
    messages = {}
    packet_delays = {}
    
    # create all messages
    # key = seq id, value = message to send
    while cur_seq_id < sys.getsizeof(data):
        msg = int.to_bytes(cur_seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[cur_seq_id : cur_seq_id + MESSAGE_SIZE]
        messages[cur_seq_id] = msg
        packet_delays[cur_seq_id] = {'sent': 0, 'received': 0}
        cur_seq_id += MESSAGE_SIZE
        
    # can keep sending as long as there are messages
    while len(messages) != 0:
        # send 100 msgs at a time
        for i in list(messages.keys())[:100]:
            udp_socket.sendto(messages[i], ('localhost', 5001))
            packet_delays[i]['sent'] = time.time()

            try:
                # get ack and its id
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                print(ack_id, ack[SEQ_ID_SIZE:])

                # remove packet from dictionary if ack is recieved in order
                # automatically takes care of dupe acks since it's already removed from dict
                if len(messages) == 1 or ack_id == list(messages.keys())[1]:
                    packet_delays[min(messages.keys())]['received'] = time.time()
                    messages.pop(min(messages.keys()))                    

            # go to top of loop and resend new packet window if timeout
            except socket.timeout:
                continue
        
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