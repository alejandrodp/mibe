import json
import os
from pathlib import Path

from flask import Flask, request, jsonify, flash, redirect, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS

UPLOAD_FOLDER = '.'

app = Flask(__name__)
CORS(app)

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def is_zip(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['zip']


@app.route('/mib/upload', methods=['GET', 'POST'])
def upload_mib():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify(json.load(open(Path("mockups", "upload_mib.json"))))
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=submit value=Upload>
        </form>
        '''


@app.route('/search/<term>', methods=['GET'])
def search_oid(term):
    args = request.args
    print(args)
    print(term)
    return jsonify(json.load(open(Path("mockups", "search.json"))))


@app.route('/mib/download/<mibid>', methods=['GET'])
def download_pdf(mibid):
    print(mibid)
    return send_from_directory(Path("mockups"), "example.pdf")


@app.route('/vendor', methods=['GET'])
def vendor():
    return jsonify({
        "34578": "hpe",
        "632": "aruba",
        "54345": "cisco",
        "65346546": "ibm",
    })
