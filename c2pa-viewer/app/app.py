import os
import subprocess
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
JSON_OUTPUT_FOLDER = 'json_outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

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

def get_software_agent_name(agent_data):
    """Helper om naam uit softwareAgent te halen, of het nu string of dict is."""
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

        # 1. Claim Generator (verschillende mogelijke veldnamen)
        claim_generator_text = None
        if "claim_generator_info" in manifest_data_to_parse: # OpenAI-stijl
            cg_info_list = manifest_data_to_parse["claim_generator_info"]
            if isinstance(cg_info_list, list) and cg_info_list:
                claim_generator_text = cg_info_list[0].get("name")
        elif "claim_generator" in manifest_data_to_parse: # Adobe Firefly-stijl
            claim_generator_text = manifest_data_to_parse["claim_generator"]
            # Vaak bevat dit meer dan alleen de naam, bijv. "Adobe_Firefly adobe_c2pa/0.12.4..."
            # Probeer de toolnaam eruit te filteren
            if claim_generator_text and " " in claim_generator_text:
                 possible_tool_name = claim_generator_text.split(" ")[0].replace("_", " ")
                 if possible_tool_name.lower() in ["adobe firefly", "chatgpt", "openai"]: # Herken bekende tools
                     claim_generator_text = possible_tool_name


        # 2. Acties
        assertions = manifest_data_to_parse.get("assertions", [])
        # Zoek naar c2pa.actions of c2pa.actions.v2
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
                    elif software_agent_name: # Andere acties
                        if software_agent_name not in other_actions_agents: # Voorkom duplicaten
                             other_actions_agents.append(software_agent_name)


        # Samenvatting opbouwen
        if created_by_tool:
            summary_points.append(f"Gemaakt met: {created_by_tool}")
        elif claim_generator_text and any(tool_kw in claim_generator_text.lower() for tool_kw in ["firefly", "chatgpt", "gpt", "dall-e"]):
            # Als 'created_by_tool' mist, maar claim_generator lijkt een tool te zijn.
            created_by_tool = claim_generator_text # Gebruik voor verdere logica
            summary_points.append(f"Gemaakt met/door: {claim_generator_text}")


        if ai_generated_flag:
            if not created_by_tool or not any(ai_kw in created_by_tool.lower() for ai_kw in ["gpt", "dall-e", "firefly", "midjourney", "adobe"]):
                summary_points.append("AI is gebruikt om afbeelding (mogelijk volledig) te genereren.")
        
        # Toon "Referenties afgegeven door" als het een andere entiteit is dan de creatietool
        if claim_generator_text and (not created_by_tool or created_by_tool.lower() not in claim_generator_text.lower()):
             summary_points.append(f"Referenties afgegeven door: {claim_generator_text}")


        # Andere tools die betrokken waren (als die er zijn en niet al genoemd)
        for agent in other_actions_agents:
            if agent.lower() != (created_by_tool or "").lower() and agent.lower() != (claim_generator_text or "").lower():
                summary_points.append(f"Ook gebruikt: {agent}")


        # Issuer van de signature
        signature_info = manifest_data_to_parse.get("signature_info", {})
        issuer = signature_info.get("issuer")
        
        # Voeg issuer alleen toe als het nog niet is genoemd (als tool, claim generator)
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

# ... (rest van app.py blijft hetzelfde) ...
# Zorg ervoor dat de routes en de main if-block correct zijn zoals in het vorige volledige app.py antwoord.
# Hieronder alleen de relevante delen voor de duidelijkheid, de rest is identiek.

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
        original_filename_base, original_file_ext = os.path.splitext(file.filename)
        secure_filename_base = secure_filename(original_filename_base)
        processed_filename = secure_filename(file.filename)
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
                    c2pa_summary_points = generate_c2pa_summary(parsed_json) # <<<< HIER GEBRUIKT
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
                is_no_c2pa_data_error = any(msg.lower() in error_output.lower() for msg in no_c2pa_messages)

                if is_no_c2pa_data_error:
                    info_message = "Geen C2PA-metadata aangetroffen in dit bestand."
                    c2pa_data_json_string = None 
                else:
                    error_message = f"c2patool fout (code {process.returncode}): {error_output}"
                
                if not error_output.strip() and not is_no_c2pa_data_error:
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
                               c2pa_data=c2pa_data_json_string,
                               c2pa_summary=c2pa_summary_points,
                               json_download_filename=json_filename_to_save if c2pa_data_json_string and not error_message else None,
                               error=error_message,
                               info_message=info_message)

    flash(f'Ongeldig bestandstype. Alleen {", ".join(ALLOWED_EXTENSIONS)} zijn toegestaan.')
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