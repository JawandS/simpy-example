# Simulating a 911 Call Center using SimPy with dynamic agent resources
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
# Call Center Controller
# ---------------------
class CallCenter:
    def __init__(self, env):
        self.env = env
        self.agents = simpy.Resource(env, capacity=5)  # Initial low-period capacity
        env.process(self.shift_manager())

    def shift_manager(self):
        while True:
            minute = int(self.env.now)
            if minute in HIGH_PERIOD:
                capacity = 25
            elif minute in MODERATE_PERIOD:
                capacity = 15
            else:
                capacity = 5
            # Only update if the capacity has changed
            if self.agents.capacity != capacity:
                self.agents = simpy.Resource(self.env, capacity=capacity)
            yield self.env.timeout(1)

# ---------------------
# Simulation Processes
# ---------------------
def person_call(env, caller_id, call_center, wait_times, call_durations):
    arrival_time = env.now
    with call_center.agents.request() as request:
        yield request
        wait_time = env.now - arrival_time
        wait_times.append(wait_time)
        duration = call_length(env)
        call_durations.append(duration)
        yield env.timeout(duration)

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
    # Track results
    results = pd.DataFrame(columns=["Total Calls", "Avg Wait Time", "Max Wait Time", "Avg Duration"])

    # Run simulations
    seed = 404
    for i in range(5):
        np.random.seed(seed + i)
        wait_times, call_durations = run_simulation()
        results = pd.concat([results, pd.DataFrame({
            "Total Calls": len(call_durations),
            "Avg Wait Time": np.mean(wait_times),
            "Max Wait Time": max(wait_times),
            "Avg Duration": np.mean(call_durations)
        }, index=[0])])
    print("\nSimulation Results:")
    print(results)
