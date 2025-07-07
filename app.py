import streamlit as st
import pandas as pd
from difflib import get_close_matches

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("sample.csv")

df = load_data()

# Valid types
valid_types = ["PIPE", "NIPPLE", "VALVE", "BOLT", "STUD", "FLANGE", "STOPPER", "STOPPLE", "ELL", "ELBOW"]
df['UPPER_DESC'] = df['MATERIAL_NUMBER_TEXT'].astype(str).str.upper()
filtered_df = df[df['UPPER_DESC'].str.split(',').str[0].str.strip().isin(valid_types)]

# --- Validators ---
def validate_pipe(parts):
    return (
        parts[0] == "PIPE" and
        any(x in parts for x in ["COAT", "WRAP", "DUALCOAT"]) and
        any("W" in p for p in parts) and
        any(x in parts for x in ["X", "Y", "API"]) and
        any(p.replace('.', '', 1).isdigit() for p in parts)
    )

def validate_nipple(parts):
    return (
        parts[0] == "NIPPLE" and
        any("X" in p for p in parts) and
        "TOE" in parts and
        any(x in parts for x in ["BLK", "GALV", "SC", "ZINC"])
    )

def validate_flange(parts):
    return (
        parts[0] == "FLANGE" and
        any(x in parts for x in ["WN", "SLIPON", "THRD", "RF", "FF", "RTJ"]) and
        any(p.isdigit() or "150A" in p or "300A" in p or "600A" in p for p in parts) and
        any(x in parts for x in ["CS", "CARBON", "STL"])
    )

def validate_bolt(parts):
    return (
        parts[0] in ["BOLT", "STUD"] and
        any("X" in p for p in parts) and
        any("STEEL" in p or "CARBON" in p for p in parts)
    )

def validate_valve(parts):
    return (
        parts[0] == "VALVE" and
        any(x in parts for x in ["BALL", "GATE", "CHECK", "PLUG"]) and
        any(p.isdigit() or '"' in p for p in parts) and
        any(x in parts for x in ["150A", "300A", "600A"]) and
        any(x in parts for x in ["FE RF", "FLANGED", "THRD"]) and
        any(x in parts for x in ["FP", "FULL PORT"]) and
        any(p for p in parts if len(p) > 4 and p.isalnum())
    )

def validate_ell(parts):
    return (
        parts[0] in ["ELL", "ELBOW"] and
        any(x in parts for x in ["45", "90"]) and
        any(x in parts for x in ["WELD", "THRD", "SOCKET"]) and
        any(p.replace('"', '').isdigit() for p in parts) and
        any(x in parts for x in ["LR", "SR"]) and
        any(x in parts for x in ["X", "Y", "API"])
    )

def validate_stopper(parts):
    return (
        parts[0] in ["STOPPER", "STOPPLE"] and
        any("WELD" in p or "THRD" in p for p in parts) and
        any(p.replace('"', '').isdigit() for p in parts) and
        any("#" in p or "150A" in p or "ANSI" in p for p in parts)
    )

def classify_and_suggest(desc, ref_df):
    parts = [p.strip().upper() for p in desc.split(",")]
    if not parts:
        return "Invalid", "Empty description", "No suggestion"

    type_ = parts[0]
    if type_ == "PIPE" and validate_pipe(parts): return "Valid", "", ""
    elif type_ == "NIPPLE" and validate_nipple(parts): return "Valid", "", ""
    elif type_ == "FLANGE" and validate_flange(parts): return "Valid", "", ""
    elif type_ in ["BOLT", "STUD"] and validate_bolt(parts): return "Valid", "", ""
    elif type_ == "VALVE" and validate_valve(parts): return "Valid", "", ""
    elif type_ in ["ELL", "ELBOW"] and validate_ell(parts): return "Valid", "", ""
    elif type_ in ["STOPPER", "STOPPLE"] and validate_stopper(parts): return "Valid", "", ""
    else:
        reason = f"Failed format rules for {type_}"
        suggestions = ref_df[ref_df['MATERIAL_NUMBER_TEXT'].str.upper().str.startswith(type_)]['MATERIAL_NUMBER_TEXT'].tolist()
        match = get_close_matches(desc.upper(), suggestions, n=1, cutoff=0.3)
        return "Invalid", reason, match[0] if match else "No suggestion"

# --- Streamlit UI ---
st.set_page_config(page_title="Material Description Validator", layout="wide")
st.title("🧾 Smart Material Description Validator & Auto-Suggester")

edited_rows = []

for idx, row in filtered_df.iterrows():
    desc = row['MATERIAL_NUMBER_TEXT']
    status, reason, suggestion = classify_and_suggest(desc, df)

    with st.expander(f"{desc}"):
        st.markdown(f"**Status:** {'✅ Valid' if status == 'Valid' else '❌ Invalid'}")
        if reason:
            st.markdown(f"**Reason:** {reason}")
        if suggestion and suggestion != "No suggestion":
            st.markdown(f"**Suggested Completion:** `{suggestion}`")

        new_val = st.text_input("Edit Description (if needed):", value=desc, key=f"edit_{idx}")
        if st.button("💾 Save", key=f"save_{idx}"):
            edited_rows.append({
                "Original": desc,
                "Corrected": new_val
            })
            st.success("Saved!")

if edited_rows:
    st.subheader("📘 Saved Corrections")
    st.dataframe(pd.DataFrame(edited_rows))
