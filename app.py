import io
import os
import pandas as pd
import streamlit as st
from google import genai

st.set_page_config(page_title="BudgetLens AI", page_icon="💰", layout="wide")

st.title("💰 BudgetLens AI")
st.caption("AI-powered Budget Variance Analyzer | End-Term Project")
st.markdown(
    "Upload **Budget vs Actual** data. The app calculates the variance deterministically, "
    "then uses Gemini to explain the largest deviations and suggest management actions."
)

REQUIRED = {"Category", "Budget", "Actual"}

def clean_data(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if not REQUIRED.issubset(df.columns):
        raise ValueError("The file must contain exactly these minimum columns: Category, Budget, Actual.")
    df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
    df["Actual"] = pd.to_numeric(df["Actual"], errors="coerce")
    df["Category"] = df["Category"].astype(str).str.strip()
    df = df.dropna(subset=["Category", "Budget", "Actual"])
    if (df["Budget"] < 0).any() or (df["Actual"] < 0).any():
        raise ValueError("Budget and Actual values cannot be negative.")
    if df.empty:
        raise ValueError("No valid rows found.")
    return df

def calculate_variance(df):
    out = df.copy()
    out["Variance"] = out["Actual"] - out["Budget"]
    out["Variance %"] = out.apply(
        lambda r: (r["Variance"] / r["Budget"] * 100) if r["Budget"] != 0 else 0, axis=1
    )
    out["Status"] = out["Variance"].apply(
        lambda x: "Overspend" if x > 0 else ("Underspend" if x < 0 else "On Budget")
    )
    return out

def build_prompt(df, top3, total_budget, total_actual, total_var, total_pct):
    rows = df[["Category","Budget","Actual","Variance","Variance %","Status"]].round(2).to_dict("records")
    top = top3[["Category","Budget","Actual","Variance","Variance %","Status"]].round(2).to_dict("records")
    return f"""
You are a finance analyst supporting a management team.
Analyze the following budget-versus-actual expense data.

IMPORTANT RULES:
1. Use only the numbers supplied below.
2. Do not invent causes such as inflation, hiring, vendor changes, etc.
3. If a cause is not present in the data, explicitly call it a hypothesis that needs validation.
4. Focus on material adverse variances and practical management actions.
5. Keep the response concise and executive-friendly.
6. State that the app is an analytical aid, not a substitute for management review.

Totals:
Budget = {total_budget:.2f}
Actual = {total_actual:.2f}
Variance = {total_var:.2f}
Variance % = {total_pct:.2f}%

Top 3 adverse variances:
{top}

Full dataset:
{rows}

Return exactly these sections:
1. Executive insight
2. Top 3 drivers
3. Possible explanations to validate
4. Recommended actions
5. Data/AI limitation
"""

def call_gemini(prompt, api_key):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    return response.text

with st.sidebar:
    st.header("⚙️ Controls")
    api_key = st.text_input("Gemini API Key", type="password", help="Used only for this session.")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    st.markdown("---")
    st.info("Demo file format: Category | Budget | Actual")

if uploaded:
    try:
        if uploaded.name.lower().endswith(".csv"):
            raw = pd.read_csv(uploaded)
        else:
            raw = pd.read_excel(uploaded)
        df = clean_data(raw)
    except Exception as e:
        st.error(f"Input error: {e}")
        st.stop()
else:
    df = pd.read_csv("sample_budget.csv")
    st.success("Demo mode: sample budget data loaded. Upload your own file from the sidebar.")

result = calculate_variance(df)
total_budget = result["Budget"].sum()
total_actual = result["Actual"].sum()
total_var = result["Variance"].sum()
total_pct = (total_var / total_budget * 100) if total_budget else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Budget", f"₹{total_budget:,.0f}")
c2.metric("Total Actual", f"₹{total_actual:,.0f}")
c3.metric("Total Variance", f"₹{total_var:,.0f}", delta=f"{total_pct:.1f}%")
c4.metric("Adverse Items", int((result["Variance"] > 0).sum()))

st.subheader("📊 Variance Dashboard")
chart = result.set_index("Category")[["Budget", "Actual"]]
st.bar_chart(chart)

st.subheader("🔎 Detailed Variance Table")
display = result.copy()
display["Budget"] = display["Budget"].map(lambda x: f"₹{x:,.0f}")
display["Actual"] = display["Actual"].map(lambda x: f"₹{x:,.0f}")
display["Variance"] = display["Variance"].map(lambda x: f"₹{x:,.0f}")
display["Variance %"] = display["Variance %"].map(lambda x: f"{x:.1f}%")
st.dataframe(display, use_container_width=True, hide_index=True)

top3 = result.sort_values("Variance", ascending=False).head(3)
st.subheader("🚨 Top 3 Adverse Variances")
st.dataframe(top3[["Category","Budget","Actual","Variance","Variance %","Status"]], use_container_width=True, hide_index=True)

if st.button("✨ Generate AI Management Commentary", type="primary"):
    prompt = build_prompt(result, top3, total_budget, total_actual, total_var, total_pct)
    if not api_key:
        st.warning("No Gemini API key entered. Showing deterministic fallback commentary.")
        st.markdown(
            f"**Executive insight:** Actual spending is ₹{total_var:,.0f} above budget "
            f"({total_pct:.1f}%). The largest adverse variances are "
            f"{', '.join(top3['Category'].tolist())}. "
            "Management should validate the underlying transaction-level drivers before taking corrective action."
        )
    else:
        with st.spinner("Gemini is analyzing the variance drivers..."):
            try:
                answer = call_gemini(prompt, api_key)
                st.markdown(answer)
            except Exception as e:
                st.error("Gemini call failed. The deterministic calculations remain available.")
                st.code(str(e))

st.download_button(
    "⬇️ Download variance results",
    result.to_csv(index=False).encode("utf-8"),
    file_name="budget_variance_results.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("Privacy: Do not upload confidential financial data for the classroom demo. "
           "If a Gemini API key is used, the text prompt/data sent to the API is processed by the third-party model provider. "
           "This prototype is for educational use and should not be used as the sole basis for financial decisions.")
