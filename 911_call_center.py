# Simulating a 911 Call Center using SimPy
# This script simulates a call center environment where customers call in and are served by available agents


# Dependencies
import simpy
import numpy as np
import pandas as pd

# ---------------------
# Simulation Info
# ---------------------

# Define periods of call volume rates
HIGH_PERIOD = set(range(12 * 60, 16 * 60))  # Peak time between 12pm and 4pm
MODERATE_PERIOD = set(range(8 * 60, 12 * 60)) # Moderate time between 8am and 12pm
LOW_PERIOD = set(range(0, 8 * 60)) | set(range(16 * 60, 24 * 60))  # Low time before 8am and after 4pm

def call_rate(env):
    """
    Determines the call rate based on the current time in the simulation.
    Uses a Poisson distribution to generate the number of calls.

    Parameters:
        env (simpy.Environment): The simulation environment.

    Returns:
        int: Number of calls to be generated based on the time period.
    """
    if env.now in HIGH_PERIOD:
        return np.random.poisson(lam=2.5)
    elif env.now in MODERATE_PERIOD:
        return np.random.poisson(lam=1.5)
    else:
        return np.random.poisson(lam=0.5)

def call_length(env):
    """
    Determines the call length based on the current time in the simulation.
    Uses a normal distribution to generate the call duration.

    Parameters:
        env (simpy.Environment): The simulation environment.

    Returns:
        float: Duration of the call.
    """
    if env.now in HIGH_PERIOD:
        return max(1, np.random.normal(loc=10, scale=3))
    elif env.now in MODERATE_PERIOD:
        return max(1, np.random.normal(loc=7, scale=2))
    else:
        return max(1, np.random.normal(loc=5, scale=1))

# ---------------------
# Simulation Process
# ---------------------

def person_call(env, caller_id, agents, wait_times, call_durations):
    """
    Simulates a call from a person to the call center.

    Parameters:
        env (simpy.Environment): The simulation environment.
        caller_id (int): Identifier for the caller.
        agents (simpy.Resource): Resource representing available agents.
        wait_times (list): List to record each caller's wait time.
        call_durations (list): List to record each call's duration.
    
    Yields:
        simpy.Event: Represents the time the caller waits and the call duration.
    """
    # Log the time the call arrives
    arrival_time = env.now
    # Request an agent
    with agents.request() as request:
        yield request
        wait_time = env.now - arrival_time
        # Log the time the caller starts talking to an agent
        wait_times.append(wait_time)

        duration = call_length(env)
        # Log the length of the call
        call_durations.append(duration)
        yield env.timeout(duration)

def call_generator(env, agents, wait_times, call_durations):
    """
    Generates calls to the call center over time.
    Calls are generated based on the call rate determined by the time of day.

    Parameters:
        env (simpy.Environment): The simulation environment.
        agents (simpy.Resource): Resource representing available agents.
        wait_times (list): List to track wait times.
        call_durations (list): List to track call durations.

    Yields:
        simpy.Event: Triggers every simulated minute to generate new calls.
    """
    caller_id = 0
    while env.now < 24 * 60:  # Simulate for 24 hours
        num_calls = call_rate(env) # Get the number of calls to generate
        for _ in range(num_calls):
            # Generate a call
            env.process(person_call(env, caller_id, agents, wait_times, call_durations))
            caller_id += 1
        yield env.timeout(1)  # wait for 1 minute of simulated time

# ---------------------
# Run Simulation
# ---------------------

def run_simulation():
    env = simpy.Environment()
    agents = simpy.Resource(env, capacity=12)  # Initialize agents 

    wait_times = []
    call_durations = []

    env.process(call_generator(env, agents, wait_times, call_durations))
    env.run(until=24 * 60)  # Run for 24 hours

    print(f"Total calls handled: {len(call_durations)}")
    print(f"Average wait time: {np.mean(wait_times):.2f} min")
    print(f"Max wait time: {max(wait_times):.2f} min")
    print(f"Average call duration: {np.mean(call_durations):.2f} min")
    return wait_times, call_durations

# Run the simulation
if __name__ == "__main__":
    seed = 404
    # Run 5 times
    for i in range(5):
        print("-" * 40)
        np.random.seed(seed + i)
        print(f"Run {i + 1}:")
        wait_times, call_durations = run_simulation()        
    print("-" * 40)
