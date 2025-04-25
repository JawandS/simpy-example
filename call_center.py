# -----------------------------
# Dependencies
# -----------------------------
import simpy
import numpy as np
import pandas as pd

# -----------------------------
# Simulation Parameters
# -----------------------------
NUM_AGENTS = 25               # Number of call center agents
SIM_DURATION = 8 * 60         # Simulation runs for 8 hours (480 minutes)
CALLS_PER_MINUTE = 3          # Constant number of incoming calls per minute
MEAN_CALL_DURATION = 8        # Average call duration in minutes
STD_CALL_DURATION = 5         # Standard deviation of call duration
NUM_RUNS = 5                  # Number of simulation runs

# -----------------------------
# Customer Process
# -----------------------------
def customer(env, agents, wait_times, call_durations):
    """
    Simulates a single customer calling the center.

    - Waits for an available agent.
    - Records wait time and call duration.
    """
    arrival = env.now
    with agents.request() as request:
        yield request
        wait_time = env.now - arrival
        wait_times.append(wait_time)

        # Simulate the actual call duration
        duration = max(1, np.random.normal(MEAN_CALL_DURATION, STD_CALL_DURATION))
        call_durations.append(duration)
        yield env.timeout(duration)

# -----------------------------
# Call Generator Process
# -----------------------------
def generate_calls(env, agents, wait_times, call_durations):
    """
    Generates a fixed number of calls every minute.
    """
    while env.now < SIM_DURATION:
        for i in range(CALLS_PER_MINUTE):
            env.process(customer(env, agents, wait_times, call_durations))
        yield env.timeout(1)  # Wait 1 minute before next batch

# -----------------------------
# Simulation Runner
# -----------------------------
def run_simulation():
    """
    Runs the call center simulation multiple times and collects performance metrics.
    Returns a DataFrame with results.
    """
    all_results = []

    for run in range(1, NUM_RUNS + 1):
        env = simpy.Environment()
        agents = simpy.Resource(env, capacity=NUM_AGENTS)
        wait_times = []
        call_durations = []

        env.process(generate_calls(env, agents, wait_times, call_durations))
        env.run(until=SIM_DURATION)

        # Store metrics for this run
        all_results.append({
            "Run": run,
            "Avg Wait Time (min)": round(np.mean(wait_times), 2) if wait_times else 0,
            "Max Wait Time (min)": round(max(wait_times), 2) if wait_times else 0,
            "Avg Call Duration (min)": round(np.mean(call_durations), 2) if call_durations else 0,
            "Total Calls": len(call_durations)
        })

    return pd.DataFrame(all_results)

# -----------------------------
# Run the Simulation and Display Results
# -----------------------------
if __name__ == "__main__":
    results_df = run_simulation()
    print("\nSimulation Results (Fixed Call Rate):\n")
    print(results_df.to_string(index=False))
