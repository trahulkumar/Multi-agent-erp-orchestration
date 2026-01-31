import simpy
import random
import pandas as pd
import numpy as np
import os

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# --- CONFIGURATION (Based on Paper Table 2) ---
SIM_TIME = 1000
NUM_EPISODES = 50  # Average over this many runs for stability
ARRIVAL_RATE = 5   # Poisson lambda
RESOURCES = 10     # Worker threads
FAILURE_PROB = 0.10 # Base failure probability (Credit check, etc.)

# Cost for ROI Calculation (for Discussion section later)
AVG_ORDER_VALUE = 2500 # Midpoint of U(100, 5000)
MARGIN = 0.20          # 20% profit margin
COST_MANUAL_FIX = 50   # Cost to fix an error manually

class Order:
    def __init__(self, env, order_id):
        self.env = env
        self.id = order_id
        self.arrival_time = env.now
        self.value = random.uniform(100, 5000)
        self.is_error = False
        self.start_process_time = 0
        self.end_process_time = 0

# --- SYSTEM 1: MONOLITHIC (Sequential, Locking) ---
def monolithic_process(env, order, resource, stats):
    with resource.request() as req:
        yield req
        order.start_process_time = env.now
        
        # Sequential Stages (Credit -> Inventory -> Fulfillment -> Billing)
        # If any fails, the whole chain holds the lock longer or fails entirely
        
        # Credit Check (Slow, Blocking)
        yield env.timeout(random.uniform(5, 15))
        if random.random() < FAILURE_PROB:
            # Monolithic fails safely but slowly (catches error, rejects order)
            stats['errors'] += 0 # Rejected, not an "error" in downstream, just lost throughput
            return 

        # Inventory (Blocking)
        yield env.timeout(random.uniform(3, 8))
        
        # Fulfillment (Blocking)
        yield env.timeout(random.uniform(5, 12))
        
        # Billing (Blocking)
        yield env.timeout(random.uniform(2, 5))
        
        order.end_process_time = env.now
        stats['completed'] += 1
        stats['cycle_times'].append(order.end_process_time - order.arrival_time)

# --- SYSTEM 2: RPA (Rule-Based, Parallel but Rigid) ---
def rpa_process(env, order, resources, stats):
    # RPA does not lock the whole chain; it uses separate resources for each stage.
    # But it has strict rules: If Credit is "Risk", it stops immediately (Conservative).
    
    order.start_process_time = env.now
    
    # Stage 1: Credit Agent (RPA)
    with resources['credit'].request() as req:
        yield req
        yield env.timeout(random.uniform(4, 10)) # Faster than monolithic
        if random.random() < FAILURE_PROB:
            # RPA Rule: "If risk > threshold, REJECT immediately"
            return 

    # Stage 2: Inventory Agent (RPA)
    with resources['inventory'].request() as req:
        yield req
        yield env.timeout(random.uniform(2, 6))

    # Stage 3: Fulfillment Agent (RPA)
    with resources['fulfillment'].request() as req:
        yield req
        yield env.timeout(random.uniform(4, 10))
        
    # Stage 4: Billing Agent (RPA)
    with resources['billing'].request() as req:
        yield req
        yield env.timeout(random.uniform(1, 4))
        
    order.end_process_time = env.now
    stats['completed'] += 1
    stats['cycle_times'].append(order.end_process_time - order.arrival_time)

# --- SYSTEM 3: MAS (Proposed, Optimistic, Parallel) ---
def mas_process(env, order, resources, stats):
    # MAS uses "Optimistic Execution". It starts Inventory/Fulfillment 
    # BEFORE Credit is fully finalized if confidence is high.
    
    order.start_process_time = env.now
    
    # Parallel Execution Trigger
    # We simulate this by checking multiple resources simultaneously
    
    # Credit Agent (Central Orchestrator)
    # MAS involves a decision logic overhead (decision latency) but doesn't block others
    with resources['credit'].request() as req:
        yield req
        yield env.timeout(random.uniform(6, 12)) 
        
        # OPTIMISTIC POLICY:
        # The agent approves "marginal" cases to keep throughput high.
        # This increases throughput but allows some "bad" orders through (Higher Error Rate)
        if random.random() < FAILURE_PROB:
            # 60% chance MAS tries to push it through anyway (Policy: "Optimistic")
            if random.random() < 0.60:
                order.is_error = True # This will be a downstream error
            else:
                return # Standard rejection

    # Inventory & Fulfillment happen in parallel/pipelined fashion in MAS
    # Modeled as faster effective service time due to pipelining
    yield env.timeout(random.uniform(5, 10)) # Combined effective time
    
    order.end_process_time = env.now
    
    if order.is_error:
        stats['errors'] += 1 # Passed through but requires manual fix later
        stats['completed'] += 1 # It counts as throughput, but dirty throughput
    else:
        stats['completed'] += 1
        
    stats['cycle_times'].append(order.end_process_time - order.arrival_time)

# --- SIMULATION RUNNER ---
def run_simulation(mode):
    env = simpy.Environment()
    stats = {'completed': 0, 'errors': 0, 'cycle_times': []}
    
    # Resource Setup
    if mode == 'Monolithic':
        # Single pool, global lock
        resources = simpy.Resource(env, capacity=RESOURCES)
    else:
        # Specialized Agents pools
        resources = {
            'credit': simpy.Resource(env, capacity=int(RESOURCES/4) + 1),
            'inventory': simpy.Resource(env, capacity=int(RESOURCES/4) + 1),
            'fulfillment': simpy.Resource(env, capacity=int(RESOURCES/4) + 1),
            'billing': simpy.Resource(env, capacity=int(RESOURCES/4) + 1)
        }

    # Traffic Generator
    def order_generator():
        order_id = 0
        while True:
            yield env.timeout(random.expovariate(1.0 / ARRIVAL_RATE))
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

# --- MAIN EXECUTION ---
print("Running Simulations (Averaging over 50 episodes)...")

modes = ['Monolithic', 'RPA', 'MAS']
results = []

for mode in modes:
    agg_throughput = []
    agg_cycle = []
    agg_error = []
    
    for _ in range(NUM_EPISODES):
        s = run_simulation(mode)
        agg_throughput.append(s['completed'])
        if s['cycle_times']:
            agg_cycle.append(np.mean(s['cycle_times']))
        else:
            agg_cycle.append(0)
        
        # Error Rate calculation
        if s['completed'] > 0:
            rate = (s['errors'] / s['completed']) * 100
        else:
            rate = 0
        agg_error.append(rate)

    # Averages
    avg_tp = int(np.mean(agg_throughput))
    avg_cyc = np.mean(agg_cycle)
    avg_err = np.mean(agg_error)
    
    # ROI Calc (Projected)
    # Value = (Throughput * Profit) - (Errors * ManualCost)
    gross_profit = avg_tp * AVG_ORDER_VALUE * MARGIN
    error_cost = (avg_tp * (avg_err/100)) * COST_MANUAL_FIX
    net_value = gross_profit - error_cost
    
    results.append({
        'System': mode,
        'Throughput (Orders)': avg_tp,
        'Avg Cycle Time': round(avg_cyc, 2),
        'Error Rate (%)': round(avg_err, 2),
        'Net Economic Value ($)': int(net_value)
    })

df = pd.DataFrame(results)
print("\n--- NEW TABLE 3 (SIMULATION RESULTS) ---")
print(df.to_string(index=False))

# Calculate Improvements for the paper text
base_tp = df[df['System'] == 'Monolithic']['Throughput (Orders)'].values[0]
mas_tp = df[df['System'] == 'MAS']['Throughput (Orders)'].values[0]
rpa_tp = df[df['System'] == 'RPA']['Throughput (Orders)'].values[0]

print(f"\n--- Key Improvements ---")
print(f"MAS vs Monolithic Throughput: +{((mas_tp - base_tp)/base_tp)*100:.1f}%")
print(f"RPA vs Monolithic Throughput: +{((rpa_tp - base_tp)/base_tp)*100:.1f}%")
print(f"MAS vs RPA Throughput: +{((mas_tp - rpa_tp)/rpa_tp)*100:.1f}%")

# Save results to CSV (relative to project root if run from root)
# Using os.path.join to be safe
output_file = os.path.join('output', 'simulation_results.csv')
df.to_csv(output_file, index=False)
print(f"\nResults saved to '{output_file}'")