import os
import inspect
import streamlit as st
import chanda

# Try importing settings if available
try:
    import settings
except ImportError:
    settings = None

st.set_page_config(page_title="Chandojñānam", page_icon="📜", layout="centered")

st.title("📜 Chandojñānam (छन्दोज्ञानम्)")
st.caption("Sanskrit Meter Identification and Scansion")

# 1. Determine data directory path
DATA_PATH = None
if settings:
    for attr in ["DATA_PATH", "DATA_DIR", "CHANDA_DATA_DIR", "CHANDA_DATA"]:
        if hasattr(settings, attr):
            DATA_PATH = getattr(settings, attr)
            break

if not DATA_PATH or not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 2. Cache & load the Chanda engine
@st.cache_resource
def load_analyzer(path):
    return chanda.Chanda(path)

try:
    analyzer = load_analyzer(DATA_PATH)
except Exception as e:
    st.error(f"Failed to initialize Chanda with data path '{DATA_PATH}': {e}")
    st.stop()

# Helper function to call identify_from_text dynamically
def run_chanda_identification(analyzer, text, fuzzy=True):
    # Target method is identify_from_text
    method = getattr(analyzer, "identify_from_text", None) or getattr(analyzer, "process_text", None)
    if method is None:
        raise AttributeError("Could not find an identification method on Chanda instance.")
    
    # Inspect arguments expected by the method
    sig = inspect.signature(method)
    kwargs = {}
    params = sig.parameters
    
    # Pass arguments based on what the method accepts
    for param_name in params:
        if param_name in ["fuzzy", "fuzzy_match", "approximate"]:
            kwargs[param_name] = fuzzy
        elif param_name in ["text", "input_text", "verse"]:
            kwargs[param_name] = text

    # Call with kwargs if matched, otherwise pass text as first argument
    if kwargs:
        return method(**kwargs)
    return method(text)

# UI Elements
default_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
verse = st.text_area("Enter Sanskrit verse (Devanagari or Romanized):", value=default_verse, height=120)

fuzzy = st.checkbox("Enable fuzzy matching (approximate match)", value=True)

if st.button("Identify Meter", type="primary"):
    if verse.strip():
        with st.spinner("Analyzing verse..."):
            try:
                result = run_chanda_identification(analyzer, verse.strip(), fuzzy=fuzzy)
                
                st.success("Analysis Complete!")

                # Try to summarize or format if helper methods exist
                if hasattr(analyzer, "format_summary"):
                    try:
                        summary = analyzer.format_summary(result)
                        st.subheader("Summary")
                        st.write(summary)
                    except Exception:
                        pass
                
                # Show full structured result
                st.subheader("Details")
                if isinstance(result, (dict, list)):
                    st.json(result)
                else:
                    st.write(result)

            except Exception as e:
                st.error(f"Analysis failed: {e}")
    else:
        st.warning("Please enter a verse.")
