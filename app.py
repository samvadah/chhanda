import os
import inspect
import pandas as pd
import streamlit as st
import chanda

try:
    import settings
except ImportError:
    settings = None

# Professional page configuration without emojis
st.set_page_config(page_title="Chandojnanam", layout="wide")

# Helper functions for Sanskrit mode (Strictly no English punctuation, only danda)
def to_devanagari_numerals(text):
    digit_map = str.maketrans("0123456789", "०१२३४५६७८९")
    return str(text).translate(digit_map)

def clean_sanskrit_text(text):
    if text is None:
        return ""
    text = to_devanagari_numerals(str(text))
    # Eliminate all English punctuation characters
    for char in ':,.-!?()[]{}"\';/\\_~`@#$%^&*+=':
        text = text.replace(char, " ")
    return " ".join(text.split())

# 1. Determine data directory path
DATA_PATH = None
if settings:
    for attr in ["DATA_PATH", "DATA_DIR", "CHANDA_DATA_DIR", "CHANDA_DATA"]:
        if hasattr(settings, attr):
            DATA_PATH = getattr(settings, attr)
            break

if not DATA_PATH or not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 2. Engine initialization
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

# Language selection
language = st.sidebar.radio(
    "Language / भाषा",
    options=["English", "संस्कृतम्"]
)
is_sa = (language == "संस्कृतम्")

# UI Localization
if is_sa:
    title_text = "छन्दोज्ञानम्"
    subtitle_text = "संस्कृतच्छन्दःपरिज्ञानप्रणाली ॥"
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
    input_label = "Sanskrit Verse"
    fuzzy_label = "Enable Approximate Matching"
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

# Main Headers
st.title(title_text)
st.caption(subtitle_text)

# Input Section
default_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
verse_input = st.text_area(input_label, value=default_verse, height=110)
fuzzy_enabled = st.checkbox(fuzzy_label, value=True)

if st.button(button_label, type="primary"):
    if not verse_input.strip():
        st.warning(empty_warning)
    else:
        try:
            raw_output = run_identification(analyzer, verse_input.strip(), fuzzy=fuzzy_enabled)
            res_data = raw_output.get("result", {}) if isinstance(raw_output, dict) else {}

            # 1. Primary Verse-level Meter Identification
            verse_matches = res_data.get("verse", [])
            primary_meter = unknown_meter
            if verse_matches and isinstance(verse_matches, list):
                first_match = verse_matches[0]
                if isinstance(first_match, dict) and "chanda" in first_match:
                    ch_info = first_match["chanda"]
                    if ch_info and isinstance(ch_info, list) and len(ch_info) > 0:
                        primary_meter = ch_info[0][0] if isinstance(ch_info[0], list) else ch_info[0]

            if is_sa:
                clean_meter = clean_sanskrit_text(primary_meter)
                st.markdown(f"### {verse_meter_label} । {clean_meter} ॥")
            else:
                st.markdown(f"### {verse_meter_label}: **{primary_meter}**")

            # 2. Line-by-Line Structured Summary Table
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

                if is_sa:
                    summary_rows.append({
                        col_pada: clean_sanskrit_text(line_str),
                        col_meter: clean_sanskrit_text(chanda_val),
                        col_jaati: clean_sanskrit_text(jaati_val),
                        col_syllables: clean_sanskrit_text(length_val),
                        col_matras: clean_sanskrit_text(matra_val),
                        col_ganas: clean_sanskrit_text(gana_val)
                    })
                else:
                    summary_rows.append({
                        col_pada: line_str,
                        col_meter: str(chanda_val),
                        col_jaati: str(jaati_val),
                        col_syllables: length_val,
                        col_matras: matra_val,
                        col_ganas: str(gana_val)
                    })

            if summary_rows:
                st.markdown(f"#### {table_header_line}")
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            # 3. Syllable Matrix and Scansion Display
            st.markdown(f"#### {table_header_scansion}")
            for idx, line_entry in enumerate(lines_data):
                line_str = line_entry.get("line", "")
                r = line_entry.get("result", {})
                syllables = r.get("display_syllables") or r.get("syllables") or []
                lg_list = r.get("display_lg") or r.get("lg") or []

                if not syllables:
                    continue

                if is_sa:
                    disp_line = clean_sanskrit_text(line_str)
                    st.markdown(f"**{col_pada} {to_devanagari_numerals(idx + 1)} । {disp_line}**")
                    syllables_disp = [clean_sanskrit_text(s) for s in syllables]
                    lg_disp = [clean_sanskrit_text(x) for x in lg_list]
                else:
                    st.markdown(f"**Line {idx + 1}: {line_str}**")
                    syllables_disp = syllables
                    lg_disp = lg_list

                # Cleanly formatted HTML grid for reliable horizontal alignment across screen sizes
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
