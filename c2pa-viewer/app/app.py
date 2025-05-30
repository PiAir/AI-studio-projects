import os
import subprocess
import json
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename
from PIL import Image 
from PIL.ExifTags import TAGS

# --- Flask App Initialisatie ---
app = Flask(__name__)

# --- Globale Variabelen & Configuratie ---
UPLOAD_FOLDER = 'uploads'
JSON_OUTPUT_FOLDER = 'json_outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'wav', 'mp3'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'} 
AUDIO_EXTENSIONS = {'wav', 'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER
app.secret_key = 'supersecretkey'

# Maak de mappen als ze niet bestaan
for folder in [UPLOAD_FOLDER, JSON_OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- Helper Functies ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    if '.' in filename: return filename.rsplit('.', 1)[1].lower()
    return None

def get_software_agent_name(agent_data):
    if isinstance(agent_data, str): return agent_data
    if isinstance(agent_data, dict): return agent_data.get("name")
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
        if not manifest_data_to_parse: return ["Geen manifesten gevonden."]
        
        created_by_tool, ai_generated_flag, other_actions_agents = None, False, []
        claim_generator_text = None

        if "claim_generator_info" in manifest_data_to_parse:
            cg_info_list = manifest_data_to_parse["claim_generator_info"]
            if isinstance(cg_info_list, list) and cg_info_list: claim_generator_text = cg_info_list[0].get("name")
        elif "claim_generator" in manifest_data_to_parse: # Voor Adobe Firefly stijl
            claim_generator_text = manifest_data_to_parse["claim_generator"]
            # Probeer toolnaam te extraheren uit "Adobe_Firefly adobe_c2pa/0.12.4..."
            if claim_generator_text and " " in claim_generator_text:
                 possible_tool_name = claim_generator_text.split(" ")[0].replace("_", " ")
                 # Herken bekende tools om te voorkomen dat versie info etc. wordt getoond als "tool"
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
                        if software_agent_name: created_by_tool = software_agent_name
                        if digital_source_type and "trainedAlgorithmicMedia" in digital_source_type: ai_generated_flag = True
                    elif software_agent_name and software_agent_name not in other_actions_agents: 
                        other_actions_agents.append(software_agent_name)

        if created_by_tool: summary_points.append(f"Gemaakt met: {created_by_tool}")
        elif claim_generator_text and any(tool_kw in claim_generator_text.lower() for tool_kw in ["firefly", "chatgpt", "gpt", "dall-e", "sora"]):
            created_by_tool = claim_generator_text # Gebruik voor verdere logica
            summary_points.append(f"Gemaakt met/door: {claim_generator_text}")
        
        if ai_generated_flag:
            # Voorkom dubbele AI melding als toolnaam al AI suggereert
            if not created_by_tool or not any(ai_kw in created_by_tool.lower() for ai_kw in ["gpt", "dall-e", "firefly", "midjourney", "adobe", "sora"]):
                summary_points.append("AI is gebruikt om media (mogelijk volledig) te genereren.")
        
        # "Referenties afgegeven door" alleen als het anders is dan de creatietool
        if claim_generator_text and (not created_by_tool or created_by_tool.lower() not in claim_generator_text.lower()):
             summary_points.append(f"Referenties afgegeven door: {claim_generator_text}")

        for agent in other_actions_agents: # Andere tools
            if agent.lower() != (created_by_tool or "").lower() and agent.lower() != (claim_generator_text or "").lower():
                summary_points.append(f"Ook gebruikt: {agent}")

        signature_info = manifest_data_to_parse.get("signature_info", {})
        issuer = signature_info.get("issuer")
        mentioned_entities = [created_by_tool, claim_generator_text] # Bouw lijst van al genoemde entiteiten
        if created_by_tool: mentioned_entities.append(created_by_tool)
        if claim_generator_text: mentioned_entities.append(claim_generator_text)
        mentioned_entities_lower = [e.lower() for e in mentioned_entities if e] # Converteer naar lowercase voor case-insensitive check
        
        if issuer and issuer.lower() not in mentioned_entities_lower:
            summary_points.append(f"Handtekening uitgegeven door: {issuer}")
        
        if not summary_points and manifest_data_to_parse: # Als er nog steeds niks is, maar wel een manifest
             summary_points.append("Algemene C2PA-informatie aanwezig. Bekijk JSON voor details.")
        
        return summary_points if summary_points else ["Geen specifieke samenvattingspunten gevonden, bekijk de volledige JSON."]
    except Exception as e:
        app.logger.error(f"Error generating C2PA summary: {e}", exc_info=True)
        return [f"Kon geen samenvatting genereren (fout: {type(e).__name__}). Bekijk de volledige JSON."]

def get_exif_data(image_path):
    exif_data_dict = {}
    try:
        image = Image.open(image_path)
        exif_pil = image.getexif() 
        if exif_pil:
            for tag_id, value in exif_pil.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    try:
                        decoded_value = value.decode('utf-8', errors='replace')
                        # Toon alleen "leesbare" strings, anders de representatie van bytes
                        # Check of de string printbare ASCII bevat of gangbare whitespace
                        is_printable_string = all(32 <= ord(char) <= 126 or ord(char) in [9,10,13] for char in decoded_value.strip())
                        if decoded_value.strip() and is_printable_string: # Alleen als het niet leeg is en printbaar
                             exif_data_dict[str(tag_name)] = decoded_value.strip()
                        else:
                             exif_data_dict[str(tag_name)] = f"Binair (lengte {len(value)})"
                    except Exception: # Fallback voor onverwachte decodeerfouten
                        exif_data_dict[str(tag_name)] = f"Binair (lengte {len(value)})"
                else:
                    exif_data_dict[str(tag_name)] = value
            return json.dumps(exif_data_dict, indent=4, default=str) # default=str voor niet-JSON-serialiseerbare types
    except Exception as e:
        app.logger.warning(f"Kon EXIF data niet lezen van {image_path}: {e}")
    return None

# --- Routes ---
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
        file_ext = get_file_extension(processed_filename)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        file.save(filepath)

        c2pa_data_json_string = None
        c2pa_summary_points = None
        exif_data_json_string = None
        error_message = None
        info_message = None
        json_filename_to_save = processed_filename + '.c2pa.json'

        if file_ext in IMAGE_EXTENSIONS:
            exif_data_json_string = get_exif_data(filepath)

        try:
            c2patool_path = '/usr/local/bin/c2patool'
            # Standaard aanroep om C2PA data te lezen (JSON output)
            process = subprocess.run(
                [c2patool_path, filepath],
                capture_output=True, text=True, check=False 
            )
            if process.returncode == 0:
                raw_json_output = process.stdout
                try:
                    parsed_json = json.loads(raw_json_output)
                    c2pa_data_json_string = json.dumps(parsed_json, indent=4)
                    c2pa_summary_points = generate_c2pa_summary(parsed_json)
                    # Sla de JSON op voor download
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
                no_c2pa_messages = ["No C2PA marker found", "No manifest found", "Error: No claim found"]
                unknown_format_message = "asset could not be parsed" # Geldt voor alle media
                
                is_no_c2pa_data_error = any(msg.lower() in error_output.lower() for msg in no_c2pa_messages)
                is_unknown_format_error = unknown_format_message.lower() in error_output.lower()

                if is_unknown_format_error:
                    error_message = "Fout bij het verwerken: het mediaformaat wordt niet herkend of het bestand is mogelijk beschadigd."
                    c2pa_data_json_string = None # Geen data om te tonen/downloaden
                elif is_no_c2pa_data_error:
                    info_message = "Geen C2PA-metadata aangetroffen in dit bestand."
                    c2pa_data_json_string = None # Geen data om te tonen/downloaden
                else: # Andere c2patool fout
                    error_message = f"c2patool fout (code {process.returncode}): {error_output}"
                
                # Fallback als er een exit code is maar geen duidelijke error output
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
                               file_extension=file_ext,
                               c2pa_data=c2pa_data_json_string,
                               c2pa_summary=c2pa_summary_points,
                               exif_data=exif_data_json_string,
                               json_download_filename=json_filename_to_save if c2pa_data_json_string and not error_message else None,
                               error=error_message,
                               info_message=info_message)

    flash(f'Ongeldig bestandstype. Alleen {", ".join(sorted(list(ALLOWED_EXTENSIONS)))} zijn toegestaan.')
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

# --- Main execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)