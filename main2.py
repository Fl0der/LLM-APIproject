import os
import json
import google.generativeai as genai

def setup_gemini():
    """Iestatīt Gemini API"""
    print("Ievadiet savu Gemini API atslēgu:")
    api_key = input().strip()
    
    if not api_key:
        print("Kļūda: API atslēga ir obligāta")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model
    except Exception as e:
        print(f"Kļūda iestatot Gemini: {e}")
        return None

def read_file(file_path):
    """Nolasīt teksta failu"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Kļūda: Fails {file_path} netika atrasts")
        return None

def create_prompt(jd_text, cv_text):
    """Izveidot promptu Gemini API"""
    prompt = f"""
Kā HR speciālists, analizējiet kandidāta CV atbilstību darba aprakstam un sniedziet novērtējumu JSON formātā.

Darba apraksts:
{jd_text}

Kandidāta CV:
{cv_text}

Atbildiet TIKAI JSON formātā ar šādu struktūru:
{{
    "match_score": 0-100,
    "summary": "Īss apraksts, cik labi CV atbilst JD",
    "strengths": [
        "Galvenās prasmes/pieredze no CV, kas atbilst JD",
        "Otra nozīmīgākā atbilstība",
        "Trešā nozīmīgākā atbilstība"
    ],
    "missing_requirements": [
        "Svarīgas JD prasības, kas CV nav redzamas",
        "Otra svarīgā trūkstošā prasme", 
        "Trešā trūkstošā prasme"
    ],
    "verdict": "strong match | possible match | not a match"
}}

Vērtējuma kritēriji:
- match_score: 0-100, kur 100 ir pilnīga atbilstība
- verdict: "strong match" (>=75), "possible match" (40-74), "not a match" (<40)
- strengths: 3 galvenās atbilstības
- missing_requirements: 3 galvenās trūkstošās prasmes

Atbildi sniedziet TIKAI JSON formātā.
"""
    return prompt

def save_prompt_to_file(prompt, cv_number):
    """Saglabāt promptu failā"""
    os.makedirs("prompts", exist_ok=True)
    prompt_file = f"prompts/prompt_cv{cv_number}.md"
    
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"Prompt saglabāts: {prompt_file}")
    return prompt_file

def call_gemini(model, prompt):
    """Izsaukt Gemini Flash ar temperature 0.3"""
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000
            )
        )
        return response.text
    except Exception as e:
        print(f"Kļūda izsaucot Gemini API: {e}")
        return None

def parse_json_response(response_text):
    """Parsēt JSON atbildi"""
    try:
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
        else:
            print("JSON netika atrasts atbildē")
            return None
    except json.JSONDecodeError as e:
        print(f"Kļūda parsējot JSON: {e}")
        return None

def save_json_output(data, cv_number):
    """Saglabāt JSON izvadi"""
    os.makedirs("outputs", exist_ok=True)
    output_file = f"outputs/cv{cv_number}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSON izvade saglabāta: {output_file}")
    return output_file

def generate_markdown_report(data, cv_number):
    """Ģenerēt Markdown pārskatu"""
    report_content = f"""# Kandidāta CV{cv_number} atbilstības pārskats

## Rezultātu kopsavilkums

**Atbilstības rezultāts:** {data.get('match_score', 0)}/100
**Vērtējums:** {data.get('verdict', '')}

## Kopsavilkums
{data.get('summary', '')}

## Stiprās puses

"""
    
    for strength in data.get('strengths', []):
        report_content += f"- {strength}\n"
    
    report_content += "\n## Trūkstošās prasmes\n"
    
    for missing in data.get('missing_requirements', []):
        report_content += f"- {missing}\n"
    
    return report_content

def generate_html_report(data, cv_number):
    """Ģenerēt HTML pārskatu"""
    html_content = f"""<!DOCTYPE html>
<html lang="lv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kandidāta CV{cv_number} atbilstības pārskats</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .score {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
        .section {{ margin-bottom: 30px; }}
        .strengths li {{ color: green; }}
        .missing li {{ color: red; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Kandidāta CV{cv_number} atbilstības pārskats</h1>
        <div class="score">Atbilstības rezultāts: {data.get('match_score', 0)}/100</div>
        <div class="verdict">Vērtējums: {data.get('verdict', '')}</div>
    </div>
    
    <div class="section">
        <h2>Kopsavilkums</h2>
        <p>{data.get('summary', '')}</p>
    </div>
    
    <div class="section strengths">
        <h2>Stiprās puses</h2>
        <ul>
"""
    
    for strength in data.get('strengths', []):
        html_content += f"            <li>{strength}</li>\n"
    
    html_content += """        </ul>
    </div>
    
    <div class="section missing">
        <h2>Trūkstošās prasmes</h2>
        <ul>
"""
    
    for missing in data.get('missing_requirements', []):
        html_content += f"            <li>{missing}</li>\n"
    
    html_content += """        </ul>
    </div>
</body>
</html>"""
    
    return html_content

def save_reports(data, cv_number):
    """Saglabāt Markdown un HTML pārskatus"""
    os.makedirs("outputs", exist_ok=True)
    
    # Saglabāt Markdown pārskatu
    md_report = generate_markdown_report(data, cv_number)
    md_file = f"outputs/cv{cv_number}_report.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"Markdown pārskats saglabāts: {md_file}")
    
    # Saglabāt HTML pārskatu
    html_report = generate_html_report(data, cv_number)
    html_file = f"outputs/cv{cv_number}_report.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    print(f"HTML pārskats saglabāts: {html_file}")

def main():
    """Galvenā programmas funkcija"""
    print("CV-JD Atbilstības Analīzes Rīks")
    print("=" * 40)
    
    # Iestatīt Gemini
    model = setup_gemini()
    if not model:
        return
    
    # Pārbaudīt ievades failus
    jd_file = "sample_inputs/jd.txt"
    cv_files = [
        "sample_inputs/cv1.txt",
        "sample_inputs/cv2.txt", 
        "sample_inputs/cv3.txt"
    ]
    
    # 1. solis: Nolasīt darba aprakstu
    jd_text = read_file(jd_file)
    if not jd_text:
        print("Nevar nolasīt darba aprakstu")
        return
    
    print("Darba apraksts nolasīts")
    
    # Apstrādāt katru CV
    for i, cv_file in enumerate(cv_files, 1):
        print(f"\n--- Apstrādā CV{i} ---")
        
        # 1. solis: Nolasīt CV
        cv_text = read_file(cv_file)
        if not cv_text:
            print(f"Nevar nolasīt CV{i}")
            continue
        
        # 2. solis: Sagatavot promptu un saglabāt
        prompt = create_prompt(jd_text, cv_text)
        save_prompt_to_file(prompt, i)
        
        # 3. solis: Izsaukt Gemini Flash ar temperature 0.3
        response = call_gemini(model, prompt)
        
        if not response:
            print(f"Neizdevās saņemt atbildi priekš CV{i}")
            continue
        
        # 4. solis: Parsēt un saglabāt JSON
        json_data = parse_json_response(response)
        if not json_data:
            print(f"Neizdevās parsēt atbildi priekš CV{i}")
            continue
            
        save_json_output(json_data, i)
        
        # 5. solis: Ģenerēt pārskatus (Markdown un HTML)
        save_reports(json_data, i)
        
        print(f"CV{i} apstrāde pabeigta")
    
    print("\n=== Visi CV apstrādāti veiksmīgi! ===")
    print("Rezultāti saglabāti mapēs 'prompts' un 'outputs'")

if __name__ == "__main__":
    main()