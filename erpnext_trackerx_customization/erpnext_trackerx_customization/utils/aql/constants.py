# -*- coding: utf-8 -*-
"""
AQL Constants and Lookup Tables

Industry standard constants for AQL calculations based on ISO 2859-1.
"""

from __future__ import unicode_literals

# Standard AQL values as per ISO 2859-1 (MIL-STD-105E)
# Complete industry standard AQL levels from strictest to most lenient
STANDARD_AQL_VALUES = [
    "0.065", "0.10", "0.15", "0.25", "0.40", "0.65", 
    "1.0", "1.5", "2.5", "4.0", "6.5", "10", "15", "25", "40", "65", "100", "150"
]

# Most commonly used AQL values in manufacturing
COMMON_AQL_VALUES = ["0.65", "1.0", "1.5", "2.5", "4.0", "6.5"]

# AQL value classifications by strictness level
AQL_STRICTNESS_LEVELS = {
    "Extremely Strict": ["0.065", "0.10", "0.15"],          # Safety-critical, high-precision
    "Very Strict": ["0.25", "0.40", "0.65"],               # Critical components, premium quality
    "Standard": ["1.0", "1.5", "2.5"],                     # General manufacturing, consumer products  
    "Lenient": ["4.0", "6.5", "10"],                       # Non-critical, cost-sensitive
    "Very Lenient": ["15", "25", "40"],                    # Basic quality, rough materials
    "Extremely Lenient": ["65", "100", "150"]              # Material classification, screening only
}

# Sample size code to sample size mapping
SAMPLE_SIZE_MAPPING = {
    'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20,
    'G': 32, 'H': 50, 'J': 80, 'K': 125, 'L': 200,
    'M': 315, 'N': 500, 'P': 800, 'Q': 1250, 'R': 2000
}

# Inspection levels
GENERAL_INSPECTION_LEVELS = ["1", "2", "3"]
SPECIAL_INSPECTION_LEVELS = ["S1", "S2", "S3", "S4"]
ALL_INSPECTION_LEVELS = GENERAL_INSPECTION_LEVELS + SPECIAL_INSPECTION_LEVELS

# Inspection regimes
INSPECTION_REGIMES = ["Normal", "Tightened", "Reduced"]

# Lot size to sample code mapping for different inspection levels
LOT_SIZE_RANGES = {
    # General Inspection Level I
    "1": {
        (2, 8): "A", (9, 15): "A", (16, 25): "B", (26, 50): "C",
        (51, 90): "C", (91, 150): "D", (151, 280): "E", (281, 500): "F",
        (501, 1200): "G", (1201, 3200): "H", (3201, 10000): "J",
        (10001, 35000): "K", (35001, 150000): "L", (150001, 500000): "M",
        (500001, 999999999): "N"
    },
    
    # General Inspection Level II (Standard)
    "2": {
        (2, 8): "A", (9, 15): "B", (16, 25): "C", (26, 50): "D",
        (51, 90): "E", (91, 150): "F", (151, 280): "G", (281, 500): "H",
        (501, 1200): "J", (1201, 3200): "K", (3201, 10000): "L",
        (10001, 35000): "M", (35001, 150000): "N", (150001, 500000): "P",
        (500001, 999999999): "Q"
    },
    
    # General Inspection Level III
    "3": {
        (2, 8): "B", (9, 15): "C", (16, 25): "D", (26, 50): "E",
        (51, 90): "F", (91, 150): "G", (151, 280): "H", (281, 500): "J",
        (501, 1200): "K", (1201, 3200): "L", (3201, 10000): "M",
        (10001, 35000): "N", (35001, 150000): "P", (150001, 500000): "Q",
        (500001, 999999999): "R"
    },
    
    # Special Inspection Levels (S1-S4 have same mapping)
    "S1": {
        (2, 90): "A", (91, 280): "B", (281, 500): "C", (501, 1200): "D",
        (1201, 3200): "E", (3201, 10000): "F", (10001, 35000): "G",
        (35001, 150000): "H", (150001, 500000): "J", (500001, 999999999): "K"
    },
    "S2": {
        (2, 90): "A", (91, 280): "B", (281, 500): "C", (501, 1200): "D",
        (1201, 3200): "E", (3201, 10000): "F", (10001, 35000): "G",
        (35001, 150000): "H", (150001, 500000): "J", (500001, 999999999): "K"
    },
    "S3": {
        (2, 90): "A", (91, 280): "B", (281, 500): "C", (501, 1200): "D",
        (1201, 3200): "E", (3201, 10000): "F", (10001, 35000): "G",
        (35001, 150000): "H", (150001, 500000): "J", (500001, 999999999): "K"
    },
    "S4": {
        (2, 90): "A", (91, 280): "B", (281, 500): "C", (501, 1200): "D",
        (1201, 3200): "E", (3201, 10000): "F", (10001, 35000): "G",
        (35001, 150000): "H", (150001, 500000): "J", (500001, 999999999): "K"
    }
}

# Default inspection regime
DEFAULT_INSPECTION_REGIME = "Normal"

# Default inspection level
DEFAULT_INSPECTION_LEVEL = "2"