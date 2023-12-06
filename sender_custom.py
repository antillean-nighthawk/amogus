import socket, time # standard libraries
import shared_functions # my own library

# TCPenis?

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

data = shared_functions.get_song_file()

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start_time = time.time()
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)
    
    # variable declaration
    cwnd = 3 
    ssthresh = 9999999 # starts as infinity
    messages, packet_delays, ack_count = {}, {}, {}
    increase = True # True = exponential increase, False = exponential decrease
    
    last_seq_id, messages, packet_delays = shared_functions.create_messages(data)
        
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
                # print(ack_id, ack[SEQ_ID_SIZE:])

                # record ack counts
                ack_count[ack_id] = ack_count.setdefault(ack_id, 0) + 1

                # remove packet from dictionary if ack is recieved in order
                # automatically takes care of dupe acks since it's already removed from dict
                if len(messages) == 1 or ack_id == list(messages.keys())[1]:
                    packet_delays[min(messages.keys())]['received'] = time.time()
                    messages.pop(min(messages.keys()))     

                # check if phases need to be switched 
                # 3 dupes (packet loss) => exp decrease
                if ack_count[ack_id] >= 3: # exp increase => exp decrease
                    ssthresh = cwnd / 2
                    increase = False
                    # immediately resend the dropped packet
                    udp_socket.sendto(messages[ack_id], ('localhost', 5001))
                elif cwnd < ssthresh: # exp decrease => exp increase
                    increase = True

                # implement congestion control according to phase
                cwnd *= 2 if increase else 0.5

            except socket.timeout:
                ssthresh = cwnd / 2
                increase = False

    shared_functions.closing_sequence(last_seq_id, udp_socket)
    end_time = time.time()
    shared_functions.get_metrics(start_time, end_time, data, packet_delays)