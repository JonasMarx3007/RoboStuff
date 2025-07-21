import pandas as pd
from tkinter import Tk, filedialog, messagebox
import os
import string
import sys

def generate_plate_positions(rows=8, cols=12):
    row_labels = list(string.ascii_uppercase[:rows])
    col_labels = list(range(1, cols + 1))
    return [f"{row}{col}" for col in col_labels for row in row_labels]

def alert_and_exit(message, title="Info"):
    root = Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    os._exit(0)

def error_and_exit(message, title="Error"):
    root = Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    os._exit(1)

def process_plate_excel():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select an Excel plate file", filetypes=[("Excel files", "*.xlsx *.xls")])
    if not file_path:
        alert_and_exit("No file selected.", "Cancelled")

    df = pd.read_excel(file_path)
    df.rename(columns={df.columns[0]: 'Row'}, inplace=True)
    df_long = df.melt(id_vars='Row', var_name='Column', value_name='Value').dropna().reset_index(drop=True)
    df_long['Sample'] = df_long.index + 1
    df_long['SourceWellSample'] = df_long['Row'] + df_long['Column'].astype(str)
    df_long['volumeSample'] = 10 / df_long['Value']

    invalid_mask = (df_long['volumeSample'] < 1) | (df_long['volumeSample'] > 30)
    if invalid_mask.any():
        invalid_wells = df_long.loc[invalid_mask, 'SourceWellSample'].tolist()
        well_list = ', '.join(invalid_wells)
        error_and_exit(f"The following wells have invalid volumeSample values (<1 or >30):\n{well_list}", "Invalid volumeSample")

    df_long['volumeWater'] = 30 - df_long['volumeSample']
    df_long['SourceWellWater'] = 'A1'

    plate_positions = generate_plate_positions()
    if len(df_long) > len(plate_positions):
        error_and_exit(f"Too many samples ({len(df_long)}). Max for 96-well plate is {len(plate_positions)}.", "Plate Overflow")

    df_long['TargetWellWater'] = plate_positions[:len(df_long)]
    df_long['TargetWellSample'] = plate_positions[:len(df_long)]

    output_df = pd.DataFrame({
        'Sample': df_long['Sample'],
        'volumeWater': df_long['volumeWater'].round(1).astype(str),
        'SourceWellWater': df_long['SourceWellWater'],
        'TargetWellWater': df_long['TargetWellWater'],
        'volumeSample': df_long['volumeSample'].round(1).astype(str),
        'SourceWellSample': df_long['SourceWellSample'],
        'TargetWellSample': df_long['TargetWellSample']
    })

    headers = output_df.columns.tolist()
    lines = ['; '.join(headers)] + ['; '.join([str(row[col]) for col in headers]) for _, row in output_df.iterrows()]
    output_file = os.path.join(os.path.dirname(file_path), 'S1_Parameter.txt')

    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))

    alert_and_exit(f"Output successfully written to:\n{output_file}", "Success")

if __name__ == "__main__":
    process_plate_excel()
