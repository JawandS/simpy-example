import simpy
import numpy as np
import pandas as pd

# ---------------------
# Sim Parameters
# ---------------------
# Call rates per minute
CALL_RATE = 1.5

# Call durations in minutes
CALL_DURATION = 7
CALL_DURATION_STD = 5

# Number of agents
AGENTS = 15

# ---------------------
# Call Behavior
# ---------------------
def call_rate(env):
    return np.random.poisson(lam=CALL_RATE)

def call_length(env):
    return max(1, np.random.normal(loc=CALL_DURATION, scale=CALL_DURATION_STD))

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
        for i in range(AGENTS):
            agent = Agent(f"Agent_{i}")
            self.store.put(agent)

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
    all_wait_times = []
    all_call_durations = []

    seed = 404
    SIMULATIONS = 25
    for i in range(SIMULATIONS):
        np.random.seed(seed + i)
        wait_times, call_durations = run_simulation()
        all_wait_times.extend(wait_times)
        all_call_durations.extend(call_durations)

    # Convert to DataFrame for analysis
    results = pd.DataFrame({
        "Wait Time": all_wait_times,
        "Call Duration": all_call_durations
    })
    results["Wait Time"] = results["Wait Time"].astype(int)
    results["Call Duration"] = results["Call Duration"].astype(int)

    # Display summary statistics
    print(f"Total Calls: {len(results) / SIMULATIONS:.0f}")
    print(f"Avg Wait Time: {results['Wait Time'].mean():.2f} minutes")
    print(f"Max Wait Time: {results['Wait Time'].max()} minutes")