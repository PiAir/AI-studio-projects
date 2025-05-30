import os
import subprocess
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
JSON_OUTPUT_FOLDER = 'json_outputs' # << NIEUWE MAPCONFIGURATIE
ALLOWED_EXTENSIONS = {'png'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER # << NIEUWE MAPCONFIGURATIE
app.secret_key = 'supersecretkey'

# Maak de mappen als ze niet bestaan
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(JSON_OUTPUT_FOLDER): # << NIEUWE MAP AANMAKEN
    os.makedirs(JSON_OUTPUT_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Geen bestanddeel in het request')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('Geen bestand geselecteerd')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename) # Bewaar originele bestandsnaam voor JSON
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(filepath)

        c2pa_data_json_string = None # Dit wordt de string voor weergave en opslag
        error_message = None
        json_filename_to_save = original_filename + '.json' # bv. image.png.json

        try:
            c2patool_path = '/usr/local/bin/c2patool'
            process = subprocess.run(
                [c2patool_path, filepath],
                capture_output=True,
                text=True,
                check=False
            )

            if process.returncode == 0:
                raw_json_output = process.stdout
                try:
                    # Parseer en formatteer voor nette weergave en opslag
                    parsed_json = json.loads(raw_json_output)
                    c2pa_data_json_string = json.dumps(parsed_json, indent=4)

                    # Sla de geformatteerde JSON op
                    json_save_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename_to_save)
                    with open(json_save_path, 'w') as f_json:
                        f_json.write(c2pa_data_json_string)

                except json.JSONDecodeError:
                    # Als het geen valide JSON is, toon en sla het op zoals het is (minder waarschijnlijk nu het werkt)
                    c2pa_data_json_string = raw_json_output
                    error_message = "Output van c2patool was geen valide JSON, maar wordt wel getoond."
                    # Sla de ruwe output op als het geen JSON is
                    json_save_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename_to_save)
                    with open(json_save_path, 'w') as f_json: # Overschrijf met ruwe data
                        f_json.write(raw_json_output)


            else:
                error_output = process.stderr or process.stdout
                if "No C2PA marker found" in error_output or "No manifest found" in error_output:
                    error_message = "Geen C2PA-manifest gevonden in het bestand."
                else:
                    error_message = f"c2patool fout (code {process.returncode}): {error_output}"
                if not error_output.strip():
                    error_message = f"c2patool gaf een foutcode {process.returncode} zonder specifieke melding."

        except FileNotFoundError:
            error_message = f"c2patool uitvoerbaar bestand niet gevonden op: {c2patool_path}. Controleer de Dockerfile."
        except PermissionError:
            error_message = f"Permissie geweigerd bij uitvoeren van {c2patool_path}. Controleer bestandspermissies in de container."
        except Exception as e:
            error_message = f"Een onverwachte fout is opgetreden: {str(e)}"

        return render_template('index.html',
                               filename=original_filename, # Dit is de PNG bestandsnaam
                               c2pa_data=c2pa_data_json_string,
                               json_download_filename=json_filename_to_save if c2pa_data_json_string and not error_message else None, # Geef JSON bestandsnaam door voor downloadlink
                               error=error_message)

    flash('Ongeldig bestandstype, alleen PNG is toegestaan.')
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# << NIEUWE ROUTE VOOR DOWNLOADEN JSON >>
@app.route('/download_json/<json_filename>')
def download_json(json_filename):
    try:
        return send_from_directory(app.config['JSON_OUTPUT_FOLDER'],
                                   json_filename,
                                   as_attachment=True,
                                   mimetype='application/json')
    except FileNotFoundError:
        flash(f"JSON-bestand {json_filename} niet gevonden voor download.", "error")
        # Redirect naar de hoofdpagina, of toon een 404-pagina
        # We moeten de oorspronkelijke PNG-naam ergens vandaan halen om de pagina correct te renderen,
        # wat lastig is als we alleen de json_filename hebben.
        # Een simpele redirect is misschien het beste.
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)