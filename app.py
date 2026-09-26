import ast
# Compatibility patch for Python 3.12+ / 3.14 with Aksharamukha
if not hasattr(ast, 'Str'):
    ast.Str = ast.Constant
    ast.Num = ast.Constant
    ast.Bytes = ast.Constant
    ast.NameConstant = ast.Constant

import os
import re
import inspect
import pandas as pd
import streamlit as st
import chanda

try:
    from aksharamukha import transliterate
    HAS_AKSHARAMUKHA = True
except ImportError:
    HAS_AKSHARAMUKHA = False

try:
    import settings
except ImportError:
    settings = None

st.set_page_config(page_title="Chhandojnanam", layout="wide")

AKSHARAMUKHA_SCHEMES = [
    "Devanagari", "IAST", "ISO", "Harvard-Kyoto", "SLP1", "ITRANS", "Velthuis", "WX",
    "Bengali", "Gujarati", "Gurmukhi", "Kannada", "Malayalam", 
    "Oriya", "Tamil", "Telugu", "Brahmi", "Grantha", "Sharada", "Siddham"
]

# Helper functions for Sanskrit mode (Strictly no English punctuation, only danda)
def to_devanagari_numerals(text):
    digit_map = str.maketrans("0123456789", "०१२३४५६७८९")
    return str(text).translate(digit_map)

def clean_sanskrit_text(text):
    if text is None:
        return ""
    text = to_devanagari_numerals(str(text))
    for char in ':,.-!?()[]{}"\';/\\_~`@#$%^&*+=':
        text = text.replace(char, " ")
    return " ".join(text.split())

# Re-align syllables:
# 1. Pure halantas merge to preceding letter (व + म् -> वम्)
# 2. Conjunct onsets transfer codas to preceding letter (ल + म्ब्य -> लम्ब् + य)
def realign_phonetic_syllables(syllables, lg_list):
    if not syllables:
        return [], []
    syls = list(syllables)
    lgs = list(lg_list)
    
    # Step 1: Merge any purely halanta/consonant tokens (like trailing 'म्', 'न्', 'त्') into previous syllable
    pure_coda_pattern = re.compile(r"^(?:[\u0915-\u0939\u0958-\u095F]\u094D)+$")
    i = 1
    while i < len(syls):
        if pure_coda_pattern.match(syls[i]):
            syls[i - 1] += syls[i]
            syls.pop(i)
            if i < len(lgs) and len(lgs) > len(syls):
                lgs.pop(i)
        else:
            i += 1

    # Step 2: Transfer conjunct onset codas to preceding syllable
    conjunct_pattern = re.compile(r"^((?:[\u0915-\u0939\u0958-\u095F]\u094D)+)(.+)$")
    for i in range(1, len(syls)):
        m = conjunct_pattern.match(syls[i])
        if m:
            coda = m.group(1)       # e.g. 'म्ब्', 'र्', 'त्'
            remainder = m.group(2)  # e.g. 'य', 'म', 'स'
            syls[i - 1] += coda
            syls[i] = remainder
            
    if len(lgs) > len(syls):
        lgs = lgs[:len(syls)]
        
    return syls, lgs

# Unpack meter name from nested structures
def extract_primary_meter(res_data):
    verse_matches = res_data.get("verse", [])
    if verse_matches and isinstance(verse_matches, list):
        for vm in verse_matches:
            if isinstance(vm, dict) and "chanda" in vm:
                cand = vm["chanda"]
                while isinstance(cand, (list, tuple)) and len(cand) > 0:
                    cand = cand[0]
                if isinstance(cand, str) and cand.strip():
                    return cand.strip()

    for l_entry in res_data.get("line", []):
        r = l_entry.get("result", {})
        disp_ch = r.get("display_chanda")
        if disp_ch and isinstance(disp_ch, str):
            name = disp_ch.split("(")[0].strip()
            if name:
                return name
        ch = r.get("chanda")
        cand = ch
        while isinstance(cand, (list, tuple)) and len(cand) > 0:
            cand = cand[0]
        if isinstance(cand, str) and cand.strip():
            return cand.strip()
            
    return None

# Transliteration helpers
def convert_to_devanagari(text, input_script_choice):
    if not text or not HAS_AKSHARAMUKHA:
        return text
    try:
        if input_script_choice == "Auto-Detect":
            detected = transliterate.auto_detect(text)
            src_script = detected if detected else "IAST"
        else:
            src_script = input_script_choice
        return transliterate.process(src_script, "Devanagari", text)
    except Exception:
        return text

def convert_from_devanagari(text, target_script):
    if not text or not HAS_AKSHARAMUKHA or target_script == "Devanagari":
        return text
    try:
        return transliterate.process("Devanagari", target_script, str(text))
    except Exception:
        return text

# Determine data directory path
DATA_PATH = None
if settings:
    for attr in ["DATA_PATH", "DATA_DIR", "CHANDA_DATA_DIR", "CHANDA_DATA"]:
        if hasattr(settings, attr):
            DATA_PATH = getattr(settings, attr)
            break

if not DATA_PATH or not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

@st.cache_resource
def load_analyzer(path):
    return chanda.Chanda(path)

try:
    analyzer = load_analyzer(DATA_PATH)
except Exception as e:
    st.error(f"Initialization failure: {e}")
    st.stop()

def run_identification(analyzer, text, fuzzy=True):
    method = getattr(analyzer, "identify_from_text", None) or getattr(analyzer, "process_text", None)
    if method is None:
        raise AttributeError("Identification method not found")
    
    sig = inspect.signature(method)
    kwargs = {}
    for param in sig.parameters:
        if param in ["fuzzy", "fuzzy_match", "approximate"]:
            kwargs[param] = fuzzy
        elif param in ["text", "input_text", "verse"]:
            kwargs[param] = text

    if kwargs:
        return method(**kwargs)
    return method(text)

# Sidebar: Language & Script Selectors
language = st.sidebar.radio(
    "Language / भाषा",
    options=["English", "संस्कृतम्"]
)
is_sa = (language == "संस्कृतम्")

def format_script(s):
    if is_sa:
        if s == "Auto-Detect": return "स्वयम्"
        if s == "Devanagari": return "देवनागरी"
    return s

st.sidebar.markdown("---")
t_input_script = "निवेशलिपिः" if is_sa else "Input Script"
t_output_script = "निर्गमलिपिः" if is_sa else "Output Script"

input_options = ["Auto-Detect"] + AKSHARAMUKHA_SCHEMES
input_script_sel = st.sidebar.selectbox(t_input_script, input_options, index=0, format_func=format_script)
output_script_sel = st.sidebar.selectbox(t_output_script, AKSHARAMUKHA_SCHEMES, index=0, format_func=format_script)

# Localization mapping
if is_sa:
    title_text = "छन्दोज्ञानम्"
    subtitle_text = "संस्कृतच्छन्दःपरिज्ञानप्रणाली ॥"
    help_label = "साहाय्यम्"
    input_label = "पद्यम्"
    fuzzy_label = "सान्निध्यसन्धानम्"
    button_label = "परीक्ष्यताम्"
    empty_warning = "कृपया पद्यं प्रविश्यताम् ॥"
    verse_meter_label = "प्रधानच्छन्दः"
    table_header_line = "पादविश्लेषणम्"
    table_header_scansion = "वर्णलघुगुरुविभागः"
    col_pada = "पादः"
    col_meter = "छन्दः"
    col_jaati = "जातिः"
    col_syllables = "वर्णाः"
    col_matras = "मात्राः"
    col_ganas = "गणाः"
    row_syllable = "वर्णः"
    row_nature = "प्रकृतिः"
    unknown_meter = "अज्ञातम्"
else:
    title_text = "Chandojnanam"
    subtitle_text = "Sanskrit Prosody and Metrical Identification System"
    help_label = "Help"
    input_label = "Sanskrit Verse"
    fuzzy_label = "Fuzzy Matching"
    button_label = "Analyze Verse"
    empty_warning = "Please provide verse text for analysis."
    verse_meter_label = "Identified Meter"
    table_header_line = "Line Analysis"
    table_header_scansion = "Syllable and Scansion Matrix"
    col_pada = "Line / Pada"
    col_meter = "Meter"
    col_jaati = "Jaati"
    col_syllables = "Syllables"
    col_matras = "Matras"
    col_ganas = "Gana Sequence"
    row_syllable = "Syllable"
    row_nature = "Weight (L/G)"
    unknown_meter = "Unidentified"

# Header with Help Link Button
col_header, col_help_btn = st.columns([5, 1])
with col_header:
    st.title(title_text)
    st.caption(subtitle_text)
with col_help_btn:
    st.write("")
    st.link_button(
        help_label,
        "https://web.archive.org/web/20250620200354/https://sanskrit.iitk.ac.in/jnanasangraha/chanda/help"
    )

# Input Section
default_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
verse_input = st.text_area(input_label, value=default_verse, height=110)
fuzzy_enabled = st.checkbox(fuzzy_label, value=True)

if st.button(button_label, type="primary"):
    if not verse_input.strip():
        st.warning(empty_warning)
    else:
        try:
            # Transliterate input into Devanagari for the engine
            devanagari_input = convert_to_devanagari(verse_input.strip(), input_script_sel)

            raw_output = run_identification(analyzer, devanagari_input, fuzzy=fuzzy_enabled)
            res_data = raw_output.get("result", {}) if isinstance(raw_output, dict) else {}

            # 1. Primary Verse-level Meter Identification
            primary_meter = extract_primary_meter(res_data) or unknown_meter

            # Render output script conversion if needed
            disp_meter = convert_from_devanagari(primary_meter, output_script_sel)
            if is_sa:
                clean_meter = clean_sanskrit_text(disp_meter)
                st.markdown(f"### {verse_meter_label} । {clean_meter} ॥")
            else:
                st.markdown(f"### {verse_meter_label}: **{disp_meter}**")

            # 2. Line-by-Line Summary Table
            lines_data = res_data.get("line", [])
            summary_rows = []
            
            for line_entry in lines_data:
                line_str = line_entry.get("line", "")
                r = line_entry.get("result", {})

                chanda_val = r.get("display_chanda") or r.get("chanda") or ""
                jaati_val = r.get("display_jaati") or r.get("jaati") or ""
                length_val = r.get("display_length") or r.get("length") or 0
                matra_val = r.get("display_matra") or r.get("matra") or 0
                gana_val = r.get("display_gana") or r.get("gana") or ""

                line_out = convert_from_devanagari(line_str, output_script_sel)
                chanda_out = convert_from_devanagari(chanda_val, output_script_sel)
                jaati_out = convert_from_devanagari(jaati_val, output_script_sel)
                gana_out = convert_from_devanagari(gana_val, output_script_sel)

                if is_sa:
                    summary_rows.append({
                        col_pada: clean_sanskrit_text(line_out),
                        col_meter: clean_sanskrit_text(chanda_out),
                        col_jaati: clean_sanskrit_text(jaati_out),
                        col_syllables: clean_sanskrit_text(length_val),
                        col_matras: clean_sanskrit_text(matra_val),
                        col_ganas: clean_sanskrit_text(gana_out)
                    })
                else:
                    summary_rows.append({
                        col_pada: line_out,
                        col_meter: str(chanda_out),
                        col_jaati: str(jaati_out),
                        col_syllables: length_val,
                        col_matras: matra_val,
                        col_ganas: str(gana_out)
                    })

            if summary_rows:
                st.markdown(f"#### {table_header_line}")
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            # 3. Syllable Matrix and Scansion Display
            st.markdown(f"#### {table_header_scansion}")
            for idx, line_entry in enumerate(lines_data):
                line_str = line_entry.get("line", "")
                r = line_entry.get("result", {})
                raw_syllables = r.get("display_syllables") or r.get("syllables") or []
                lg_list = r.get("display_lg") or r.get("lg") or []

                if not raw_syllables:
                    continue

                # Merge pure halantas (व + म् -> वम्) & conjunct onsets (ल + म्ब्य -> लम्ब् + य)
                realigned_syllables, realigned_lg = realign_phonetic_syllables(raw_syllables, lg_list)

                # Script conversion
                line_disp = convert_from_devanagari(line_str, output_script_sel)
                syllables_disp = [convert_from_devanagari(s, output_script_sel) for s in realigned_syllables]
                lg_disp = [convert_from_devanagari(x, output_script_sel) for x in realigned_lg]

                if is_sa:
                    disp_line = clean_sanskrit_text(line_disp)
                    st.markdown(f"**{col_pada} {to_devanagari_numerals(idx + 1)} । {disp_line}**")
                    syllables_disp = [clean_sanskrit_text(s) for s in syllables_disp]
                    lg_disp = [clean_sanskrit_text(x) for x in lg_disp]
                else:
                    st.markdown(f"**Line {idx + 1}: {line_disp}**")

                # HTML grid display
                table_html = """
                <div style="overflow-x:auto; margin-bottom: 22px;">
                    <table style="width:100%; border-collapse: collapse; text-align: center; font-size: 15px;">
                        <tr style="border-bottom: 1px solid #c0c0c0; background-color: rgba(128, 128, 128, 0.08);">
                            <th style="padding: 6px 12px; font-weight: 600; text-align: left; min-width: 90px;">""" + row_syllable + """</th>"""
                for s in syllables_disp:
                    table_html += f'<td style="padding: 6px 10px; border-left: 1px solid #e0e0e0;">{s}</td>'
                
                table_html += f"""</tr>
                        <tr style="border-bottom: 1px solid #c0c0c0;">
                            <th style="padding: 6px 12px; font-weight: 600; text-align: left; min-width: 90px;">""" + row_nature + """</th>"""
                for lg in lg_disp:
                    table_html += f'<td style="padding: 6px 10px; border-left: 1px solid #e0e0e0;">{lg}</td>'
                
                table_html += """</tr>
                    </table>
                </div>"""
                
                st.markdown(table_html, unsafe_allow_html=True)

        except Exception as e:
            if is_sa:
                st.error("दोषः सञ्जातः ॥")
            else:
                st.error(f"Analysis error: {e}")

# Footers with collapsible expanders (matching Sakhaa architecture)
st.write("")
st.write("")
st.markdown("---")

if is_sa:
    t_links_title = "🔗 अन्यानि तन्त्रांशाणि"
    t_links = """
* 🧮 [**सङ्ख्या**](https://sankhya.streamlit.app) संस्कृतसङ्ख्यापरिवर्तकः
* 🧩 [**सन्धीराट्**](https://sandhify.streamlit.app) सन्धियोजकः
* 🐻‍❄️ [**सखा**](https://sakhaa.streamlit.app) संस्कृतपदपरिचयकृत्
* 📚 [**संस्कृतजालस्थानानां सूचिः**](https://anotepad.com/note/read/qx4598pk)
"""
    t_report_title = "दोषावलोकनम्"
    t_report_body = (
        "<strong>दोषावलोकनम्।</strong> यत्र कुत्रापि दोषाः दृश्यन्ते सद्य एव विद्युत्पत्रेण गिड्ढब्जालस्थले वा सूच्यताम्<br><br>"
        "<div style='text-align: center; margin-top: 15px;'>"
        "<a href='mailto:samvadah@proton.me' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black; margin-right: 10px;'>विद्युत्पत्रम्</a>"
        "<a href='https://github.com/samvadah/chhanda/issues' target='_blank' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black;'>गिड्ढब्जालस्थलम्</a>"
        "</div>"
    )
    t_footer = '<div style="text-align: center; font-size: 0.9rem; color: #6b7280; margin-top: 2.5rem;">भारतदेशे श्रद्धया रचितं <a href="https://linktr.ee/samvadah" target="_blank" rel="noopener" style="color: #6b7280; text-decoration: underline;">संस्कृतसंवादेन</a>।</div>'

    with st.expander(t_links_title, expanded=False):
        st.markdown(t_links)

    with st.expander(t_report_title, expanded=False):
        st.markdown(f"<div style='color: gray; font-size: 0.9em;'>{t_report_body}</div>", unsafe_allow_html=True)

    st.markdown(t_footer, unsafe_allow_html=True)
else:
    t_links_title_en = "🔗 Related Tools"
    t_links_en = """
* 🧮 [**Sankhya**](https://sankhya.streamlit.app) - Sanskrit Numeral Converter
* 🧩 [**Sandhify**](https://sandhify.streamlit.app) - Sanskrit Sandhi Joiner
* 🐻‍❄️ [**Sakhaa**](https://sakhaa.streamlit.app) - Sanskrit Morphological Analyzer
* 📚 [**Annotated List of Sanskrit Websites**](https://anotepad.com/note/read/qx4598pk)
"""
    t_report_title_en = "Report Mistakes"
    t_report_body_en = (
        "<strong>Mistakes / Errors:</strong> If you spot any incorrect identifications or prosodic analyses, please report them immediately via email or GitHub.<br><br>"
        "<div style='text-align: center; margin-top: 15px;'>"
        "<a href='mailto:samvadah@proton.me' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black; margin-right: 10px;'>Report via Email</a>"
        "<a href='https://github.com/samvadah/chhanda/issues' target='_blank' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black;'>Open GitHub Issue</a>"
        "</div>"
    )
    t_footer_en = '<div style="text-align: center; font-size: 0.9rem; color: #6b7280; margin-top: 2.5rem;">Crafted with devotion in India by <a href="https://linktr.ee/samvadah" target="_blank" rel="noopener" style="color: #6b7280; text-decoration: underline;">Sanskrit Samvadah</a>.</div>'

    with st.expander(t_links_title_en, expanded=False):
        st.markdown(t_links_en)

    with st.expander(t_report_title_en, expanded=False):
        st.markdown(f"<div style='color: gray; font-size: 0.9em;'>{t_report_body_en}</div>", unsafe_allow_html=True)

    st.markdown(t_footer_en, unsafe_allow_html=True)
