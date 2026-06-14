#!/usr/bin/env python3
"""
OFCO Manpower Analysis Script
Analyzes manpower charges from Excel file and categorizes successful/failed records
"""

import pandas as pd
import re
from datetime import datetime
import sys

def analyze_manpower_data():
    """Main analysis function for OFCO manpower data"""
    
    print("=== OFCO MANPOWER ANALYSIS ===")
    print(f"Analysis started at: {datetime.now()}")
    print("-" * 50)
    
    try:
        # Load data from Excel file
        print("Loading data from 'ofco all.xlsx'...")
        df = pd.read_excel('ofco all.xlsx', sheet_name='Manpower')
        print(f"✓ Successfully loaded {len(df)} records")
        
        # Enhanced regex pattern for manpower extraction
        # Pattern captures: count, role, date, hours, rate
        pattern = r'Manpower.*?(\d+).*?([A-Za-z\s]+?).*?(\d{1,2}-[A-Za-z]{3}-\d{4}).*?(\d+(?:\.\d+)?)\s*hrs.*?AED\s*(\d+(?:\.\d+)?)'
        
        successful_records = []
        failed_records = []
        
        print("\nProcessing records...")
        
        # Process each row
        for index, row in df.iterrows():
            subject = str(row.get('SUBJECT', ''))
            
            # Check if record contains manpower
            if 'manpower' in subject.lower():
                match = re.search(pattern, subject, re.IGNORECASE)
                
                if match:
                    # Extract matched groups
                    count = int(match.group(1))
                    role = match.group(2).strip()
                    date = match.group(3)
                    hours = float(match.group(4))
                    rate = float(match.group(5))
                    
                    # Calculate total cost
                    total_cost = count * hours * rate
                    
                    # Store successful record
                    successful_records.append({
                        'Row': index + 1,
                        'Subject': subject,
                        'Count': count,
                        'Role': role,
                        'Date': date,
                        'Hours': hours,
                        'Rate_AED': rate,
                        'Total_Cost': total_cost
                    })
                else:
                    # Store failed record
                    failed_records.append({
                        'Row': index + 1,
                        'Subject': subject,
                        'Reason': 'Regex pattern did not match manpower format'
                    })
        
        # Print summary
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Total records processed: {len(df)}")
        print(f"Successful extractions: {len(successful_records)}")
        print(f"Failed extractions: {len(failed_records)}")
        print(f"Success rate: {len(successful_records)/len(df)*100:.1f}%")
        
        if successful_records:
            total_cost = sum(record['Total_Cost'] for record in successful_records)
            total_personnel = sum(record['Count'] for record in successful_records)
            total_hours = sum(record['Hours'] * record['Count'] for record in successful_records)
            
            print(f"\n=== FINANCIAL SUMMARY ===")
            print(f"Total cost: AED {total_cost:,.2f}")
            print(f"Total personnel: {total_personnel}")
            print(f"Total hours: {total_hours:,.1f}")
            print(f"Average rate: AED {total_cost/total_hours:.2f}/hour")
        
        # Save results to Excel
        print(f"\nSaving results to 'OFCO_Manpower_Analysis_Results.xlsx'...")
        
        with pd.ExcelWriter('OFCO_Manpower_Analysis_Results.xlsx', engine='openpyxl') as writer:
            # Successful records sheet
            if successful_records:
                success_df = pd.DataFrame(successful_records)
                success_df.to_excel(writer, sheet_name='Successful_Records', index=False)
            
            # Failed records sheet
            if failed_records:
                failed_df = pd.DataFrame(failed_records)
                failed_df.to_excel(writer, sheet_name='Failed_Records', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': ['Total Records', 'Successful Records', 'Failed Records', 
                          'Success Rate (%)', 'Total Cost (AED)', 'Total Personnel', 'Total Hours'],
                'Value': [len(df), len(successful_records), len(failed_records),
                         round(len(successful_records)/len(df)*100, 1),
                         round(total_cost, 2) if successful_records else 0,
                         total_personnel if successful_records else 0,
                         round(total_hours, 1) if successful_records else 0]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print("✓ Analysis completed successfully!")
        print("✓ Results saved to 'OFCO_Manpower_Analysis_Results.xlsx'")
        
        # Display sample successful records
        if successful_records:
            print(f"\n=== SAMPLE SUCCESSFUL RECORDS ===")
            for i, record in enumerate(successful_records[:3]):
                print(f"{i+1}. {record['Count']} {record['Role']} - {record['Hours']}hrs @ AED{record['Rate_AED']} = AED{record['Total_Cost']:.2f}")
        
        # Display sample failed records
        if failed_records:
            print(f"\n=== SAMPLE FAILED RECORDS ===")
            for i, record in enumerate(failed_records[:3]):
                print(f"{i+1}. Row {record['Row']}: {record['Subject'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    analyze_manpower_data()