import math

class CombatTelemetry:
    def __init__(self, buffer_size=3600):
        # 60 FPS * 60 seconds = 3600 frames
        self.buffer_size = buffer_size
        # Usamos listas nativas pre-alojadas para evitar dependencia de NumPy
        # y prevenir la saturación del Garbage Collector en RK3326
        self.rtt_buffer = [0.0] * buffer_size
        self.packet_loss_buffer = [0] * buffer_size
        self.index = 0
        self.total_packets = 0
        
    def record_packet(self, rtt, is_lost=False):
        self.rtt_buffer[self.index] = float(rtt)
        self.packet_loss_buffer[self.index] = 1 if is_lost else 0
        self.index = (self.index + 1) % self.buffer_size
        self.total_packets += 1
        
    def shannon_entropy(self):
        if self.total_packets == 0:
            return 0.0
            
        valid_len = min(self.total_packets, self.buffer_size)
        if valid_len == 0:
            return 0.0

        counts = {0: 0, 1: 0}
        for i in range(valid_len):
            val = self.packet_loss_buffer[i]
            counts[val] = counts.get(val, 0) + 1
            
        entropy = 0.0
        for val, count in counts.items():
            if count > 0:
                prob = count / valid_len
                entropy -= prob * math.log2(prob)
        return entropy
        
    def gilbert_elliott_probs(self):
        valid_len = min(self.total_packets, self.buffer_size)
        if valid_len < 2:
            return 0.0, 0.0
            
        transitions = [[0, 0], [0, 0]]
        for i in range(valid_len - 1):
            s_from = self.packet_loss_buffer[i]
            s_to = self.packet_loss_buffer[i + 1]
            transitions[s_from][s_to] += 1
            
        row0_sum = sum(transitions[0])
        row1_sum = sum(transitions[1])
        
        # P(Good -> Bad) y P(Bad -> Good)
        p = transitions[0][1] / row0_sum if row0_sum > 0 else 0.0
        r = transitions[1][0] / row1_sum if row1_sum > 0 else 0.0
        return p, r
