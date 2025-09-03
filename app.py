# app.py (deployment-ready: Streamlit frontend calls Flask API)
import streamlit as st
import pandas as pd
import requests
import db_utils

# Set your API URL (update after deploying Flask API on Render)
API_URL = "https://ai-vs-human-detector-2.onrender.com"
HISTORY_URL = "https://ai-vs-human-detector-2.onrender.com"

# Initialize local DB (optional: only if you want Streamlit to also keep local logs)
db_utils.init_db()

st.set_page_config(page_title="AI vs Human Content Detector", page_icon="🤖", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("📌 Navigation", ["Detector", "Analytics"])

if page == "Detector":
    st.title("🤖 AI vs Human Content Detector")
    st.write("Paste some text below and click **Analyze**. Short inputs (<20 words) are treated as human by default.")

    text = st.text_area("✍️ Enter text to analyze:", height=220)

    if st.button("🔍 Analyze"):
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            try:
                resp = requests.post(API_URL, json={"text": text}, timeout=15)
                if resp.status_code == 200:
                    result = resp.json()
                else:
                    st.error(f"API error: {resp.status_code}")
                    result = {}
            except Exception as e:
                st.error(f"Connection error: {e}")
                result = {}

            if result:
                pred = result.get("prediction", "Unknown")
                conf = result.get("confidence", 0.0)
                feats = result.get("features", {})
                contribs = result.get("contributions", {})
                top = result.get("top_contributors", [])
                note = result.get("note", "")

                # Log result locally (optional)
                db_utils.log_result(text, pred, conf, feats.get("n_words", 0))

                # Show prediction
                st.subheader("Prediction")
                if "AI-generated" in pred:
                    st.error(pred)
                elif "Empty Text" in pred:
                    st.warning(pred)
                else:
                    st.success(pred)

                # Confidence
                st.subheader("Confidence")
                st.progress(int(conf * 100))
                st.write(f"**{conf*100:.1f}%** confidence ({conf})")

                # Feature breakdown
                if feats:
                    st.subheader("Feature breakdown")
                    df_feats = pd.DataFrame.from_dict(feats, orient='index', columns=['value']).reset_index()
                    df_feats.columns = ["Feature", "Value"]
                    st.table(df_feats)

                # Contributions
                if contribs:
                    st.subheader("Feature contributions (percent points)")
                    df_contrib = pd.DataFrame.from_dict(contribs, orient='index', columns=['percent'])
                    df_contrib.index.name = 'Feature'
                    df_contrib = df_contrib.sort_values(by='percent', ascending=True)
                    st.bar_chart(df_contrib)

                # Top contributors
                if top:
                    st.subheader("Top indicators influencing this prediction")
                    for label, val in top:
                        st.write(f"- **{label}** → {val:.2f} percent points")

                if note:
                    st.info(note)

elif page == "Analytics":
    st.title("📊 Analytics Dashboard")

    try:
        resp = requests.get(HISTORY_URL, timeout=15)
        if resp.status_code == 200:
            rows = resp.json()
        else:
            st.error(f"API error: {resp.status_code}")
            rows = []
    except Exception as e:
        st.error(f"Connection error: {e}")
        rows = []

    if not rows:
        st.info("No history yet. Run some detections first!")
    else:
        df = pd.DataFrame(rows)
        df["Timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

        # Show table
        st.subheader("History")
        st.dataframe(df[["Timestamp", "prediction", "confidence", "n_words"]], use_container_width=True)

        # Charts
        st.subheader("Trends")
        st.line_chart(df[["Timestamp", "confidence"]].set_index("Timestamp"))

        st.subheader("AI vs Human Distribution")
        st.bar_chart(df["prediction"].value_counts())
