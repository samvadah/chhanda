import os
import re
import inspect
import pandas as pd
import streamlit as st
import chanda

try:
    import settings
except ImportError:
    settings = None

st.set_page_config(page_title="Chandojnanam", layout="wide")

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

# Re-align syllables so conjunct codas attach to the preceding syllable (e.g. ल + म्ब्य -> लम्ब् + य)
def realign_phonetic_syllables(syllables):
    if not syllables:
        return []
    syls = list(syllables)
    conjunct_pattern = re.compile(r"^((?:[\u0915-\u0939\u0958-\u095F]\u094D)+)(.+)$")
    
    for i in range(1, len(syls)):
        m = conjunct_pattern.match(syls[i])
        if m:
            coda = m.group(1)       # Coda consonant cluster with virama (e.g. 'म्ब्', 'र्', 'त्')
            remainder = m.group(2)  # Remaining vowel-bearing part (e.g. 'य', 'म', 'स')
            syls[i - 1] += coda
            syls[i] = remainder
            
    return syls

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

    # Fallback to line-level identification
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
            raw_output = run_identification(analyzer, verse_input.strip(), fuzzy=fuzzy_enabled)
            res_data = raw_output.get("result", {}) if isinstance(raw_output, dict) else {}

            # 1. Primary Verse-level Meter Identification
            primary_meter = extract_primary_meter(res_data) or unknown_meter

            if is_sa:
                clean_meter = clean_sanskrit_text(primary_meter)
                st.markdown(f"### {verse_meter_label} । {clean_meter} ॥")
            else:
                st.markdown(f"### {verse_meter_label}: **{primary_meter}**")

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
                raw_syllables = r.get("display_syllables") or r.get("syllables") or []
                lg_list = r.get("display_lg") or r.get("lg") or []

                if not raw_syllables:
                    continue

                # Re-align codas phonetically (e.g. ल + म्ब्य -> लम्ब् + य)
                realigned_syllables = realign_phonetic_syllables(raw_syllables)

                if is_sa:
                    disp_line = clean_sanskrit_text(line_str)
                    st.markdown(f"**{col_pada} {to_devanagari_numerals(idx + 1)} । {disp_line}**")
                    syllables_disp = [clean_sanskrit_text(s) for s in realigned_syllables]
                    lg_disp = [clean_sanskrit_text(x) for x in lg_list]
                else:
                    st.markdown(f"**Line {idx + 1}: {line_str}**")
                    syllables_disp = realigned_syllables
                    lg_disp = lg_list

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

# Footer, Tool Links, and Issue Reporting Section
st.write("")
st.write("")
st.divider()

if is_sa:
    t_links_title = "🔗 अन्यानि तन्त्रांशाणि"
    t_links = """
* 🧮 [**सङ्ख्या**](https://sankhya.streamlit.app) संस्कृतसङ्ख्यापरिवर्तकः
* 🧩 [**सन्धीराट्**](https://sandhify.streamlit.app) सन्धियोजकः
* 📰 [**संस्कृतवार्ताः**](https://sanskritnews.streamlit.app) संस्कृतवार्ताजनित्रम्
* [**सखा**](https://sakhaa.streamlit.app) संस्कृतपदपरिचयकृत्
* 📚 [**संस्कृतजालस्थानानां सूचिः**](https://anotepad.com/note/read/qx4598pk)
"""
    t_report_title = "दोषावलोकनम्"
    t_report_body = (
        "<strong>दोषावलोकनम्।</strong> यत्र कुत्रापि दोषाः दृश्यन्ते सद्य एव विद्युत्पत्रेण गिड्ढब्जालस्थले वा सूच्यताम्<br><br>"
        "<div style='text-align: center; margin-top: 15px;'>"
        "<a href='mailto:samvadah@proton.me' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black; margin-right: 10px;'>विद्युत्पत्रम्</a>"
        "<a href='https://github.com/samvadah/chhana/issues' target='_blank' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black;'>गिड्ढब्जालस्थलम्</a>"
        "</div>"
    )
    t_footer = '<div style="text-align: center; font-size: 0.9rem; color: #6b7280; margin-top: 2.5rem;">भारतदेशे श्रद्धया रचितं <a href="https://linktr.ee/samvadah" target="_blank" rel="noopener" style="color: #6b7280; text-decoration: underline;">संस्कृतसंवादेन</a>।</div>'

    st.markdown(f"### {t_links_title}")
    st.markdown(t_links)
    st.markdown("---")
    st.markdown(f"### {t_report_title}")
    st.markdown(t_report_body, unsafe_allow_html=True)
    st.markdown(t_footer, unsafe_allow_html=True)
else:
    t_links_title_en = "Related Tools"
    t_links_en = """
* [**Sankhya**](https://sankhya.streamlit.app) Sanskrit Numeral Converter
* [**Sandhirat**](https://sandhify.streamlit.app) Sanskrit Sandhi Joiner
* [**Sanskrit News**](https://sanskritnews.streamlit.app) Sanskrit News Generator
* [**Sakhaa**](https://sakhaa.streamlit.app) Sanskrit Morphological Analyzer
* [**Sanskrit Websites Directory**](https://anotepad.com/note/read/qx4598pk)
"""
    t_report_title_en = "Issue Reporting"
    t_report_body_en = (
        "<strong>Issue Reporting:</strong> If you find any issues, please report them via email or on GitHub.<br><br>"
        "<div style='text-align: center; margin-top: 15px;'>"
        "<a href='mailto:samvadah@proton.me' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black; margin-right: 10px;'>Email</a>"
        "<a href='https://github.com/samvadah/chhanda/issues' target='_blank' style='text-decoration: none; padding: 5px 10px; background-color: #f0f2f6; border-radius: 5px; color: black;'>GitHub Issues</a>"
        "</div>"
    )
    t_footer_en = '<div style="text-align: center; font-size: 0.9rem; color: #6b7280; margin-top: 2.5rem;">Crafted with devotion in India by <a href="https://linktr.ee/samvadah" target="_blank" rel="noopener" style="color: #6b7280; text-decoration: underline;">Sanskrit Samvadah</a>.</div>'

    st.markdown(f"### {t_links_title_en}")
    st.markdown(t_links_en)
    st.markdown("---")
    st.markdown(f"### {t_report_title_en}")
    st.markdown(t_report_body_en, unsafe_allow_html=True)
    st.markdown(t_footer_en, unsafe_allow_html=True)
