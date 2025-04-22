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
# Sim Parameters
# ---------------------
# Call rates per minute
HIGH_CALLS_RATE = 3
MODERATE_CALLS_RATE = 2
LOW_CALLS_RATE = 0.8

# Call durations in minutes
HIGH_CALLS_DURATION = 10
HIGH_CALLS_DURATION_STD = 3
MODERATE_CALLS_DURATION = 7
MODERATE_CALLS_DURATION_STD = 2
LOW_CALLS_DURATION = 5
LOW_CALLS_DURATION_STD = 1

# Number of agents
HIGH_AGENTS = 25
MODERATE_AGENTS = 15
LOW_AGENTS = 5

# ---------------------
# Call Behavior
# ---------------------
def call_rate(env):
    if int(env.now) in HIGH_PERIOD:
        return np.random.poisson(lam=HIGH_CALLS_RATE)
    elif int(env.now) in MODERATE_PERIOD:
        return np.random.poisson(lam=MODERATE_CALLS_RATE)
    else:
        return np.random.poisson(lam=LOW_CALLS_RATE)

def call_length(env):
    if int(env.now) in HIGH_PERIOD:
        return max(1, np.random.normal(loc=HIGH_CALLS_DURATION, scale=HIGH_CALLS_DURATION_STD))
    elif int(env.now) in MODERATE_PERIOD:
        return max(1, np.random.normal(loc=MODERATE_CALLS_DURATION, scale=MODERATE_CALLS_DURATION))
    else:
        return max(1, np.random.normal(loc=LOW_CALLS_DURATION, scale=LOW_CALLS_DURATION_STD))

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
        self.target_capacity = LOW_AGENTS
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
                target = HIGH_AGENTS
            elif now in MODERATE_PERIOD:
                target = MODERATE_AGENTS
            else:
                target = LOW_AGENTS

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
    for i in range(25):
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

    print("Simulation Results:")
    # Print average of each column (round to 2 decimal places)
    print("Total Calls:", results["Total Calls"].mean())
    print("Avg Wait Time:", round(results["Avg Wait Time"].mean(), 2))
    print("Max Wait Time:", round(max(results["Max Wait Time"]), 2))
    print("Avg Duration:", round(results["Avg Duration"].mean(), 2))
