import socket
import struct
import select

PORT = 5005
MAGIC_HEADER = b'CVP1' # Cimarrón vs Pumas v1
# Packet struct: Header(4), sequence(I), x(f), y(f), hp(i), action(i), facing_left(B)
PACKET_FORMAT = '!4sIffiiB'
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

class NetworkManager:
    def __init__(self, is_host=True):
        self.is_host = is_host
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass
        self.sock.setblocking(False)
        self.sequence = 0
        
        if self.is_host:
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except OSError:
                pass
            try:
                self.sock.bind(('', PORT))
            except OSError:
                pass
            self.target_addr = None
        else:
            try:
                self.sock.bind(('', PORT + 1))
            except OSError:
                pass
            self.target_addr = ('255.255.255.255', PORT)
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except OSError:
                pass

    def discover_and_connect(self):
        # Broadcast beacon to find host/client
        if not self.is_host and self.target_addr and self.target_addr[0] == '255.255.255.255':
            try:
                self.sock.sendto(b'BEACON_CLIENT', self.target_addr)
            except (OSError, BlockingIOError):
                pass
        
        try:
            ready = select.select([self.sock], [], [], 0.01)
        except (OSError, ValueError):
            return False

        if ready[0]:
            try:
                data, addr = self.sock.recvfrom(1024)
            except (OSError, BlockingIOError):
                return False

            if self.is_host and b'BEACON_CLIENT' in data:
                self.target_addr = addr
                try:
                    self.sock.sendto(b'BEACON_HOST_ACK', addr)
                except (OSError, BlockingIOError):
                    pass
                return True
            elif not self.is_host and b'BEACON_HOST_ACK' in data:
                self.target_addr = addr
                return True
        return self.target_addr is not None and self.target_addr[0] != '255.255.255.255'

    def send_state(self, x, y, hp, action, facing_left):
        if not self.target_addr:
            return
        self.sequence += 1
        data = struct.pack(PACKET_FORMAT, MAGIC_HEADER, self.sequence, float(x), float(y), int(hp), int(action), int(bool(facing_left)))
        try:
            self.sock.sendto(data, self.target_addr)
        except (OSError, BlockingIOError):
            pass

    def receive_state(self):
        latest_data = None
        while True:
            try:
                ready = select.select([self.sock], [], [], 0.001)
            except (OSError, ValueError):
                break

            if ready[0]:
                try:
                    data, addr = self.sock.recvfrom(1024)
                except (OSError, BlockingIOError):
                    break
                if len(data) == PACKET_SIZE:
                    try:
                        unpacked = struct.unpack(PACKET_FORMAT, data)
                        if unpacked[0] == MAGIC_HEADER:
                            latest_data = unpacked
                    except struct.error:
                        pass
            else:
                break
        return latest_data # (header, seq, x, y, hp, action, facing)

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass
