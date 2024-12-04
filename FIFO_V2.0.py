import simpy
import random
import matplotlib.pyplot as plt

# Constants
SIM_TIME = 0.40 * 60 * 60
QUEUE_MAX_SIZE = 40
SERVICE_TIME = 0.253
NETWORK_LATENCY = 0.2

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
            
            packet_drops[self.id] += 1

    def dequeue(self):
        while True:
            if self.queue_size > 0:
                packet = yield self.queue.get()
                self.queue_size -= 1
                queue_times[self.id].append(self.env.now - packet['time'])
                yield self.env.timeout(SERVICE_TIME)
            else:
                yield self.env.timeout(0.1)


def packet_generator(env, pc_id, primary_switch, secondary_switch=None):
    while True:

        interval = random.uniform(0.1, 0.5)
        yield env.timeout(interval)

        yield env.timeout(NETWORK_LATENCY)
        packet = {'time': env.now, 'source': pc_id}
        primary_switch.enqueue(packet, secondary_switch)


def log_queue_length(env):
    while True:
        for i in queue_lengths:
            queue_lengths[i].append({'time': env.now, 'length': switches[i].queue_size})
        yield env.timeout(10)


env = simpy.Environment()
switches = {
    1: Switch(env, 1),
    2: Switch(env, 2)
}

for sw in switches.values():
    env.process(sw.dequeue())

env.process(packet_generator(env, 'PC1', switches[1], switches[2]))
env.process(packet_generator(env, 'PC2', switches[1], switches[2]))
env.process(packet_generator(env, 'PC3', switches[1], switches[2]))
env.process(packet_generator(env, 'PC4', switches[2], switches[1]))

env.process(log_queue_length(env))

env.run(until=SIM_TIME)

times = [entry['time'] for entry in queue_lengths[1]]
queue1_lengths = [entry['length'] for entry in queue_lengths[1]]
queue2_lengths = [entry['length'] for entry in queue_lengths[2]]

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

plt.figure(figsize=(10, 6))
plt.bar(['SW1', 'SW2'], [packet_drops[1], packet_drops[2]], color=['blue', 'orange'])
plt.xlabel('Switch')
plt.ylabel('Packets Dropped')
plt.title('Packet Drops')
plt.grid(axis='y')
plt.savefig("packet_drops.png")
plt.show()
