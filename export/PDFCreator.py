import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime, timezone, timedelta


def parseJSON():
    tableData = []
    counter = 0
    titles = []
    dataPDF = []
    
    # Load the JSON data from file
    with open('data3.json', 'r') as json_file:
        data = json.load(json_file)

    # Flatten the JSON data and create matrices with each key mapped to a list containing all its values
    flattened_data = flatten_json(data)
    key_matrix = {key: flattened_data[key] for key in flattened_data}

   
    for key, matrix in key_matrix.items():
        current = key.split('.')
        if (current[0] == "imports"):
            if (counter == 0):
                tableData = [['Class', 'Element']]
                counter = 1
                titles.append('Required Imports')
            else:
                for i in range(len(matrix)):
                    tableData.append([current[1], matrix[i]])
    dataPDF.append(tableData)

    tableData = []

    for key, matrix in key_matrix.items():
        counter = 0
        current = key.split('.')
        
        if (current[0] != "imports" and current[0] != "meta"):
            if (counter == 0 and (current[0] not in titles)):
                titles.append(current[0])
                dataPDF.append(tableData)
                tableData = []
                counter = 1
                tableData.append([current[1].capitalize(), matrix[0]])
            else:
                if (current[1] == 'revisions'):
                    continue
                elif(current[1] == 'lastupdated'):
                    input_format = "%Y%m%d%H%M"
                    parsed_date = datetime.strptime(matrix[0][:-1], input_format)

                    # Manually add the UTC timezone information
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)

                    # Define your desired output format
                    output_format = "%Y-%m-%d %H:%M:%S %Z"

                    # Convert the UTC time to the desired output format with timezone representation
                    formatted_date = parsed_date.strftime(output_format)
                    tableData.append([current[1].capitalize(), formatted_date])
                else:
                    for i in range(len(matrix)):
                        tableData.append([current[1].capitalize(), matrix[i]])
    dataPDF.append(tableData)                
    dataPDF.remove([])
    element = []
    for i in range(len(titles)):
        value = create_pdf_table(dataPDF[i], titles[i])
        element.append(value[0])
        element.append(value[1])
    makePDF(element)


def flatten_json(data, prefix=''):
    items = {}
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            items.update(flatten_json(value, prefix=new_prefix))
    elif isinstance(data, list):
        if prefix in items:
            items[prefix].extend(data)
        else:
            items[prefix] = data
    else:
        items[prefix] = [data]
    return items

def create_pdf_table(data, title, min_table_width = 200, max_table_width = 1000):
    
    elements = []

    # Add title to the PDF
    title_style = getSampleStyleSheet()["Title"]
    # Change the text color to red
    title_style.textColor = '#3b82f6'
    title_text = Paragraph(title, title_style)
    elements.append(title_text)

    available_width = max(min_table_width, min(max_table_width, max_table_width / len(data[0])))

    # Create the table with adjusted column widths
    table = Table(data, colWidths=[available_width / len(data[0])] * len(data[0]))
    

  
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#3b82f6'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('WORDWRAP', (0, 0), (-1, -1), 'TRUE'), 
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, '#C8C8C8'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ])
    table.setStyle(style)

    
    elements.append(table)
    return elements
    

def makePDF(dataWrite):
    doc = SimpleDocTemplate("table.pdf", pagesize=letter)
    doc.build(dataWrite)

if __name__ == "__main__":
    parseJSON()