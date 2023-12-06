import socket, time # standard libraries
import shared_functions # my own library

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
WINDOW_SIZE = 100

data = shared_functions.get_song_file()
 
# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start_time = time.time()
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)
    
    last_seq_id, messages, packet_delays = shared_functions.create_messages(data)

    # send first 100 msgs
    for i in list(messages.keys())[:WINDOW_SIZE]:
        udp_socket.sendto(messages[i], ('localhost', 5001))
        packet_delays[i]['sent'] = time.time()
        
    # can keep sending as long as there are messages
    while len(messages) != 0:
        try:
            # get ack and its id
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], signed=True, byteorder='big')
            # print(ack_id, ack[SEQ_ID_SIZE:])

            # remove packet from dictionary if ack is recieved in order
            if ack_id > min(messages.keys()):
                packet_delays[min(messages.keys())]['received'] = time.time()
                messages.pop(min(messages.keys()))

                # break loop after sending last message
                if len(messages) == 0:
                    break

                # shift window and send another msg upon successful ack
                udp_socket.sendto(messages[min(messages.keys())], ('localhost', 5001))
                packet_delays[min(messages.keys())]['sent'] = time.time()

        except socket.timeout:
            continue
            # print("Timeout error => resending ... ")
        
    shared_functions.closing_sequence(last_seq_id, udp_socket)
    end_time = time.time()
    shared_functions.get_metrics(start_time, end_time, data, packet_delays)