import argparse
import socket


def client(ip, port, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port))
            sock.sendall(bytes(message, 'utf-8'))
            response = str(sock.recv(1024), 'utf-8')
            print("Received: {}".format(response))

    # Handle server errors by outputting message to user
    except ConnectionError as e:
        print(e.strerror)


if __name__ == '__main__':
    # Define arguments (server)
    parser = argparse.ArgumentParser(
        prog='Project 1 Client',
        description='Client that connects to Project 1 Server that\'s running on the same network'
    )
    parser.add_argument('--server', default='127.0.0.1:8000')

    # Parse and validate server argument
    args = parser.parse_args()
    try:
        ip, port = args.server.split(':')
        try:
            port = int(port)
        except ValueError as e:
            raise ValueError('Invalid port: not a number') from e
        if not (1 <= int(port) <= 65535):
            raise ValueError('Invalid port number: not in valid port range')
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error as e:
        print('Invalid IP')
        exit(1)
    except ValueError as e:
        print(e)
        exit(1)

    # Start long-running process
    print('Client ready!')
    try:
        while True:
            data = input('> ')
            command = data.split(' ')[0]
            if command not in ['data', 'delete', 'add', 'report']:
                print('Invalid command')
            else:
                client(ip, port, data)
    except (KeyboardInterrupt, SystemExit):
        exit(0)
