import os
import subprocess
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
JSON_OUTPUT_FOLDER = 'json_outputs'
# GEWIJZIGD: 'mp4' toegevoegd
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4'}

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

def get_file_extension(filename):
    """Helper om de bestandsextensie te krijgen."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None

def get_software_agent_name(agent_data):
    if isinstance(agent_data, str):
        return agent_data
    if isinstance(agent_data, dict):
        return agent_data.get("name")
    return None

def generate_c2pa_summary(parsed_json_data):
    summary_points = []
    try:
        if not parsed_json_data or "manifests" not in parsed_json_data:
            return ["Geen valide C2PA manifest data gevonden voor samenvatting."]

        active_manifest_label = parsed_json_data.get("active_manifest")
        manifest_data_to_parse = None

        if active_manifest_label and active_manifest_label in parsed_json_data["manifests"]:
            manifest_data_to_parse = parsed_json_data["manifests"][active_manifest_label]
        elif parsed_json_data["manifests"]:
            first_manifest_key = list(parsed_json_data["manifests"].keys())[0]
            manifest_data_to_parse = parsed_json_data["manifests"][first_manifest_key]
        
        if not manifest_data_to_parse:
            return ["Geen manifesten gevonden in de data."]

        created_by_tool = None
        ai_generated_flag = False
        other_actions_agents = []

        claim_generator_text = None
        if "claim_generator_info" in manifest_data_to_parse:
            cg_info_list = manifest_data_to_parse["claim_generator_info"]
            if isinstance(cg_info_list, list) and cg_info_list:
                claim_generator_text = cg_info_list[0].get("name")
        elif "claim_generator" in manifest_data_to_parse:
            claim_generator_text = manifest_data_to_parse["claim_generator"]
            if claim_generator_text and " " in claim_generator_text:
                 possible_tool_name = claim_generator_text.split(" ")[0].replace("_", " ")
                 if possible_tool_name.lower() in ["adobe firefly", "chatgpt", "openai", "sora"]:
                     claim_generator_text = possible_tool_name

        assertions = manifest_data_to_parse.get("assertions", [])
        actions_assertion = next((a for a in assertions if a.get("label") in ["c2pa.actions", "c2pa.actions.v2"]), None)
        
        if actions_assertion and isinstance(actions_assertion.get("data"), dict) and isinstance(actions_assertion["data"].get("actions"), list):
            for action_item in actions_assertion["data"]["actions"]:
                if isinstance(action_item, dict):
                    action_type = action_item.get("action")
                    software_agent_name = get_software_agent_name(action_item.get("softwareAgent"))
                    digital_source_type = action_item.get("digitalSourceType")

                    if action_type == "c2pa.created":
                        if software_agent_name:
                            created_by_tool = software_agent_name
                        if digital_source_type and "trainedAlgorithmicMedia" in digital_source_type:
                            ai_generated_flag = True
                    elif software_agent_name:
                        if software_agent_name not in other_actions_agents:
                             other_actions_agents.append(software_agent_name)

        if created_by_tool:
            summary_points.append(f"Gemaakt met: {created_by_tool}")
        elif claim_generator_text and any(tool_kw in claim_generator_text.lower() for tool_kw in ["firefly", "chatgpt", "gpt", "dall-e", "sora"]):
            created_by_tool = claim_generator_text
            summary_points.append(f"Gemaakt met/door: {claim_generator_text}")

        if ai_generated_flag:
            if not created_by_tool or not any(ai_kw in created_by_tool.lower() for ai_kw in ["gpt", "dall-e", "firefly", "midjourney", "adobe", "sora"]):
                summary_points.append("AI is gebruikt om media (mogelijk volledig) te genereren.")
        
        if claim_generator_text and (not created_by_tool or created_by_tool.lower() not in claim_generator_text.lower()):
             summary_points.append(f"Referenties afgegeven door: {claim_generator_text}")

        for agent in other_actions_agents:
            if agent.lower() != (created_by_tool or "").lower() and agent.lower() != (claim_generator_text or "").lower():
                summary_points.append(f"Ook gebruikt: {agent}")

        signature_info = manifest_data_to_parse.get("signature_info", {})
        issuer = signature_info.get("issuer")
        mentioned_entities = [created_by_tool, claim_generator_text]
        mentioned_entities_lower = [e.lower() for e in mentioned_entities if e]
        if issuer and issuer.lower() not in mentioned_entities_lower:
            summary_points.append(f"Handtekening uitgegeven door: {issuer}")
        
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
        processed_filename = secure_filename(file.filename)
        file_ext = get_file_extension(processed_filename) # << HAAL EXTENSIE OP
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        file.save(filepath)

        c2pa_data_json_string = None
        c2pa_summary_points = None
        error_message = None
        info_message = None
        json_filename_to_save = processed_filename + '.json'

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
                    c2pa_data_json_string = raw_json_output 
                    error_message = "Output van c2patool was geen valide JSON, maar wordt wel getoond."
                    json_save_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename_to_save)
                    with open(json_save_path, 'w') as f_json:
                        f_json.write(raw_json_output)
            else: 
                error_output = process.stderr or process.stdout
                no_c2pa_messages = [
                    "No C2PA marker found", 
                    "No manifest found",
                    "Error: No claim found"
                ]
                unknown_format_message = "asset could not be parsed: Unknown image format" # Kan ook voor video's gelden

                is_no_c2pa_data_error = any(msg.lower() in error_output.lower() for msg in no_c2pa_messages)
                is_unknown_format_error = unknown_format_message.lower() in error_output.lower()

                if is_unknown_format_error:
                    error_message = "Fout bij het verwerken van het bestand: het mediaformaat wordt niet herkend of het bestand is mogelijk beschadigd."
                    c2pa_data_json_string = None
                elif is_no_c2pa_data_error:
                    info_message = "Geen C2PA-metadata aangetroffen in dit bestand."
                    c2pa_data_json_string = None 
                else:
                    error_message = f"c2patool fout (code {process.returncode}): {error_output}"
                
                if not error_output.strip() and not is_no_c2pa_data_error and not is_unknown_format_error:
                    error_message = f"c2patool gaf een foutcode {process.returncode} zonder specifieke melding."
        
        except FileNotFoundError:
            error_message = f"c2patool uitvoerbaar bestand niet gevonden op: {c2patool_path}. Controleer de Dockerfile."
        except PermissionError:
            error_message = f"Permissie geweigerd bij uitvoeren van {c2patool_path}. Controleer bestandspermissies in de container."
        except Exception as e:
            app.logger.error(f"Onverwachte fout tijdens c2patool aanroep: {e}", exc_info=True)
            error_message = f"Een onverwachte fout is opgetreden: {str(e)}"

        return render_template('index.html',
                               filename=processed_filename,
                               file_extension=file_ext, # << GEEF EXTENSIE DOOR
                               c2pa_data=c2pa_data_json_string,
                               c2pa_summary=c2pa_summary_points,
                               json_download_filename=json_filename_to_save if c2pa_data_json_string and not error_message else None,
                               error=error_message,
                               info_message=info_message)

    flash(f'Ongeldig bestandstype. Alleen {", ".join(sorted(list(ALLOWED_EXTENSIONS)))} zijn toegestaan.') # Sorteer voor consistentie
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