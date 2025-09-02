# app.py (with DB logging + Analytics page)
import streamlit as st
import pandas as pd
import time
from detector_v2 import analyze_text as detect_ai_content
import db_utils

# Initialize DB
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
            result = detect_ai_content(text)
            pred = result["prediction"]
            conf = result.get("confidence", 0.0)
            feats = result.get("features", {})
            contribs = result.get("contributions", {})
            top = result.get("top_contributors", [])
            note = result.get("note", "")

            # Log result to DB
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
            st.subheader("Feature breakdown")
            if feats:
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

            if top:
                st.subheader("Top indicators influencing this prediction")
                for label, val in top:
                    st.write(f"- **{label}** → {val:.2f} percent points")

            if note:
                st.info(note)

elif page == "Analytics":
    st.title("📊 Analytics Dashboard")

    rows = db_utils.fetch_all()
    if not rows:
        st.info("No history yet. Run some detections first!")
    else:
        df = pd.DataFrame(rows, columns=["ID", "Timestamp", "Text Hash", "Prediction", "Confidence", "Word Count"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="s")

        # Show table
        st.subheader("History")
        st.dataframe(df[["Timestamp", "Prediction", "Confidence", "Word Count"]], use_container_width=True)

        # Charts
        st.subheader("Trends")
        st.line_chart(df[["Timestamp", "Confidence"]].set_index("Timestamp"))

        st.subheader("AI vs Human Distribution")
        st.bar_chart(df["Prediction"].value_counts())
