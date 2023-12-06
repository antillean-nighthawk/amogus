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

    last_seq_id, messages, packet_delays = shared_functions.create_messages(data)   

    # send all data
    while len(messages) > 0:
        try:
            # send the next pending message
            udp_socket.sendto(messages[min(messages.keys())], ('localhost', 5001))
            packet_delays[min(messages.keys())]['sent'] = time.time()

            # await response
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], signed=True, byteorder='big')
            # print(ack_id, ack[SEQ_ID_SIZE:])

            # remove packet from dictionary if ack is recieved in order
            # handles packets 1 at a time, only looks at next packet in the list
            if ack_id == list(messages.keys())[1] or len(messages) == 1:
                packet_delays[min(messages.keys())]['received'] = time.time()
                messages.pop(min(messages.keys()))

        except socket.timeout:
            continue
            # print("Timeout error => resending ... ")

    shared_functions.closing_sequence(last_seq_id, udp_socket)
    end_time = time.time()
    shared_functions.get_metrics(start_time, end_time, data, packet_delays)