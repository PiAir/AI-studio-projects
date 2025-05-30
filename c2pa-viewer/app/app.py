import os
import subprocess
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
JSON_OUTPUT_FOLDER = 'json_outputs' # Map voor opgeslagen JSON
ALLOWED_EXTENSIONS = {'png'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER
app.secret_key = 'supersecretkey'

# Maak de mappen als ze niet bestaan
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

        active_manifest_label = parsed_json_data.get("active_manifest")
        manifest_data_to_parse = None

        if active_manifest_label and active_manifest_label in parsed_json_data["manifests"]:
            manifest_data_to_parse = parsed_json_data["manifests"][active_manifest_label]
        elif parsed_json_data["manifests"]: # Val terug op het eerste manifest
            first_manifest_key = list(parsed_json_data["manifests"].keys())[0]
            manifest_data_to_parse = parsed_json_data["manifests"][first_manifest_key]
        
        if not manifest_data_to_parse:
            return ["Geen manifesten gevonden in de data."]

        # 1. Claim generator
        claim_generator_info = manifest_data_to_parse.get("claim_generator_info")
        if isinstance(claim_generator_info, list) and claim_generator_info:
            claim_generator_name = claim_generator_info[0].get("name")
            if claim_generator_name:
                summary_points.append(f"Referenties afgegeven door: {claim_generator_name}")

        # 2. Acties
        assertions = manifest_data_to_parse.get("assertions", [])
        actions_assertion = next((a for a in assertions if a.get("label") == "c2pa.actions.v2"), None)
        if actions_assertion and isinstance(actions_assertion.get("data"), dict) and isinstance(actions_assertion["data"].get("actions"), list):
            for action_item in actions_assertion["data"]["actions"]:
                if isinstance(action_item, dict):
                    action_type = action_item.get("action")
                    software_agent_name = action_item.get("softwareAgent", {}).get("name")
                    digital_source_type = action_item.get("digitalSourceType")

                    if action_type == "c2pa.created":
                        if software_agent_name:
                            summary_points.append(f"Gemaakt met: {software_agent_name}")
                        else: # Soms is er geen softwareAgent maar wel direct een digitalSourceType
                             summary_points.append(f"Gemaakt (bron: {digital_source_type or 'onbekend'})")

                        if digital_source_type and "trainedAlgorithmicMedia" in digital_source_type:
                            summary_points.append("AI is gebruikt om afbeelding (mogelijk volledig) te genereren.")
                    
                    elif software_agent_name : # Voor andere acties zoals "converted", "edited"
                        action_verb = action_type.split('.')[-1] if action_type else "bewerkt"
                        summary_points.append(f"Afbeelding {action_verb} met: {software_agent_name}")


        # 3. Issuer van de signature
        signature_info = manifest_data_to_parse.get("signature_info", {})
        issuer = signature_info.get("issuer")
        # Voeg alleen toe als het nieuwe info is en nog niet genoemd als claim_generator
        if issuer and (not claim_generator_info or issuer != claim_generator_info[0].get("name")):
            summary_points.append(f"Handtekening uitgegeven door: {issuer}")
        
        # Fallback als er helemaal geen punten zijn
        if not summary_points and manifest_data_to_parse:
             summary_points.append("Algemene C2PA-informatie aanwezig. Bekijk JSON voor details.")


        return summary_points if summary_points else ["Geen specifieke samenvattingspunten gevonden, bekijk de volledige JSON."]

    except Exception as e:
        app.logger.error(f"Error generating C2PA summary: {e}", exc_info=True)
        return [f"Kon geen samenvatting genereren (fout: {type(e).__name__}). Bekijk de volledige JSON."]


@app.route('/', methods=['GET'])
def index_get():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Geen bestanddeel in het request')
        return redirect(url_for('index_get'))
    file = request.files['file']
    if file.filename == '':
        flash('Geen bestand geselecteerd')
        return redirect(url_for('index_get'))

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(filepath)

        c2pa_data_json_string = None
        c2pa_summary_points = None
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
                    c2pa_summary_points = generate_c2pa_summary(parsed_json)

                    json_save_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename_to_save)
                    with open(json_save_path, 'w') as f_json:
                        f_json.write(c2pa_data_json_string)
                except json.JSONDecodeError:
                    c2pa_data_json_string = raw_json_output # Toon ruwe output als parsen mislukt
                    error_message = "Output van c2patool was geen valide JSON, maar wordt wel getoond."
                    # Sla de ruwe output op
                    json_save_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename_to_save)
                    with open(json_save_path, 'w') as f_json:
                        f_json.write(raw_json_output)
            else: # c2patool gaf een foutcode
                error_output = process.stderr or process.stdout
                if "No C2PA marker found" in error_output or "No manifest found" in error_output:
                    error_message = "Geen C2PA-manifest gevonden in het bestand."
                else:
                    error_message = f"c2patool fout (code {process.returncode}): {error_output}"
                if not error_output.strip(): # Fallback als er geen specifieke melding is
                    error_message = f"c2patool gaf een foutcode {process.returncode} zonder specifieke melding."
        
        except FileNotFoundError:
            error_message = f"c2patool uitvoerbaar bestand niet gevonden op: {c2patool_path}. Controleer de Dockerfile."
        except PermissionError:
            error_message = f"Permissie geweigerd bij uitvoeren van {c2patool_path}. Controleer bestandspermissies in de container."
        except Exception as e:
            app.logger.error(f"Onverwachte fout tijdens c2patool aanroep: {e}", exc_info=True)
            error_message = f"Een onverwachte fout is opgetreden: {str(e)}"

        return render_template('index.html',
                               filename=original_filename,
                               c2pa_data=c2pa_data_json_string,
                               c2pa_summary=c2pa_summary_points,
                               json_download_filename=json_filename_to_save if c2pa_data_json_string and not error_message else None,
                               error=error_message)

    flash('Ongeldig bestandstype, alleen PNG is toegestaan.')
    return redirect(url_for('index_get'))

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
        return redirect(url_for('index_get'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)