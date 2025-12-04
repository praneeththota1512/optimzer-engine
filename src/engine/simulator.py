"""
Monte Carlo simulator for robustness testing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import timedelta


def simulate_perturbations(data: Dict[str, pd.DataFrame], config: Dict[str, Any],
                           num_scenarios: int = 100) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation with ETA and service time perturbations
    
    Args:
        data: Loaded data
        config: Configuration
        num_scenarios: Number of scenarios to simulate
        
    Returns:
        Summary statistics
    """
    ships = data['ships'].copy()
    
    sim_config = config.get('simulation', {})
    eta_noise_hours = sim_config.get('eta_noise_hours', 2.0)
    service_variance = sim_config.get('service_time_variance', 0.15)
    
    # Store perturbed ETAs and service times
    eta_samples = []
    service_samples = []
    
    for scenario in range(num_scenarios):
        scenario_etas = []
        scenario_services = []
        
        for _, ship in ships.iterrows():
            # Perturb ETA (normal distribution)
            eta_delta_hours = np.random.normal(0, eta_noise_hours)
            perturbed_eta = ship['eta_iso'] + timedelta(hours=eta_delta_hours)
            scenario_etas.append(perturbed_eta)
            
            # Perturb service time (lognormal to ensure positive)
            service_multiplier = np.random.lognormal(0, service_variance)
            perturbed_service = ship['service_hours'] * service_multiplier
            scenario_services.append(perturbed_service)
        
        eta_samples.append(scenario_etas)
        service_samples.append(scenario_services)
    
    # Compute statistics
    eta_array = np.array([[eta.timestamp() for eta in scenario] for scenario in eta_samples])
    service_array = np.array(service_samples)
    
    # Mean delay from original ETA
    original_etas = np.array([ship['eta_iso'].timestamp() for _, ship in ships.iterrows()])
    mean_eta_delays = np.mean(eta_array - original_etas, axis=0) / 3600  # hours
    
    # Service time statistics
    mean_services = np.mean(service_array, axis=0)
    std_services = np.std(service_array, axis=0)
    
    summary = {
        'num_scenarios': num_scenarios,
        'ship_statistics': []
    }
    
    for idx, (_, ship) in enumerate(ships.iterrows()):
        summary['ship_statistics'].append({
            'ship_id': ship['ship_id'],
            'mean_eta_delay_hours': float(mean_eta_delays[idx]),
            'original_service_hours': float(ship['service_hours']),
            'mean_service_hours': float(mean_services[idx]),
            'std_service_hours': float(std_services[idx]),
        })
    
    return summary


if __name__ == "__main__":
    import sys
    import json
    from data_load import load_all, load_config
    
    inputs_dir = sys.argv[1] if len(sys.argv) > 1 else "inputs/"
    config_path = sys.argv[2] if len(sys.argv) > 2 else "config.yaml"
    
    print("Loading data...")
    data = load_all(inputs_dir)
    config = load_config(config_path)
    
    print("Running simulation...")
    summary = simulate_perturbations(data, config, num_scenarios=100)
    
    print(f"\nSimulated {summary['num_scenarios']} scenarios")
    print("\nShip statistics:")
    for stat in summary['ship_statistics']:
        print(f"  {stat['ship_id']}:")
        print(f"    Mean ETA delay: {stat['mean_eta_delay_hours']:.2f} hours")
        print(f"    Service time: {stat['original_service_hours']:.1f}h → "
              f"{stat['mean_service_hours']:.1f}h ± {stat['std_service_hours']:.1f}h")
    
    # Save to file
    with open('outputs/simulation_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("\n✓ Saved to outputs/simulation_summary.json")
