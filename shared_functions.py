import statistics, sys

# this library is to store all repetitive functions so I can focus on developing protocols

# globals
PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

# read the song file
def get_song_file():
    with open('file.mp3', 'rb') as f:
        data = f.read()
    return data

# create all messages: key = seq id, value = message to send
def create_messages(data):
    cur_seq_id = 0
    packet_delays, messages = {}, {}

    while cur_seq_id < sys.getsizeof(data):
        msg = int.to_bytes(cur_seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[cur_seq_id : cur_seq_id + MESSAGE_SIZE]
        messages[cur_seq_id] = msg
        packet_delays[cur_seq_id] = {'sent': 0, 'received': 0}
        cur_seq_id += MESSAGE_SIZE

    return cur_seq_id, messages, packet_delays

# handle the tcp teardown sequence
def closing_sequence(cur_seq_id, udp_socket):
    # send empty msg
    msg = int.to_bytes(cur_seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + bytes('', encoding='utf-8')
    udp_socket.sendto(msg, ('localhost', 5001))

    # get ack & fin then send closing msg
    ack, _ = udp_socket.recvfrom(PACKET_SIZE)
    while ack[SEQ_ID_SIZE:] == 'ack':
        ack, _ = udp_socket.recvfrom(PACKET_SIZE)
        if ack[SEQ_ID_SIZE:] == 'fin': 
            udp_socket.sendto('==FINACK==', ('localhost', 5001))
            break

# calculate and display metrics
def get_metrics(start_time, end_time, data, packet_delays):
    # calculate throughput
    throughput = len(data) / (end_time - start_time)
    print(f"{throughput:.2f},")

    # calculate avg packet delay
    delays = []
    for k in packet_delays.keys():
        delays.append(packet_delays[k]['received'] - packet_delays[k]['sent'])
    avg_packet_delay = statistics.mean(delays)
    print(f"{avg_packet_delay:.2f},")

    # calculate performance metric
    performance = throughput / avg_packet_delay
    print(f"{performance:.2f},")