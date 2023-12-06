import socket, time # standard libraries
import shared_functions # my own library

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
    cwnd = 1 # window size starts at 1
    ssthresh = 64 # starts as 64 per specification
    cur_seq_id = 0
    messages, packet_delays, ack_count = {}, {}, {}
    slow_start = True # True = slow start, False = aimd
    
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
                if cwnd >= ssthresh: # slow start => aimd
                    slow_start = False
                elif ack_count[ack_id] >= 3: # fast recovery => aimd
                    # 3 dupes (packet loss) => continue aimd
                    ssthresh = cwnd / 2 
                    cwnd = ssthresh # new cwnd set at ssthresh
                    # immediately resend the dropped packet
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

    shared_functions.closing_sequence(last_seq_id, udp_socket)
    end_time = time.time()
    shared_functions.get_metrics(start_time, end_time, data, packet_delays)