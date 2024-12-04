import simpy
import random
import matplotlib.pyplot as plt

# Constants
SIM_TIME = 0.40 * 60 * 60  # 6 hours in seconds
QUEUE_MAX_SIZE = 40
SERVICE_TIME = 0.253  # Time to process each packet at a switch
NETWORK_LATENCY = 0.2  # Latency to simulate packet travel time

# Metrics
queue_lengths = {1: [], 2: []}
queue_times = {1: [], 2: []}
packet_drops = {1: 0, 2: 0}

# Switch class
class Switch:
    def __init__(self, env, id):
        self.env = env
        self.id = id
        self.queue = simpy.Store(env, capacity=QUEUE_MAX_SIZE)
        self.queue_size = 0

    def enqueue(self, packet, secondary_switch=None):
        if self.queue_size < QUEUE_MAX_SIZE:
            self.queue.put(packet)
            self.queue_size += 1
        elif secondary_switch and secondary_switch.queue_size < QUEUE_MAX_SIZE:
            secondary_switch.enqueue(packet)
        else:
            # Drop the packet if both queues are full
            packet_drops[self.id] += 1

    def dequeue(self):
        while True:
            if self.queue_size > 0:
                packet = yield self.queue.get()
                self.queue_size -= 1
                queue_times[self.id].append(self.env.now - packet['time'])
                yield self.env.timeout(SERVICE_TIME)  # Fixed service time per packet
            else:
                yield self.env.timeout(0.1)  # Idle wait

# Packet generator with random intervals for each PC
def packet_generator(env, pc_id, primary_switch, secondary_switch=None):
    while True:
        # Random packet generation interval for each PC
        interval = random.uniform(0.1, 0.5)  # Randomized interval for each packet
        yield env.timeout(interval)
        # Add network latency
        yield env.timeout(NETWORK_LATENCY)
        packet = {'time': env.now, 'source': pc_id}
        primary_switch.enqueue(packet, secondary_switch)

# Queue length logger
def log_queue_length(env):
    while True:
        for i in queue_lengths:
            queue_lengths[i].append({'time': env.now, 'length': switches[i].queue_size})
        yield env.timeout(10)  # Log every 10 seconds

# Simulation setup
env = simpy.Environment()
switches = {
    1: Switch(env, 1),
    2: Switch(env, 2)
}

# Start switches processing packets
for sw in switches.values():
    env.process(sw.dequeue())

# Connect PCs to switches with random packet generation rates
env.process(packet_generator(env, 'PC1', switches[1], switches[2]))
env.process(packet_generator(env, 'PC2', switches[1], switches[2]))
env.process(packet_generator(env, 'PC3', switches[1], switches[2]))
env.process(packet_generator(env, 'PC4', switches[2], switches[1]))

# Start logging queue lengths
env.process(log_queue_length(env))

# Run simulation
env.run(until=SIM_TIME)

# Extract data for plotting
times = [entry['time'] for entry in queue_lengths[1]]
queue1_lengths = [entry['length'] for entry in queue_lengths[1]]
queue2_lengths = [entry['length'] for entry in queue_lengths[2]]

# Plot 1: Queue Length Over Time
plt.figure(figsize=(10, 6))
plt.plot(times, queue1_lengths, label='Queue Length SW1', color='blue')
plt.plot(times, queue2_lengths, label='Queue Length SW2', color='orange')
plt.xlabel('Time (s)')
plt.ylabel('Queue Length')
plt.title('Queue Length Over Time')
plt.legend()
plt.grid(True)
plt.savefig("queue_length_over_time.png")
plt.show()

# Plot 2: Average Queue Wait Time
average_wait_time1 = sum(queue_times[1]) / len(queue_times[1]) if queue_times[1] else 0
average_wait_time2 = sum(queue_times[2]) / len(queue_times[2]) if queue_times[2] else 0

plt.figure(figsize=(10, 6))
plt.bar(['SW1', 'SW2'], [average_wait_time1, average_wait_time2], color=['blue', 'orange'])
plt.xlabel('Switch')
plt.ylabel('Average Wait Time (s)')
plt.title('Average Queue Wait Time')
plt.grid(axis='y')
plt.savefig("average_wait_time.png")
plt.show()

# Plot 3: Packet Drops
plt.figure(figsize=(10, 6))
plt.bar(['SW1', 'SW2'], [packet_drops[1], packet_drops[2]], color=['blue', 'orange'])
plt.xlabel('Switch')
plt.ylabel('Packets Dropped')
plt.title('Packet Drops')
plt.grid(axis='y')
plt.savefig("packet_drops.png")
plt.show()
