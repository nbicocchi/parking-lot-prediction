import xlsxwriter
import os

def export_table(parking_lot_id: list ,values: dict, folder_path: str, file_name: str):
    """
    Export all values in xlsx format. 
    file_name DONT'T need the format 
    """
    workbook = xlsxwriter.Workbook(os.path.join(folder_path, f'{file_name}.xlsx'))
    worksheet = workbook.add_worksheet()
    row = 0
    col = 1
    #print columns 
    for value in parking_lot_id:
        worksheet.write(row, col, value)
        col += 1

    row = 1
    for key, item in values.items():
        col = 0
        #print header
        worksheet.write(row, col, key)
        #print all values for key values
        for value in item:
            col += 1
            worksheet.write(row, col, value)
        row+=1
    workbook.close()
    print("Exporting table complete!")