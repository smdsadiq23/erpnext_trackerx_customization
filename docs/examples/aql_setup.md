# AQL System Setup Guide

This guide walks you through setting up the AQL (Accepted Quality Level) system for quality inspection.

## Prerequisites

- ERPNext TrackerX Customization app installed
- Administrator or System Manager role
- Basic understanding of quality control processes

## Step 1: Configure AQL Master Data

### 1.1 AQL Levels
Create inspection levels in **AQL Level** doctype:

```
Level Code: 1    | Type: General | Description: General Level I
Level Code: 2    | Type: General | Description: General Level II  
Level Code: 3    | Type: General | Description: General Level III
Level Code: S1   | Type: Special | Description: Special Level S-1
Level Code: S2   | Type: Special | Description: Special Level S-2
Level Code: S3   | Type: Special | Description: Special Level S-3
Level Code: S4   | Type: Special | Description: Special Level S-4
```

### 1.2 AQL Standards  
Create quality levels in **AQL Standard** doctype:

```
AQL Value: 0.65  | Description: 0.65% defective - Strict quality
AQL Value: 1.0   | Description: 1.0% defective - Standard quality
AQL Value: 2.5   | Description: 2.5% defective - Standard quality
AQL Value: 4.0   | Description: 4.0% defective - Lenient quality
```

### 1.3 AQL Table
Create acceptance/rejection criteria in **AQL Table** doctype:

```
Sample Code: H | Sample Size: 50  | AQL: 2.5 | Regime: Normal | Accept: 3 | Reject: 4
Sample Code: J | Sample Size: 80  | AQL: 2.5 | Regime: Normal | Accept: 5 | Reject: 6
Sample Code: K | Sample Size: 125 | AQL: 2.5 | Regime: Normal | Accept: 7 | Reject: 8
```

## Step 2: Configure Items

For each item that requires AQL inspection:

1. Go to **Item** list
2. Open the item
3. In the **AQL Configuration** section:
   - **Inspection Level**: Select appropriate level (e.g., "2")
   - **Inspection Regime**: Select "Normal", "Tightened", or "Reduced"  
   - **Accepted Quality Level**: Select AQL value (e.g., "2.5")

## Step 3: Material Inspection Workflow

### 3.1 Goods Receipt
1. Create **Goods Receipt Note** for incoming materials
2. System automatically creates **Material Inspection Report**

### 3.2 Quality Inspection  
1. Open **Material Inspection Report**
2. For each item in **MIR Items** table:
   - System auto-calculates **Sample Size** based on received quantity
   - System sets **Acceptance Number** and **Rejection Number** from AQL Table
   - Inspector enters **Defects Found** during physical inspection
   - System auto-determines **Inspection Result** (Accepted/Rejected)
   - System auto-populates **Accepted Qty** and **Rejected Qty**

## Step 4: Verification

Test the setup with a sample batch:
- Received Quantity: 500
- Expected Sample Code: H  
- Expected Sample Size: 50
- Expected Accept ≤ 3, Reject ≥ 4

## Troubleshooting

**Issue**: "Item does not have complete AQL configuration"
**Solution**: Ensure all three AQL fields are set on the Item

**Issue**: "No AQL table entry found" 
**Solution**: Create AQL Table entry for the specific sample code and AQL value combination

**Issue**: Sample size not calculating
**Solution**: Check that AQL Level exists and has correct level_code