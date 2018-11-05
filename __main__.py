import random
import socket
import sys
from threading import Thread, Lock


mutex = Lock()
running = True
loss_rate = 0

server = ("0.0.0.0", 42069)
clients = []


def print_usage():
    print("python network-emulator [loss_rate]")


def io_loop():
    global running
    global loss_rate
    global clients

    while running:
        cmd = input("Command: ")
        tokens = cmd.lower().split()

        if tokens[0] == 'quit':
            with mutex:
                running = False

        if tokens[0] == 'rate':
            if len(tokens) > 1:
                if tokens[1].isdigit():
                    with mutex:
                        loss_rate = tokens[1]

        if tokens[0] == 'add':
            if len(tokens) > 1:
                with mutex:
                    if len(clients) < 2:
                        clients.append(tokens[1])


def forward_packet(s, payload, address):
    global loss_rate

    with mutex:
        if random.random() >= loss_rate:
            s.sendto(payload, address)


def process_packets():
    global running
    global loss_rate
    global clients

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(server)

    while running:
        payload, incoming_client = s.recvfrom(1)

        with mutex:
            n = len(clients)

        if n == 2:
            # if there are two clients connected, forward the packet to the other client
            try:
                with mutex:
                    index = clients.index(incoming_client)
                    if index == 0:
                        dest = clients[1]
                    else:
                        dest = clients[0]

                forward_packet(s, payload, dest)
            except ValueError:
                print("Payload from " + incoming_client + " was ignored because it was not in the client list")

        if n == 1:
            # There is 1 client in the list so save the new client and send to the first client
            clients.append(incoming_client)
            forward_packet(s, payload, clients[0])

        if n == 0:
            clients.append(incoming_client)


def main():
    global loss_rate
    argc = len(sys.argv)

    # if no loss rate was given
    if argc == 1:
        # just start with 0 loss rate
        loss_rate = 0
        network_thread = Thread(target=process_packets)
        network_thread.start()
        io_loop()
        network_thread.join()
    # if loss rate was given
    elif argc == 2:
        # check if value is a number
        if not sys.argv[1].isdigit():
            print_usage()
        else:
            # set loss rate and start thread
            loss_rate = sys.argv[1]
            network_thread = Thread(target=process_packets)
            network_thread.start()
            io_loop()
            network_thread.join()
    else:
        print_usage()
    

if __name__ == '__main__':
    main()    