import streamlit as st
import chanda
import json

st.set_page_config(page_title="Chandojnanam", page_icon="📜")

st.title("📜 Chandojñānam")
st.caption("Sanskrit Meter Identification System (Streamlit Port)")

# Load the core Chanda engine
@st.cache_resource
def load_analyzer():
    return chanda.Chanda()

try:
    analyzer = load_analyzer()
except Exception as e:
    st.error(f"Failed to load engine. Ensure settings.py exists. Error: {e}")
    st.stop()

# Input area
default_verse = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥"
verse = st.text_area("Enter Sanskrit verse:", value=default_verse, height=100)

fuzzy = st.checkbox("Enable Fuzzy Matching", value=True)

if st.button("Identify Meter", type="primary"):
    if verse.strip():
        with st.spinner("Analyzing verse..."):
            try:
                # The engine has an analyze function that returns the meter and scansion
                result = analyzer.analyze(verse.strip(), fuzzy=fuzzy)
                
                st.success("Analysis Complete!")
                
                # Streamlit's json formatter is great for neatly displaying Python dictionaries/results
                st.json(result)
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")
    else:
        st.warning("Please enter a verse to analyze.")
