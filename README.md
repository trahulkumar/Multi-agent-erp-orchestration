# Decentralized Multi-Agent Orchestration for Legacy Order-to-Cash Optimization

This repository contains the discrete-event simulation (DES) source code and experimental data supporting the research paper: **"Decentralized Multi-Agent Orchestration for Legacy Order-to-Cash Optimization"**.

The simulation validates the performance of a proposed Multi-Agent System (MAS) against traditional Monolithic architectures and Rule-Based Robotic Process Automation (RPA) baselines within an enterprise ERP environment.

## 📄 Abstract

Legacy Enterprise Resource Planning (ERP) systems often create bottlenecks due to rigid, sequential workflow logic. This study proposes a non-invasive modernization framework overlaying a Decentralized Multi-Agent System (MAS) on existing infrastructure. By utilizing a Digital Twin for training, agents learn to orchestrate credit validation, inventory allocation, and fulfillment in parallel.

This simulation models the Order-to-Cash (O2C) cycle to quantify trade-offs between **throughput**, **cycle time**, **error rates**, and **economic ROI**.

## 🛠️ Tech Stack & Requirements

The simulation is built using Python's discrete-event simulation framework.

* **Python** 3.8+
* **SimPy** (Process-based discrete-event simulation)
* **Pandas** (Data manipulation and tabulation)
* **NumPy** (Statistical operations)
* **Matplotlib** (Data visualization)

### Installation
```bash
pip install simpy pandas numpy matplotlib
```
*Note: If you are usinguv, you can run `uv sync` to install dependencies.*

## 🚀 Simulation Overview

The script `src/simulation_main.py` models three distinct architectural patterns:

### 1. Monolithic System (Baseline 1)

* **Behavior:** Strictly sequential processing (FIFO).
* **Constraint:** Uses global locking; a delay in one stage (e.g., Credit Check) blocks the entire pipeline to maintain ACID compliance.
* **Outcome:** Low throughput, zero concurrency, low error rate.

### 2. Rule-Based RPA (Baseline 2)

* **Behavior:** Parallel processing using rigid, pre-defined rules.
* **Constraint:** "Conservative" logic. If a risk threshold is met, the process halts immediately to prevent errors.
* **Outcome:** Improved speed over monolithic, but limited throughput due to risk aversion.

### 3. Multi-Agent System (Proposed)

* **Behavior:** Decentralized, "Optimistic" parallel execution using CTDE (Centralized Training, Decentralized Execution).
* **Constraint:** Agents are allowed to make probabilistic decisions, occasionally allowing "risky" orders to proceed to maximize flow.
* **Outcome:** Highest throughput (+117% vs Monolithic), higher error rate, but significantly higher **Net Economic Value**.

## 📊 Usage

Run the simulation script to generate the comparative metrics table:

```bash
python src/simulation_main.py
```

To generate the academic figures:

```bash
python src/visualization.py
```

### Sample Output

The script generates a comparison table similar to the one below:

| System | Throughput (Orders) | Avg Cycle Time | Error Rate (%) | Net Economic Value ($) |
| --- | --- | --- | --- | --- |
| Monolithic | 177 | 27.60 | 0.00 | $88,500 |
| RPA | 178 | 21.18 | 0.00 | $89,000 |
| MAS | 189 | 17.84 | 5.84 | $93,948 |

## 📂 Repository Structure

```
├── src/
│   ├── simulation_main.py    # Main SimPy logic for Monolithic, RPA, and MAS
│   └── visualization.py      # Script to generate Figures 1, 2, and 3
├── assets/
│   ├── fig1_architecture.png # Proposed Framework Diagram
│   ├── fig2_performance.png  # Performance Comparison Chart
│   └── fig3_distribution.png # Distribution Analysis
├── output/
│   └── simulation_results.csv # Generated dataset from the latest run
├── README.md                 # Project documentation
├── requirements.txt          # Dependencies
└── pyproject.toml            # uv project configuration
```

## 📝 Citation

If you use this code or methodology in your research, please cite the associated paper:

```bibtex
@article{Thatikonda2026Decentralized,
  title={Decentralized Multi-Agent Orchestration for Legacy Order-to-Cash Optimization},
  author={Thatikonda, Rahul Kumar and Donepudi, Sucharitha},
  journal={Telkomnika (Telecommunication Computing Electronics and Control)},
  year={2026},
  note={Under Review}
}
```

## ⚖️ License

This project is licensed under the MIT License - see the LICENSE file for details.
