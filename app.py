import os
import streamlit as st
import chanda

# Try importing settings if available
try:
    import settings
except ImportError:
    settings = None

st.set_page_config(page_title="Chandojñānam", page_icon="📜", layout="centered")

st.title("📜 Chandojñānam (छन्दोज्ञानम्)")
st.caption("Sanskrit Meter Identification System")

# 1. Determine the path to the 'data' directory
DATA_PATH = None
if settings:
    for attr in ["DATA_PATH", "DATA_DIR", "CHANDA_DATA_DIR", "CHANDA_DATA"]:
        if hasattr(settings, attr):
            DATA_PATH = getattr(settings, attr)
            break

if not DATA_PATH or not os.path.exists(DATA_PATH):
    # Fallback to the 'data' directory inside the repository
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 2. Load the analyzer with the required data_path argument
@st.cache_resource
def load_analyzer(path):
    return chanda.Chanda(path)

try:
    analyzer = load_analyzer(DATA_PATH)
except Exception as e:
    st.error(f"Failed to load engine using data path '{DATA_PATH}'. Error: {e}")
    st.stop()

# Helper function to call whichever analysis method is defined in chanda.py
def identify_text(analyzer, text, fuzzy=True):
    for method_name in ["identify", "analyze", "classify", "identify_meter", "scan"]:
        if hasattr(analyzer, method_name):
            func = getattr(analyzer, method_name)
            try:
                return func(text, fuzzy=fuzzy)
            except TypeError:
                return func(text)
    if callable(analyzer):
        return analyzer(text)
    raise AttributeError(f"No suitable method found. Available: {[m for m in dir(analyzer) if not m.startswith('_')]}")

# Input section
default_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
verse = st.text_area("Enter Sanskrit verse (Devanagari or transliterated):", value=default_verse, height=120)
fuzzy = st.checkbox("Enable fuzzy matching", value=True)

if st.button("Identify Meter", type="primary"):
    if verse.strip():
        with st.spinner("Analyzing verse..."):
            try:
                result = identify_text(analyzer, verse.strip(), fuzzy=fuzzy)
                st.subheader("Result")
                if isinstance(result, (dict, list)):
                    st.json(result)
                else:
                    st.write(result)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    else:
        st.warning("Please enter a verse.")
