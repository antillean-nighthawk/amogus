import socket, time, statistics, sys

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

# read the song
with open('file.mp3', 'rb') as f:
    data = f.read()
    
# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start_time = time.time()
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    cur_seq_id = 0
    packet_delays = []
    messages = {}
    dupe_acks = []

    # create all messages
    # key = seq id, value = message to send
    while cur_seq_id <= len(data):
        msg = int.to_bytes(cur_seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[cur_seq_id : cur_seq_id + MESSAGE_SIZE]
        messages[cur_seq_id] = msg
        cur_seq_id += MESSAGE_SIZE

    # can keep sending as long as there are messages
    while len(messages) != 0:
        # send the foremost packet and remove it from the messages-to-send list
        udp_socket.sendto(messages[min(messages.keys())], ('localhost', 5001))
        packet_sent_time = time.time()
        messages.pop(min(messages.keys()))

        # await response
        while len(messages) != 0:
            try:
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                # print the seq id of current ack
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], signed=True, byteorder='big')
                print("Ack receiving: ", ack_id)

                # don't need to resend same packet if duplicate ack
                if ack_id in dupe_acks:
                    break
                else:
                    dupe_acks.append(ack_id)

                # look for ack
                if ack[SEQ_ID_SIZE:] == b'ack' and (ack_id == min(messages.keys())): # 'ack' is last 3 bytes
                    # calculate packet delay
                    ack_received_time = time.time()
                    packet_delays.append(ack_received_time - packet_sent_time)          
                    break  

            except socket.timeout:
                # resend same packet if timeout
                print("Timeout error => resending ... ")
                udp_socket.sendto(messages[min(messages.keys())], ('localhost', 5001))
                packet_sent_time = time.time()

    # send final closing message
    packet_sent_time = time.time()
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    ack_received_time = time.time()
    packet_delays.append(ack_received_time - packet_sent_time)

    # calculate throughput
    end_time = time.time()
    throughput = len(data) / (end_time - start_time)
    print(f"Throughput: {throughput:.2f} bytes per second")

    # calculate avg packet delay
    avg_packet_delay = statistics.mean(packet_delays)
    print(f"Average packet delay: {avg_packet_delay:.2f} seconds")

    # calculate performance metric
    performance = throughput / avg_packet_delay
    print(f"Performance metric: {performance:.2f}")