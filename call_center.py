import simpy
import numpy as np
import pandas as pd

# Simulation parameters
NUM_AGENTS = 15
SIM_END = 8 * 60 # 8 hours = 480 minutes (from 9am to 5pm)
MEAN_CALLS_PER_MIN = 3
STD_CALLS_PER_MIN = 1
MEAN_CALL_DURATION = 10
STD_CALL_DURATION = 3
NUM_RUNS = 5

# Results storage
results = []

def customer(env, name, agents, call_duration, wait_times, call_durations):
    """
    Simulates a customer call by requesting an available agent and processing the call.

    Parameters:
        env (simpy.Environment): The simulation environment.
        name (str): Identifier for the customer.
        agents (simpy.FilterStore): Store of available agents.
        call_duration (float): Duration of the customer's call.
        wait_times (list): List to record each customer's wait time.
        call_durations (list): List to record each call's duration.

    Yields:
        simpy.Event: Represents resource request and call duration.
    """
    arrival_time = env.now
    with agents.get(lambda x: True) as req:
        yield req
        wait_time = env.now - arrival_time
        wait_times.append(wait_time)

        yield env.timeout(call_duration)
        call_durations.append(call_duration)
        agents.put("agent")

def customer_generator(env, agents, wait_times, call_durations):
    """
    Generates customers calling the call center over time.

    Parameters:
        env (simpy.Environment): The simulation environment.
        agents (simpy.FilterStore): Store of available agents.
        wait_times (list): List to track wait times.
        call_durations (list): List to track call durations.

    Yields:
        simpy.Event: Triggers every simulated minute to generate new calls.
    """
    while env.now < SIM_END:
        calls = max(0, int(np.random.normal(MEAN_CALLS_PER_MIN, STD_CALLS_PER_MIN)))
        for i in range(calls):
            duration = max(1, np.random.normal(MEAN_CALL_DURATION, STD_CALL_DURATION))
            env.process(customer(env, f'Customer_{env.now}_{i}', agents, duration, wait_times, call_durations))
        yield env.timeout(1)

def run_simulation():
    """
    Runs the call center simulation multiple times and aggregates results.

    Returns:
        pd.DataFrame: DataFrame with average wait time, call duration, and call count for each run.
    """
    for run in range(NUM_RUNS):
        env = simpy.Environment()
        agents = simpy.FilterStore(env, capacity=NUM_AGENTS)
        for _ in range(NUM_AGENTS):
            agents.items.append("agent")

        wait_times = []
        call_durations = []

        env.process(customer_generator(env, agents, wait_times, call_durations))
        env.run(until=SIM_END)

        results.append({
            'Run': run + 1,
            'Avg Wait Time': np.mean(wait_times) if wait_times else 0,
            'Max Wait Time': max(wait_times) if wait_times else 0,
            'Avg Call Duration': np.mean(call_durations) if call_durations else 0,
            'Total Calls': len(call_durations)
        })

    return pd.DataFrame(results)

# Execute the simulation and display results
if __name__ == "__main__":
    df = run_simulation()
    print(df)
