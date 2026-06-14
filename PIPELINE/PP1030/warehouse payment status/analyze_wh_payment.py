import pandas as pd

xl = pd.ExcelFile('wh payment.xlsx')
df = pd.read_excel(xl, sheet_name=1)  # Use Merged Data (2) sheet

print('=== wh payment.xlsx Analysis ===')
print(f'Total records: {len(df)}')
print()

# Check Operation Month distribution
print('Operation Month distribution:')
print(df['Operation Month'].value_counts().sort_index())
print()

# Check Sqm and Amount relationship
sqm_count = (df['Sqm'] > 0).sum()
print(f'Sqm > 0 records: {sqm_count}')
total_sqm = df['Sqm'].sum()
total_amount = df['Amount'].sum()
total_total = df['TOTAL'].sum()
print(f'Total Sqm: {total_sqm:.2f}')
print(f'Total Amount: {total_amount:.2f}')
print(f'Total TOTAL: {total_total:.2f}')
print()

# Monthly totals
print('Monthly Sqm totals:')
monthly = df.groupby('Operation Month').agg({
    'Sqm': 'sum',
    'Amount': 'sum',
    'TOTAL': 'sum'
})
print(monthly)
print()

# Check HVDC CODE 2 (Vendor) structure
print('HVDC CODE 2 (Vendor) distribution:')
print(df['HVDC CODE 2'].value_counts())
print()

# Check IN AND OUT categories
print('IN AND OUT categories:')
print(df['IN AND OUT'].value_counts())
