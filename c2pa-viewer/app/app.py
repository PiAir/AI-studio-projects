import os
import subprocess
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
JSON_OUTPUT_FOLDER = 'json_outputs'
ALLOWED_EXTENSIONS = {'png'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER
app.secret_key = 'supersecretkey'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(JSON_OUTPUT_FOLDER):
    os.makedirs(JSON_OUTPUT_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_c2pa_summary(parsed_json_data):
    """Genereert een eenvoudige samenvatting van C2PA data."""
    summary_points = []
    try:
        if not parsed_json_data or "manifests" not in parsed_json_data:
            return ["Geen valide C2PA manifest data gevonden voor samenvatting."]

        # Probeer informatie uit het actieve manifest te halen
        active_manifest_label = parsed_json_data.get("active_manifest")
        if not active_manifest_label or active_manifest_label not in parsed_json_data["manifests"]:
            # Val terug op het eerste manifest als actieve niet (goed) is gespecificeerd
            if parsed_json_data["manifests"]:
                active_manifest_label = list(parsed_json_data["manifests"].keys())[0]
            else:
                 return ["Geen manifesten gevonden in de data."]


        manifest = parsed_json_data["manifests"].get(active_manifest_label, {})

        # 1. Claim generator
        claim_generator = manifest.get("claim_generator_info", [{}])[0].get("name")
        if claim_generator:
            summary_points.append(f"Referenties afgegeven door: {claim_generator}")

        # 2. Acties - zoek naar "created" en "softwareAgent"
        actions_assertion = next((a for a in manifest.get("assertions", []) if a.get("label") == "c2pa.actions.v2"), None)
        if actions_assertion and "data" in actions_assertion and "actions" in actions_assertion["data"]:
            for action_item in actions_assertion["data"]["actions"]:
                action_type = action_item.get("action")
                software_agent = action_item.get("softwareAgent", {}).get("name")
                digital_source_type = action_item.get("digitalSourceType")

                if action_type == "c2pa.created":
                    if software_agent:
                        summary_points.append(f"Gemaakt met: {software_agent}")
                    if digital_source_type and "trainedAlgorithmicMedia" in digital_source_type:
                        summary_points.append("Mogelijk (volledig) gegenereerd door AI.")
                elif software_agent: # Voor andere acties zoals "converted", "edited"
                    summary_points.append(f"Bewerkt/geconverteerd met: {software_agent}")
        
        # 3. Issuer van de signature
        issuer = manifest.get("signature_info", {}).get("issuer")
        if issuer and issuer != claim_generator : # Voeg alleen toe als het nieuwe info is
            summary_points.append(f"Handtekening uitgever: {issuer}")


        if not summary_points:
            return ["Geen directe samenvattingspunten gevonden, bekijk de volledige JSON."]

        return summary_points

    except Exception as e:
        # print(f"Error generating summary: {e}") # Voor debuggen
        return [f"Kon geen samenvatting genereren (fout: {type(e).__name__}). Bekijk de volledige JSON."]


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
        original_filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(filepath)

        c2pa_data_json_string = None
        c2pa_summary_points = None # << NIEUW
        error_message = None
        json_filename_to_save = original_filename + '.json'

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
                    parsed_json = json.loads(raw_json_output)
                    c2pa_data_json_string = json.dumps(parsed_json, indent=4)
                    c2pa_summary_points = generate_c2pa_summary(parsed_json) # << GENEREER SAMENVATTING

                    json_save_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename_to_save)
                    with open(json_save_path, 'w') as f_json:
                        f_json.write(c2pa_data_json_string)
                except json.JSONDecodeError:
                    c2pa_data_json_string = raw_json_output
                    error_message = "Output van c2patool was geen valide JSON, maar wordt wel getoond."
                    json_save_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename_to_save)
                    with open(json_save_path, 'w') as f_json:
                        f_json.write(raw_json_output)
            else:
                error_output = process.stderr or process.stdout
                if "No C2PA marker found" in error_output or "No manifest found" in error_output:
                    error_message = "Geen C2PA-manifest gevonden in het bestand."
                else:
                    error_message = f"c2patool fout (code {process.returncode}): {error_output}"
                if not error_output.strip():
                    error_message = f"c2patool gaf een foutcode {process.returncode} zonder specifieke melding."
        # ... (rest van except blokken blijven hetzelfde) ...
        except FileNotFoundError:
            error_message = f"c2patool uitvoerbaar bestand niet gevonden op: {c2patool_path}. Controleer de Dockerfile."
        except PermissionError:
            error_message = f"Permissie geweigerd bij uitvoeren van {c2patool_path}. Controleer bestandspermissies in de container."
        except Exception as e:
            error_message = f"Een onverwachte fout is opgetreden: {str(e)}"


        return render_template('index.html',
                               filename=original_filename,
                               c2pa_data=c2pa_data_json_string,
                               c2pa_summary=c2pa_summary_points, # << GEEF SAMENVATTING DOOR
                               json_download_filename=json_filename_to_save if c2pa_data_json_string and not error_message else None,
                               error=error_message)

    flash('Ongeldig bestandstype, alleen PNG is toegestaan.')
    return redirect(url_for('index'))

@app.route('/', methods=['GET']) # Moet boven upload_file staan of default render template index() aanroepen
def index_get():
    return render_template('index.html')


@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download_json/<json_filename>')
def download_json(json_filename):
    try:
        return send_from_directory(app.config['JSON_OUTPUT_FOLDER'],
                                   json_filename,
                                   as_attachment=True,
                                   mimetype='application/json')
    except FileNotFoundError:
        flash(f"JSON-bestand {json_filename} niet gevonden voor download.", "error")
        return redirect(url_for('index_get')) # Verwijs naar de GET route voor index

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)