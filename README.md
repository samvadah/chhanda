# 📜 छन्दोज्ञानम् (Chandojñānam)
### Sanskrit Meter Identification and Prosodic Scansion System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Transliteration](https://img.shields.io/badge/Transliteration-Aksharamukha-orange.svg)](https://aksharamukha.appspot.com/)

**छन्दोज्ञानम् (Chandojñānam)** is a modern, web-based Sanskrit meter identification and metrical scansion system powered by [Streamlit](https://streamlit.io). It scans Sanskrit verses (ślokas), calculates mātrā and akṣara counts, performs gaṇa-vibhāga, identifies classical meters, and formats syllables phonetically for prosodic clarity.

---

## ✨ Features

- **Accurate Meter Identification**: Identifies classical Sanskrit meters (e.g., *Anuṣṭubh*, *Indravajrā*, *Upendravajrā*, *Śārdūlavikrīḍita*, *Mandākrāntā*, *Vasantatilakā*, etc.) with fallback to line-level analysis.
- **Phonetic Syllable Segmentation (लघु-गुरु स्पष्टीकरणम्)**:
  - **Conjunct Coda Transfer**: Automatically shifts conjunct consonants to preceding syllables (e.g., `ल` + `म्ब्य` → **`लम्ब्` + `य`**, `ध` + `र्म` → **`धर्` + `म`**) so it is immediately visually evident why a syllable is *Guru* before a conjunct (*संयोगे परे गुरु*).
  - **Halanta Preservation**: Pure halanta consonants merge cleanly with their vowel-bearing syllable (e.g., `व` + `म्` → **`वम्`**).
- **Dual Language Interface**:
  - **Classical Sanskrit Mode (संस्कृतम्)**: Designed strictly according to classical Sanskrit formatting, replacing English punctuation with traditional daṇḍas (`।` and `॥`) and Devanagari numerals.
  - **English Mode**: Clean, publication-grade tabular layout.
- **Multi-Script Transliteration**:
  - Powered by **Aksharamukha** with auto-detection for input scripts.
  - Supports 20+ scripts including Devanagari, IAST, SLP1, Harvard-Kyoto, Telugu, Kannada, Bengali, Malayalam, Grantha, and Sharada.
- **Fuzzy Matching Support**: Capable of detecting approximate metrical patterns when slight poetic variations or reading errors exist.
- **Built-in Documentation**: Direct access to the prosodic guidelines and meter database.

---

## 🖥️ Live Demonstration

The application is hosted via Streamlit Community Cloud:
👉 **[Open Chandojñānam](https://share.streamlit.io/)** *(replace with your public app URL once deployed)*

---

## 📊 Sample Output

### Verse Input:
```text
धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।
मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥
```

### Analysis:
- **Identified Meter**: `अनुष्टुभ्` (Anuṣṭubh)
- **Line Analysis Table**:
  | Line / Pada | Meter | Jaati | Syllables | Matras | Gana Sequence |
  | :--- | :--- | :--- | :---: | :---: | :--- |
  | धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः | अनुष्टुभ् (पाद 1-2) | अष्टिः | 16 | 27 | मरतयजग |
  | मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय | अनुष्टुभ् (पाद 1-2) | अष्टिः | 16 | 23 | ररभजजल |

- **Phonetic Scansion Matrix**:
  | वर्णः (Syllable) | धर् | मक् | षेत् | रे | कु | रु | क्षेत् | रे | स | म | वे | ता | यु | युत् | स | वः |
  | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
  | **प्रकृतिः (Weight)** | **ग** | **ग** | **ग** | **ग** | **ल** | **ग** | **ग** | **ग** | **ल** | **ल** | **ग** | **ग** | **ल** | **ग** | **ल** | **ग** |

---

## 🚀 Installation & Local Setup

If running locally or testing in a development environment:

### 1. Clone the repository
```bash
git clone https://github.com/samvadah/chhanda.git
cd chhanda
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup configuration
Copy the configuration template:
```bash
cp settings.sample.py settings.py
```

### 5. Launch the Streamlit application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## ☁️ Deployment on Streamlit Cloud

1. Fork or push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app**, select your repository `samvadah/chhanda`.
4. Ensure:
   - **Branch**: `master` (or `main`)
   - **Main file path**: `app.py`
5. Click **Deploy!**

---

## 📦 Project Structure

```text
├── app.py                 # Streamlit web application (UI & formatting engine)
├── chanda.py              # Core prosodic identification engine
├── settings.sample.py     # Configuration template
├── settings.py            # Active local configuration (created from sample)
├── requirements.txt       # Dependencies (streamlit, aksharamukha, etc.)
├── data/                  # Metrical definitions, rules, and prosodic databases
└── README.md              # Project documentation
```

---

## 🔗 Related Tools by Sanskrit Samvadah

* 🧮 [**सङ्ख्या (Sankhya)**](https://sankhya.streamlit.app) - Sanskrit Numeral Converter
* 🧩 [**सन्धीराट् (Sandhirat)**](https://sandhify.streamlit.app) - Sanskrit Sandhi Joiner
* 🐻‍❄️ [**सखा (Sakhaa)**](https://sakhaa.streamlit.app) - Sanskrit Morphological Analyzer
* 📚 [**Annotated Directory of Sanskrit Tools**](https://anotepad.com/note/read/qx4598pk)

---

## 📢 Issues and Feedback

If you encounter incorrect metrical identifications or bugs:
- Open an issue on [GitHub Issues](https://github.com/samvadah/chhanda/issues)
- Or email: `samvadah@proton.me`

---

## 📜 Acknowledgements & Attribution

- Built upon the Sanskrit prosodic engine developed by **Hrishikesh Terdalkar** ([`hrishikeshrt/chandojnanam`](https://github.com/hrishikeshrt/chandojnanam)), originating from the Jnanasangraha Project at IIT Kanpur.
- Script transliteration provided by [Aksharamukha](https://github.com/virtualvinodh/aksharamukha).
- Reference Help: [IIT Kanpur Jnanasangraha Chanda Guide](https://web.archive.org/web/20250620200354/https://sanskrit.iitk.ac.in/jnanasangraha/chanda/help).

---

## ⚖️ License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**, preserving the copyleft terms of the upstream project. See the [LICENSE](LICENSE) file for full details.
