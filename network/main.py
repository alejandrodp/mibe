import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, flash, redirect, url_for, send_from_directory
from pysmi.codegen import PySnmpCodeGen, JsonCodeGen
from pysmi.compiler import MibCompiler
from pysmi.parser import SmiV2Parser
from pysmi.reader import getReadersFromUrls
from pysmi.searcher import StubSearcher
from pysmi.writer import FileWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'upload'

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def is_zip(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['zip']


@app.route('/upload_mib', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        files = [filename]
        zipe = is_zip(filename)
        if zipe:
            zipe = zipfile.ZipFile(f'{filename}.zip')
            files = zipe.namelist()
        compile(files)
        for fil in files:
            path = Path(f'{app.config["UPLOAD_FOLDER"]}/{fil}').stem
            process_mib_parsed(f'parsed/{path}.json')

        for fil in files:
            path = Path(f'{app.config["UPLOAD_FOLDER"]}/{fil}').stem
            print(path)
            parseJSON(f'parsed/{path}.json')

        return redirect(url_for('upload_file', name=filename))
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=submit value=Upload>
        </form>
        '''


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory("parsed", name)


def compile(inputMibs):
    srcDir = [app.config["UPLOAD_FOLDER"], 'mibs.zip']  # we will read MIBs from here

    # Initialize compiler infrastructure

    mibCompiler = MibCompiler(
        SmiV2Parser(),
        JsonCodeGen(),
        # out own callback function stores results in its own way
        FileWriter(os.path.join('./parsed')).setOptions(suffix='.json')
    )

    # our own callback function serves as a MIB source here
    mibCompiler.addSources(
        *getReadersFromUrls(
            *srcDir, **dict(fuzzyMatching=True)
        )
    )

    # never recompile MIBs with MACROs
    mibCompiler.addSearchers(StubSearcher(*PySnmpCodeGen.baseMibs))

    # run non-recursive MIB compilation
    results = mibCompiler.compile(*inputMibs, **dict(noDeps=False,
                                                     rebuild=True,
                                                     genTexts=True))

    mibCompiler.buildIndex(results, ignoreErrors=True)


def parseJSON(filename):
    tableData = []
    counter = 0
    titles = []
    dataPDF = []

    # Load the JSON data from file
    with open(filename, 'r') as json_file:
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
                elif (current[1] == 'lastupdated'):
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
    makePDF(element, filename)


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


def create_pdf_table(data, title):
    elements = []

    # Add title to the PDF
    title_style = getSampleStyleSheet()["Title"]
    # Change the text color to red
    title_style.textColor = colors.red
    title_text = Paragraph(title, title_style)
    elements.append(title_text)

    # Create the table
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ])
    table.setStyle(style)
    elements.append(table)
    return elements


def makePDF(dataWrite, filename):
    doc = SimpleDocTemplate(f'{filename}.pdf', pagesize=letter)
    doc.build(dataWrite)


# Function to build a hierarchical tree from MIB data
def build_tree(data, root, processed=set(), ignored_objects=[]):
    if root in processed or "oid" not in data[root]:
        return None

    processed.add(root)

    data[root]["children"] = []

    tree = data[root]

    # tree = {
    #     "name": data[root].get("name", ""),
    #     "oid": data[root].get("oid", ""),
    #     "class": data[root].get("class", ""),
    #     "description": data[root].get("description", ""),
    #     "children": []
    # }

    for key, value in data.items():
        if key != root and value.get("oid", "").startswith(data[root]["oid"]) and value["oid"][
            len(data[root]["oid"])] == ".":
            subtree = build_tree(data, key, processed, ignored_objects)
            if subtree is not None:
                tree["children"].append(subtree)
        if "oid" not in value and value not in ignored_objects:
            ignored_objects.append(value)
    return tree


# Function to process a MIB file and return its data as a dictionary
def process_mib(mib_file):
    try:
        with open(mib_file, "r") as file:
            data_json = file.read()
            data_json = data_json.replace("\\", "")
            data = json.loads(data_json)
            return data
    except FileNotFoundError:
        raise Exception("The MIB file is not found.")
    except json.JSONDecodeError:
        raise Exception("The MIB file is not a valid JSON.")


# Function to process a MIB file and build a JSON representation of the hierarchical tree
def process_mib_to_json(mib_file):
    data = process_mib(mib_file)
    root_node = "arubaWiredFan"
    tree = build_tree(data, root_node)
    return tree


# Function to write the result (tree and ignored objects) to a JSON file
def write_result_to_json(output_file, result):
    result_json = json.dumps(result, indent=2)
    with open(output_file, "w") as file:
        file.write(result_json)


def process_mib_parsed(input_mib):
    tree = process_mib_to_json(input_mib)

    result = {
        "tree": tree
    }

    output_file = input_mib.replace(".json", "_tree.json")
    write_result_to_json(output_file, result)
