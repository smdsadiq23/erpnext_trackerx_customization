#!/usr/bin/env python3
"""
AQL Table Generator

Generates complete industry-standard AQL table data according to ISO 2859-1.
Creates acceptance/rejection criteria for all sample code and AQL value combinations.
"""

import json

# Industry standard AQL acceptance/rejection table
# Based on ISO 2859-1 (MIL-STD-105E)
AQL_TABLE_DATA = {
    # Sample Code A (n=2)
    'A': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '2.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '4.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '6.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
    },
    
    # Sample Code B (n=3)
    'B': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '2.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '4.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '6.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
    },
    
    # Sample Code C (n=5)
    'C': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '2.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '4.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '6.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
    },
    
    # Sample Code D (n=8)
    'D': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '2.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '4.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '6.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '10': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '15': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 1, 're': 2}},
        '25': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 1, 're': 2}},
    },
    
    # Sample Code E (n=13)
    'E': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.5': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '2.5': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '4.0': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 1, 're': 2}},
        '6.5': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '10': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '15': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '25': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '40': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 4, 're': 5}},
    },
    
    # Sample Code F (n=20)
    'F': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.5': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '2.5': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 1, 're': 2}},
        '4.0': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '6.5': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '10': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '15': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '25': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '40': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '65': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code G (n=32) 
    'G': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.5': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '2.5': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '4.0': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '6.5': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '10': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '15': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '25': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '40': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '65': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code H (n=50)
    'H': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '1.0': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '1.5': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '2.5': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '4.0': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '6.5': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '10': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '15': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '25': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '40': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code J (n=80)
    'J': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.65': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '1.0': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '1.5': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '2.5': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '4.0': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '6.5': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '10': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '15': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '25': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code K (n=125)
    'K': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.40': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '0.65': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '1.0': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '1.5': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '2.5': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '4.0': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '6.5': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '10': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '15': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code L (n=200)
    'L': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.25': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '0.40': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '0.65': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '1.0': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '1.5': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '2.5': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '4.0': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '6.5': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '10': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code M (n=315)
    'M': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.15': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '0.25': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '0.40': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '0.65': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '1.0': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '1.5': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '2.5': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '4.0': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '6.5': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code N (n=500)
    'N': {
        '0.065': {'normal': {'ac': 0, 're': 1}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 0, 're': 1}},
        '0.10': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '0.15': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '0.25': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '0.40': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '0.65': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '1.0': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '1.5': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '2.5': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '4.0': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code P (n=800)
    'P': {
        '0.065': {'normal': {'ac': 1, 're': 2}, 'tightened': {'ac': 0, 're': 1}, 'reduced': {'ac': 1, 're': 2}},
        '0.10': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '0.15': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '0.25': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '0.40': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '0.65': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '1.0': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '1.5': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '2.5': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code Q (n=1250)
    'Q': {
        '0.065': {'normal': {'ac': 2, 're': 3}, 'tightened': {'ac': 1, 're': 2}, 'reduced': {'ac': 2, 're': 3}},
        '0.10': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '0.15': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '0.25': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '0.40': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '0.65': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '1.0': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '1.5': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    },
    
    # Sample Code R (n=2000)
    'R': {
        '0.065': {'normal': {'ac': 3, 're': 4}, 'tightened': {'ac': 2, 're': 3}, 'reduced': {'ac': 3, 're': 4}},
        '0.10': {'normal': {'ac': 5, 're': 6}, 'tightened': {'ac': 3, 're': 4}, 'reduced': {'ac': 5, 're': 6}},
        '0.15': {'normal': {'ac': 7, 're': 8}, 'tightened': {'ac': 5, 're': 6}, 'reduced': {'ac': 7, 're': 8}},
        '0.25': {'normal': {'ac': 10, 're': 11}, 'tightened': {'ac': 7, 're': 8}, 'reduced': {'ac': 10, 're': 11}},
        '0.40': {'normal': {'ac': 14, 're': 15}, 'tightened': {'ac': 10, 're': 11}, 'reduced': {'ac': 14, 're': 15}},
        '0.65': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 14, 're': 15}, 'reduced': {'ac': 21, 're': 22}},
        '1.0': {'normal': {'ac': 21, 're': 22}, 'tightened': {'ac': 21, 're': 22}, 'reduced': {'ac': 21, 're': 22}},
    }
}

# Sample size mapping
SAMPLE_SIZES = {
    'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20, 'G': 32, 'H': 50,
    'J': 80, 'K': 125, 'L': 200, 'M': 315, 'N': 500, 'P': 800, 'Q': 1250, 'R': 2000
}

def generate_aql_table_fixtures():
    """Generate complete AQL table fixtures"""
    
    fixtures = []
    
    print("Generating complete AQL table fixtures...")
    
    for code, aql_data in AQL_TABLE_DATA.items():
        sample_size = SAMPLE_SIZES[code]
        
        for aql_value, regimes in aql_data.items():
            for regime_key, criteria in regimes.items():
                regime = regime_key.title()  # Convert 'normal' to 'Normal'
                
                fixture = {
                    "docstatus": 0,
                    "doctype": "AQL Table",
                    "sample_code_letter": code,
                    "sample_size": sample_size,
                    "aql_value": aql_value,
                    "inspection_regime": regime,
                    "acceptance_number": criteria['ac'],
                    "rejection_number": criteria['re'],
                    "is_active": 1
                }
                
                fixtures.append(fixture)
    
    print(f"Generated {len(fixtures)} AQL table entries")
    return fixtures

def main():
    """Main function to generate and save AQL table data"""
    
    # Generate fixtures
    fixtures = generate_aql_table_fixtures()
    
    # Save to JSON file
    output_file = "erpnext_trackerx_customization/erpnext_trackerx_customization/fixtures/aql_table.json"
    
    with open(output_file, 'w') as f:
        json.dump(fixtures, f, indent=1)
    
    print(f"✅ Complete AQL table data saved to {output_file}")
    print(f"📊 Total entries: {len(fixtures)}")
    
    # Print summary
    sample_codes = set()
    aql_values = set()
    regimes = set()
    
    for fixture in fixtures:
        sample_codes.add(fixture['sample_code_letter'])
        aql_values.add(fixture['aql_value'])
        regimes.add(fixture['inspection_regime'])
    
    print(f"📋 Sample Codes: {sorted(sample_codes)}")
    print(f"🎯 AQL Values: {sorted(aql_values, key=float)}")
    print(f"⚙️ Inspection Regimes: {sorted(regimes)}")

if __name__ == "__main__":
    main()