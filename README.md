# BudgetLens AI — Budget Variance Analyzer

## End-Term Project
**Use Case:** #8 Budget variance analyzer  
**Format:** App  
**Stack:** Streamlit + Python + Pandas + Google Gemini API

### What the app does
1. Accepts CSV/Excel data with `Category`, `Budget`, and `Actual`.
2. Validates missing/wrong/negative values.
3. Calculates variance and variance % using deterministic Python calculations.
4. Identifies the top 3 adverse line items.
5. Uses Gemini to generate executive commentary, possible explanations to validate, and recommended actions.
6. Allows the user to download the analyzed data.

### Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

The app can run in demo mode without an API key. Enter a Gemini API key in the sidebar to activate AI commentary.

### Deploy
Push this folder to a GitHub repository and deploy it using Streamlit Community Cloud. Add the required dependencies from `requirements.txt`. For a classroom demo, entering the Gemini key in the sidebar is simplest; for a more secure deployment, use Streamlit Secrets instead.

### Input format
| Category | Budget | Actual |
|---|---:|---:|
| Marketing | 350000 | 430000 |

### Demo story
The sample dataset intentionally contains material overspends in Marketing, Travel, Recruitment and Professional Fees. The app first calculates these variances, then asks Gemini to interpret the numbers without inventing unsupported causes.

### Important limitation
AI commentary is an analytical aid. The app does not know the transaction-level reason for a variance unless that information is supplied, so hypotheses must be validated by finance staff.
