import simpy
import numpy as np
import pandas as pd

# ---------------------
# Time Period Definitions
# ---------------------
HIGH_PERIOD = set(range(12 * 60, 16 * 60))         # 12:00 PM – 3:59 PM
MODERATE_PERIOD = set(range(8 * 60, 12 * 60))      # 8:00 AM – 11:59 AM
LOW_PERIOD = set(range(0, 8 * 60)) | set(range(16 * 60, 24 * 60))  # All other hours

# ---------------------
# Call Behavior
# ---------------------
def call_rate(env):
    if int(env.now) in HIGH_PERIOD:
        return np.random.poisson(lam=3)
    elif int(env.now) in MODERATE_PERIOD:
        return np.random.poisson(lam=2)
    else:
        return np.random.poisson(lam=0.8)

def call_length(env):
    if int(env.now) in HIGH_PERIOD:
        return max(1, np.random.normal(loc=10, scale=3))
    elif int(env.now) in MODERATE_PERIOD:
        return max(1, np.random.normal(loc=7, scale=2))
    else:
        return max(1, np.random.normal(loc=5, scale=1))

# ---------------------
# Agent Class
# ---------------------
class Agent:
    def __init__(self, agent_id):
        self.id = agent_id

# ---------------------
# Call Center Using Store
# ---------------------
class CallCenter:
    def __init__(self, env):
        self.env = env
        self.store = simpy.Store(env)
        self.all_agents = []
        self.target_capacity = 5
        self._initialize_agents(self.target_capacity)
        env.process(self.shift_manager())

    def _initialize_agents(self, count):
        for i in range(count):
            agent = Agent(f"Agent_{i}")
            self.all_agents.append(agent)
            self.store.put(agent)

    def shift_manager(self):
        while True:
            now = int(self.env.now)
            if now in HIGH_PERIOD:
                target = 25
            elif now in MODERATE_PERIOD:
                target = 15
            else:
                target = 5

            current_total = len(self.all_agents)
            idle_agents = len(self.store.items)

            if target > current_total:
                # Add new agents to both pool and idle store
                for i in range(current_total, target):
                    agent = Agent(f"Agent_{i}")
                    self.all_agents.append(agent)
                    self.store.put(agent)
            elif target < current_total:
                # Mark agents as inactive only if they are idle
                excess = current_total - target
                removed = 0
                new_all_agents = []
                for agent in self.all_agents:
                    if removed < excess and agent in self.store.items:
                        self.store.items.remove(agent)
                        removed += 1
                    else:
                        new_all_agents.append(agent)
                self.all_agents = new_all_agents

            yield self.env.timeout(1)

# ---------------------
# Simulation Processes
# ---------------------
def person_call(env, caller_id, call_center, wait_times, call_durations):
    arrival_time = env.now
    agent = yield call_center.store.get()
    wait_time = env.now - arrival_time
    wait_times.append(wait_time)

    duration = call_length(env)
    call_durations.append(duration)
    yield env.timeout(duration)

    # Agent becomes available again
    yield call_center.store.put(agent)

def call_generator(env, call_center, wait_times, call_durations):
    caller_id = 0
    while env.now < 24 * 60:
        num_calls = call_rate(env)
        for _ in range(num_calls):
            env.process(person_call(env, caller_id, call_center, wait_times, call_durations))
            caller_id += 1
        yield env.timeout(1)

# ---------------------
# Run Simulation
# ---------------------
def run_simulation():
    env = simpy.Environment()
    call_center = CallCenter(env)

    wait_times = []
    call_durations = []

    env.process(call_generator(env, call_center, wait_times, call_durations))
    env.run(until=24 * 60)

    return wait_times, call_durations

# ---------------------
# Multiple Simulation Runs
# ---------------------
if __name__ == "__main__":
    results = pd.DataFrame(columns=["Total Calls", "Avg Wait Time", "Max Wait Time", "Avg Duration"])

    seed = 404
    for i in range(5):
        np.random.seed(seed + i)
        wait_times, call_durations = run_simulation()
        simulation_result = pd.DataFrame({
            "Total Calls": len(call_durations),
            "Avg Wait Time": np.mean(wait_times),
            "Max Wait Time": max(wait_times),
            "Avg Duration": np.mean(call_durations)
        }, index=[i])
        if len(results) == 0:
            results = simulation_result
        else:
            results = pd.concat([results, simulation_result])

    print("\nSimulation Results:")
    print(results)
