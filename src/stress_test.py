import simpy
import random
import pandas as pd
import numpy as np
import os

# --- CORE SIMULATION ENGINE ---

# Configuration (Global defaults, some overridden in stress test)
SIM_TIME = 1000
NUM_EPISODES = 50  # Average over this many runs for stability
ARRIVAL_RATE = 5   # Poisson lambda (default)
RESOURCES = 10     # Worker threads
FAILURE_PROB = 0.10 # Base failure probability

class Order:
    def __init__(self, env, order_id):
        self.env = env
        self.id = order_id
        self.arrival_time = env.now
        self.value = random.uniform(100, 5000)
        self.is_error = False
        self.start_process_time = 0
        self.end_process_time = 0

def monolithic_process(env, order, resource, stats):
    with resource.request() as req:
        yield req
        order.start_process_time = env.now
        yield env.timeout(random.uniform(5, 15)) # Credit
        if random.random() < FAILURE_PROB:
            return 
        yield env.timeout(random.uniform(3, 8))  # Inventory
        yield env.timeout(random.uniform(5, 12)) # Fulfillment
        yield env.timeout(random.uniform(2, 5))  # Billing
        order.end_process_time = env.now
        stats['completed'] += 1
        stats['cycle_times'].append(order.end_process_time - order.arrival_time)

def rpa_process(env, order, resources, stats):
    order.start_process_time = env.now
    with resources['credit'].request() as req:
        yield req
        yield env.timeout(random.uniform(4, 10))
        if random.random() < FAILURE_PROB:
            return 
    with resources['inventory'].request() as req:
        yield req
        yield env.timeout(random.uniform(2, 6))
    with resources['fulfillment'].request() as req:
        yield req
        yield env.timeout(random.uniform(4, 10))
    with resources['billing'].request() as req:
        yield req
        yield env.timeout(random.uniform(1, 4))
    order.end_process_time = env.now
    stats['completed'] += 1
    stats['cycle_times'].append(order.end_process_time - order.arrival_time)

def mas_process(env, order, resources, stats):
    order.start_process_time = env.now
    with resources['credit'].request() as req:
        yield req
        yield env.timeout(random.uniform(6, 12)) 
        if random.random() < FAILURE_PROB:
            if random.random() < 0.60:
                order.is_error = True
            else:
                return
    yield env.timeout(random.uniform(5, 10)) # Pipelined effective time
    order.end_process_time = env.now
    if order.is_error:
        stats['errors'] += 1
        stats['completed'] += 1
    else:
        stats['completed'] += 1
    stats['cycle_times'].append(order.end_process_time - order.arrival_time)

def run_simulation(mode, current_arrival_rate):
    env = simpy.Environment()
    stats = {'completed': 0, 'errors': 0, 'cycle_times': []}
    if mode == 'Monolithic':
        resources = simpy.Resource(env, capacity=RESOURCES)
    else:
        resources = {
            'credit': simpy.Resource(env, capacity=int(RESOURCES/4) + 1),
            'inventory': simpy.Resource(env, capacity=int(RESOURCES/4) + 1),
            'fulfillment': simpy.Resource(env, capacity=int(RESOURCES/4) + 1),
            'billing': simpy.Resource(env, capacity=int(RESOURCES/4) + 1)
        }

    def order_generator():
        order_id = 0
        while True:
            yield env.timeout(random.expovariate(1.0 / current_arrival_rate))
            order_id += 1
            order = Order(env, order_id)
            if mode == 'Monolithic':
                env.process(monolithic_process(env, order, resources, stats))
            elif mode == 'RPA':
                env.process(rpa_process(env, order, resources, stats))
            elif mode == 'MAS':
                env.process(mas_process(env, order, resources, stats))

    env.process(order_generator())
    env.run(until=SIM_TIME)
    return stats

# --- SCALABILITY STRESS TEST LOGIC ---

if __name__ == "__main__":
    print("Running SCALABILITY Stress Test...")

    # We test two scenarios: Normal Load (5) vs High Stress (8)
    arrival_scenarios = [5, 8]
    results = []

    for rate in arrival_scenarios:
        print(f"\nSimulating Arrival Rate (Lambda) = {rate}...")
        
        for mode in ['Monolithic', 'RPA', 'MAS']:
            agg_throughput = []
            agg_cycle = []
            agg_error = []
            
            for _ in range(NUM_EPISODES):
                s = run_simulation(mode, rate)
                agg_throughput.append(s['completed'])
                if s['cycle_times']:
                    agg_cycle.append(np.mean(s['cycle_times']))
                else:
                    agg_cycle.append(0)
                
                if s['completed'] > 0:
                    err = (s['errors'] / s['completed']) * 100
                else:
                    err = 0
                agg_error.append(err)

            # Averages
            avg_tp = int(np.mean(agg_throughput))
            avg_cyc = np.mean(agg_cycle)
            avg_err = np.mean(agg_error)
            
            results.append({
                'Load Intensity': f"Lambda={rate}",
                'System': mode,
                'Throughput': avg_tp,
                'Avg Cycle Time': round(avg_cyc, 2),
                'Error Rate (%)': round(avg_err, 2)
            })

    df_scale = pd.DataFrame(results)
    print("\n--- NEW TABLE 5 (SCALABILITY ANALYSIS) ---")
    print(df_scale.to_string(index=False))

    # Save results
    os.makedirs('output', exist_ok=True)
    df_scale.to_csv('output/stress_test_results.csv', index=False)
    print(f"\nStress test results saved to 'output/stress_test_results.csv'")
