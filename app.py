"""
FinPilot — AI financial investigation (Streamlit front end)

Run:  streamlit run finpilot_app.py

Data: reads data/transactions.csv and data/ground_truth.csv when present.
If they are missing (or the columns can't be recognised) a built-in demo
month of 42 transactions is used so every page still works.
"""

import random
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FinPilot — AI financial investigation",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Small compatibility helpers (work on older and newer Streamlit versions)
# ---------------------------------------------------------------------------

def html(markup: str) -> None:
    """Render raw HTML. st.html avoids Markdown/LaTeX parsing of '$' signs."""
    markup = " ".join(line.strip() for line in markup.strip().splitlines())
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup.replace("$", "&#36;"), unsafe_allow_html=True)


def keyed_container(key: str):
    try:
        return st.container(key=key)
    except TypeError:
        return st.container()


def columns(spec, **kw):
    try:
        return st.columns(spec, vertical_alignment="center", **kw)
    except TypeError:
        return st.columns(spec, **kw)


def button(label, key=None, primary=False, **kw):
    kind = "primary" if primary else "secondary"
    try:
        return st.button(label, key=key, type=kind, width="stretch", **kw)
    except TypeError:
        return st.button(label, key=key, type=kind, use_container_width=True, **kw)


def download_button(label, data, file_name, mime, key):
    try:
        return st.download_button(label, data=data, file_name=file_name,
                                  mime=mime, key=key, width="stretch")
    except TypeError:
        return st.download_button(label, data=data, file_name=file_name,
                                  mime=mime, key=key, use_container_width=True)


def dataframe(df, **kw):
    try:
        st.dataframe(df, width="stretch", **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kw)


def money(x: float) -> str:
    return f"${x:,.2f}"


# ---------------------------------------------------------------------------
# Investigation knowledge base (evidence for each flagged transaction)
# ---------------------------------------------------------------------------

FINDINGS = {
    "TXN-1052": dict(
        vendor="Cloud Infrastructure Co.", category="Hosting", amount=18420.00,
        date="2026-08-14", status="Exception", finding="Spending anomaly",
        summary="This payment is 4.4 times the vendor's six-month average of $4,210.",
        recommendation="Confirm the usage spike with engineering and check the invoice line items before close.",
        checks=[
            ("Historical spend", "Flagged", "4.4× the six-month average of $4,210"),
            ("Invoice match", "Passed", "INV-88213 matches $18,420.00"),
            ("Duplicate scan", "Passed", "No similar payment in the last 60 days"),
            ("Vendor record", "Passed", "Approved vendor since March 2023"),
        ],
    ),
    "TXN-1053": dict(
        vendor="AWS Services", category="Hosting", amount=7850.00,
        date="2026-08-18", status="Exception", finding="Possible duplicate payment",
        summary="Same vendor, same amount and same invoice number as TXN-1054, paid one day apart.",
        recommendation="Check with accounts payable whether INV-55120 was paid twice and request a refund if so.",
        checks=[
            ("Historical spend", "Passed", "Within the normal monthly range"),
            ("Invoice match", "Passed", "INV-55120 matches $7,850.00"),
            ("Duplicate scan", "Flagged", "TXN-1054 uses the same invoice and amount"),
            ("Vendor record", "Passed", "Approved vendor since January 2022"),
        ],
    ),
    "TXN-1054": dict(
        vendor="AWS Services", category="Hosting", amount=7850.00,
        date="2026-08-19", status="Exception", finding="Possible duplicate payment",
        summary="Paid one day after TXN-1053 against the same invoice, INV-55120.",
        recommendation="Review both payments together; only one should stand.",
        checks=[
            ("Historical spend", "Passed", "Within the normal monthly range"),
            ("Invoice match", "Flagged", "INV-55120 was already paid by TXN-1053"),
            ("Duplicate scan", "Flagged", "Matches TXN-1053 on vendor, amount and invoice"),
            ("Vendor record", "Passed", "Approved vendor since January 2022"),
        ],
    ),
    "TXN-1057": dict(
        vendor="Office Supply Hub", category="Office", amount=2315.00,
        date="2026-08-21", status="Exception", finding="Invoice mismatch",
        summary="The payment is $180 more than the invoice total of $2,135. The digits look transposed.",
        recommendation="Ask the vendor for a credit note of $180 or correct the payment record.",
        checks=[
            ("Historical spend", "Passed", "Within the normal monthly range"),
            ("Invoice match", "Flagged", "INV-30418 totals $2,135.00, paid $2,315.00"),
            ("Duplicate scan", "Passed", "No similar payment in the last 60 days"),
            ("Vendor record", "Passed", "Approved vendor since June 2024"),
        ],
    ),
    "TXN-1058": dict(
        vendor="Freight Partners LLC", category="Shipping", amount=3600.00,
        date="2026-08-24", status="Exception", finding="Missing invoice",
        summary="No invoice or receipt is attached to this payment.",
        recommendation="Request the invoice from the vendor before closing the period.",
        checks=[
            ("Historical spend", "Passed", "Within the normal monthly range"),
            ("Invoice match", "Flagged", "No supporting document found"),
            ("Duplicate scan", "Passed", "No similar payment in the last 60 days"),
            ("Vendor record", "Passed", "Approved vendor since August 2023"),
        ],
    ),
    "TXN-1059": dict(
        vendor="New Vendor Ltd.", category="Consulting", amount=4900.00,
        date="2026-08-27", status="Needs review", finding="New vendor",
        summary="First payment to this vendor, so there is no spending history to compare against.",
        recommendation="Confirm the vendor was approved through onboarding and that the engagement letter is on file.",
        checks=[
            ("Historical spend", "Unclear", "No history for this vendor"),
            ("Invoice match", "Passed", "INV-0001 matches $4,900.00"),
            ("Duplicate scan", "Passed", "No similar payment found"),
            ("Vendor record", "Unclear", "Vendor added on 25 August 2026"),
        ],
    ),
}

STEPS = [
    ("Read the transaction", "Amount, vendor, date and payment reference."),
    ("Compare with history", "Six months of spending for the same vendor."),
    ("Match the invoice", "Checks the supporting document and its total."),
    ("Scan for duplicates", "Same vendor, amount or invoice within 60 days."),
    ("Explain the finding", "Plain-language summary with the evidence attached."),
]

DECISIONS = {
    "Approve": "Approved",
    "Request documents": "Documents requested",
    "Escalate": "Escalated",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _find_col(df, names):
    lookup = {c.lower().strip(): c for c in df.columns}
    for n in names:
        if n in lookup:
            return lookup[n]
    return None


def demo_transactions() -> pd.DataFrame:
    rng = random.Random(8)
    normal_vendors = [
        ("Adobe Systems", "Software", 1280), ("Slack Technologies", "Software", 940),
        ("WeWork", "Facilities", 6200), ("Google Workspace", "Software", 1450),
        ("Uber for Business", "Travel", 610), ("Delta Air Lines", "Travel", 1890),
        ("Staples", "Office", 420), ("Comcast Business", "Utilities", 380),
        ("Gusto", "Payroll services", 2150), ("Zoom Video", "Software", 720),
        ("FedEx", "Shipping", 530), ("Notion Labs", "Software", 360),
    ]
    rows = []
    for i in range(42):
        txn = f"TXN-{1040 + i}"
        if txn in FINDINGS:
            f = FINDINGS[txn]
            rows.append([txn, f["date"], f["vendor"], f["category"], f["amount"]])
        else:
            v, cat, base = rng.choice(normal_vendors)
            amt = round(base * rng.uniform(0.85, 1.15), 2)
            d = date(2026, 8, 1) + timedelta(days=rng.randint(0, 30))
            rows.append([txn, d.isoformat(), v, cat, amt])
    return pd.DataFrame(rows, columns=["Transaction", "Date", "Vendor", "Category", "Amount"])


@st.cache_data
def load_data() -> tuple[pd.DataFrame, str]:
    """Returns (transactions, source_label)."""
    tx_path, gt_path = Path("data") / "transactions.csv", Path("data") / "ground_truth.csv"
    df = None
    if tx_path.exists():
        try:
            raw = pd.read_csv(tx_path)
            id_c = _find_col(raw, ["transaction_id", "txn_id", "id", "transaction"])
            amt_c = _find_col(raw, ["amount", "value", "total"])
            if id_c and amt_c:
                df = pd.DataFrame({
                    "Transaction": raw[id_c].astype(str),
                    "Date": raw[_find_col(raw, ["date", "transaction_date", "posted_date"])].astype(str)
                    if _find_col(raw, ["date", "transaction_date", "posted_date"]) else "",
                    "Vendor": raw[_find_col(raw, ["vendor", "merchant", "payee", "supplier"])].astype(str)
                    if _find_col(raw, ["vendor", "merchant", "payee", "supplier"]) else "Unknown",
                    "Category": raw[_find_col(raw, ["category", "account", "gl_account"])].astype(str)
                    if _find_col(raw, ["category", "account", "gl_account"]) else "",
                    "Amount": pd.to_numeric(raw[amt_c], errors="coerce").fillna(0.0),
                })
        except Exception:
            df = None

    source = "data/transactions.csv"
    if df is None or df.empty:
        df, source = demo_transactions(), "built-in demo data"

    # Status + finding: ground_truth.csv first, then the built-in evidence base.
    df["Status"], df["Finding"] = "Clear", ""
    labels = {}
    if gt_path.exists():
        try:
            gt = pd.read_csv(gt_path)
            gid = _find_col(gt, ["transaction_id", "txn_id", "id", "transaction"])
            glab = _find_col(gt, ["label", "anomaly_type", "exception_type", "finding", "type", "status"])
            if gid and glab:
                for t, lab in zip(gt[gid].astype(str), gt[glab].astype(str)):
                    if lab.strip().lower() not in {"", "normal", "none", "clear", "0", "false", "nan", "ok"}:
                        labels[t] = lab.replace("_", " ").strip().capitalize()
        except Exception:
            pass

    for i, t in df["Transaction"].items():
        if t in FINDINGS:
            df.at[i, "Status"] = FINDINGS[t]["status"]
            df.at[i, "Finding"] = FINDINGS[t]["finding"]
        elif t in labels:
            review = "review" in labels[t].lower() or "new vendor" in labels[t].lower()
            df.at[i, "Status"] = "Needs review" if review else "Exception"
            df.at[i, "Finding"] = labels[t]
    return df, source


def evidence_for(txn: str, row: pd.Series) -> dict:
    """Evidence for a flagged transaction. Falls back to a generic record."""
    if txn in FINDINGS:
        return FINDINGS[txn]
    return dict(
        vendor=row["Vendor"], category=row["Category"], amount=float(row["Amount"]),
        date=row["Date"], status=row["Status"], finding=row["Finding"] or "Flagged",
        summary=f"Flagged in ground truth as: {row['Finding'] or 'exception'}.",
        recommendation="Review the transaction and its supporting documents before close.",
        checks=[("Ground truth label", "Flagged", row["Finding"] or "Exception")],
    )


transactions, data_source = load_data()
flagged = transactions[transactions["Status"] != "Clear"].reset_index(drop=True)
flagged_ids = flagged["Transaction"].tolist()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

st.session_state.setdefault("page", "Overview")
st.session_state.setdefault("investigated", {})   # txn -> True
st.session_state.setdefault("live_results", {})   # txn -> real engine result
st.session_state.setdefault("decisions", {})      # txn -> {"decision", "note"}
if flagged_ids:
    st.session_state.setdefault("inv_select", flagged_ids[0])


def go(page: str, focus: str | None = None):
    st.session_state.page = page
    if focus:
        st.session_state.inv_select = focus


def first_open_item():
    for t in flagged_ids:
        if t not in st.session_state.decisions:
            return t
    return flagged_ids[0] if flagged_ids else None


def decide(txn: str, choice: str):
    st.session_state.decisions[txn] = {
        "decision": DECISIONS[choice],
        "note": st.session_state.get(f"note_{txn}", "").strip(),
    }


def undo_decision(txn: str):
    st.session_state.decisions.pop(txn, None)


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');

:root {
  --font: "Instrument Sans", "Segoe UI", system-ui, -apple-system, sans-serif;
  --canvas: #F5F4F8;
  --surface: #FFFFFF;
  --ink: #17141F;
  --body: #3B3646;
  --muted: #5F586B;
  --line: #E3DFEA;
  --brand: #5536C9;
  --brand-deep: #241B47;
  --brand-soft: #EEEAFB;
  --exc: #A63A17;   --exc-bg: #FCEDE6;
  --rev: #7F4C00;   --rev-bg: #FBF0D9;
  --ok:  #22704A;   --ok-bg:  #E5F3EB;
}

/* ---- base ---- */
.stApp { background: var(--canvas); color: var(--body); }
.stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp [data-baseweb="select"] div, [data-baseweb="popover"] li,
.stApp [data-testid="stMarkdownContainer"] { font-family: var(--font); }
.stApp p, .stApp label { font-size: 15px; }

.block-container { max-width: 1380px; width: 94%; margin: 0 auto; padding: 2.1rem 0 4rem; }
header[data-testid="stHeader"] { background: transparent; height: 2.4rem; pointer-events: none; }
header[data-testid="stHeader"] [data-testid="stToolbar"] { pointer-events: auto; }
[data-testid="stDecoration"], #MainMenu, footer { display: none; }

/* keyboard focus stays visible everywhere */
.stApp button:focus-visible, .stApp input:focus-visible, .stApp textarea:focus-visible {
  outline: 2px solid var(--brand); outline-offset: 2px;
}

/* ---- buttons ---- */
.stApp button[kind="primary"], .stApp [data-testid="stBaseButton-primary"] {
  background: var(--brand); border: 1px solid var(--brand); color: #fff;
  min-height: 44px; border-radius: 10px; font-weight: 600; font-size: 15px;
}
.stApp button[kind="primary"]:hover, .stApp [data-testid="stBaseButton-primary"]:hover {
  background: #4429AE; border-color: #4429AE; color: #fff;
}
.stApp button[kind="secondary"], .stApp [data-testid="stBaseButton-secondary"],
.stApp [data-testid="stDownloadButton"] button {
  background: var(--surface); border: 1px solid #CFC8DC; color: var(--ink);
  min-height: 44px; border-radius: 10px; font-weight: 600; font-size: 15px;
}
.stApp button[kind="secondary"]:hover, .stApp [data-testid="stBaseButton-secondary"]:hover,
.stApp [data-testid="stDownloadButton"] button:hover {
  border-color: var(--brand); color: var(--brand); background: var(--surface);
}
.stApp button p { font-size: 15px; font-weight: 600; }

/* ---- top bar navigation ---- */
.st-key-topbar { padding-bottom: 14px; border-bottom: 1px solid var(--line); margin-bottom: 8px; }
.st-key-topbar button {
  min-height: 38px !important; border: none !important; box-shadow: none !important;
  background: transparent !important; color: var(--muted) !important; border-radius: 8px !important;
}
.st-key-topbar button:hover { color: var(--ink) !important; background: #ECE9F2 !important; }
.st-key-topbar button[kind="primary"], .st-key-topbar [data-testid="stBaseButton-primary"] {
  background: var(--brand-soft) !important; color: var(--brand) !important;
}
.st-key-topbar button p { font-size: 15px; }

.brand { display: flex; align-items: center; gap: 10px; color: var(--ink);
  font-size: 21px; font-weight: 700; letter-spacing: -0.01em; }
.brand-mark { width: 32px; height: 32px; border-radius: 9px; background: var(--brand-deep);
  display: grid; place-items: center; }
.brand-mark span { width: 12px; height: 12px; background: #B9A8FF; transform: rotate(45deg); border-radius: 2px; }
.who { display: flex; justify-content: flex-end; align-items: center; gap: 12px;
  color: var(--muted); font-size: 14px; }
.who strong { color: var(--ink); font-weight: 600; }
.avatar { width: 34px; height: 34px; border-radius: 50%; background: var(--brand-soft);
  color: var(--brand); display: grid; place-items: center; font-size: 13px; font-weight: 700; }

/* ---- type ---- */
.page-title { color: var(--ink); font-size: 30px; font-weight: 700; letter-spacing: -0.02em;
  margin: 18px 0 4px; line-height: 1.2; }
.page-sub { color: var(--muted); font-size: 16px; line-height: 1.6; max-width: 68ch; margin: 0 0 6px; }
.h2 { color: var(--ink); font-size: 19px; font-weight: 650; margin: 26px 0 2px; letter-spacing: -0.01em; }
.h2-sub { color: var(--muted); font-size: 14.5px; margin: 0 0 4px; }

/* ---- close status (hero) ---- */
.close {
  display: grid; grid-template-columns: 1.25fr 1fr; gap: 0; margin-top: 18px;
  background: var(--surface); border: 1px solid var(--line); border-radius: 18px; overflow: hidden;
}
.close-main { padding: 40px 44px; }
.close-period { color: var(--brand); font-size: 15px; font-weight: 600; }
.close-main h1 { font-family: var(--font); color: var(--ink); font-size: 44px; line-height: 1.08;
  font-weight: 700; letter-spacing: -0.03em; margin: 10px 0 0; padding: 0; }
.close-main p { color: var(--body); font-size: 17px; line-height: 1.65; margin: 18px 0 0; max-width: 54ch; }
.close-side { padding: 40px 40px; background: #FAF9FC; border-left: 1px solid var(--line); }
.tally { display: flex; align-items: baseline; gap: 10px; color: var(--ink); }
.tally b { font-size: 46px; font-weight: 700; letter-spacing: -0.03em; font-variant-numeric: tabular-nums; }
.tally span { color: var(--muted); font-size: 16px; }
.bar { display: flex; height: 12px; border-radius: 6px; overflow: hidden; margin: 18px 0 18px; gap: 2px; }
.bar i { display: block; height: 100%; }
.legend { display: grid; gap: 10px; }
.legend div { display: flex; align-items: center; gap: 10px; font-size: 15px; color: var(--body); }
.legend div em { font-style: normal; margin-left: auto; color: var(--ink); font-weight: 600;
  font-variant-numeric: tabular-nums; }
.sw { width: 12px; height: 12px; border-radius: 3px; flex: 0 0 12px; }
.decided { margin-top: 22px; padding-top: 18px; border-top: 1px solid var(--line);
  font-size: 15px; color: var(--body); }
.decided b { color: var(--ink); }

/* ---- generic card ---- */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; }
.card-pad { padding: 24px 26px; }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 16px;
  padding: 18px 22px; border-bottom: 1px solid var(--line); }
.card-head h3 { margin: 0; padding: 0; color: var(--ink); font-size: 17px; font-weight: 650; font-family: var(--font); }
.card-head span { color: var(--muted); font-size: 14px; }

/* ---- attention list ---- */
.item { display: grid; grid-template-columns: 150px 1fr auto; gap: 18px; align-items: center;
  padding: 16px 22px; border-bottom: 1px solid #EEEBF3; }
.item:last-child { border-bottom: none; }
.item .id { color: var(--ink); font-weight: 600; font-size: 15px; font-variant-numeric: tabular-nums; }
.item .vend { color: var(--muted); font-size: 13.5px; margin-top: 3px; line-height: 1.35; }
.item .what { color: var(--ink); font-size: 15.5px; font-weight: 600; }
.item .why { color: var(--muted); font-size: 14.5px; margin-top: 3px; line-height: 1.5; }
.item .amt { color: var(--ink); font-weight: 600; font-size: 15px; text-align: right;
  font-variant-numeric: tabular-nums; }
.item .amt div { margin-top: 6px; }

/* ---- status pills ---- */
.pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 13px;
  font-weight: 600; white-space: nowrap; }
.pill.exc { color: var(--exc); background: var(--exc-bg); }
.pill.rev { color: var(--rev); background: var(--rev-bg); }
.pill.ok  { color: var(--ok);  background: var(--ok-bg); }
.pill.neu { color: var(--brand); background: var(--brand-soft); }

/* ---- how it checks (a real sequence, so it is numbered) ---- */
.method { background: var(--brand-deep); border-radius: 14px; padding: 26px 26px 10px; color: #fff; }
.method h3 { margin: 0; padding: 0; font-family: var(--font); font-size: 19px; font-weight: 650; color: #fff; }
.method > p { color: #CFC8E6; font-size: 15px; line-height: 1.6; margin: 8px 0 14px; }
.step { display: grid; grid-template-columns: 30px 1fr; gap: 12px; padding: 12px 0;
  border-top: 1px solid rgba(255,255,255,.12); }
.step .n { width: 28px; height: 28px; border-radius: 50%; background: rgba(185,168,255,.18);
  color: #D9CFFF; display: grid; place-items: center; font-size: 13px; font-weight: 700; }
.step .t { color: #fff; font-size: 15px; font-weight: 600; }
.step .d { color: #CFC8E6; font-size: 14px; margin-top: 2px; line-height: 1.5; }

/* ---- principle strip ---- */
.principle { margin-top: 30px; padding: 22px 26px; border-radius: 14px; background: var(--brand-soft);
  display: flex; gap: 22px; align-items: baseline; flex-wrap: wrap; }
.principle b { color: var(--brand-deep); font-size: 19px; font-weight: 700; white-space: nowrap; }
.principle span { color: var(--body); font-size: 15.5px; line-height: 1.6; flex: 1 1 380px; }

/* ---- investigation result ---- */
.facts { display: grid; grid-template-columns: repeat(4, 1fr); border-bottom: 1px solid var(--line); }
.facts div { padding: 16px 22px; border-right: 1px solid var(--line); }
.facts div:last-child { border-right: none; }
.facts small { display: block; color: var(--muted); font-size: 13.5px; margin-bottom: 4px; }
.facts b { color: var(--ink); font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums; }
.finding { padding: 22px; }
.finding h4 { margin: 0; padding: 0; font-family: var(--font); color: var(--ink); font-size: 22px; font-weight: 700; letter-spacing: -0.01em; }
.finding p { color: var(--body); font-size: 16px; line-height: 1.65; margin: 8px 0 0; max-width: 70ch; }
.checks { width: 100%; border-collapse: collapse; }
.checks td { padding: 13px 22px; border-top: 1px solid #EEEBF3; font-size: 15px; color: var(--body); vertical-align: top; }
.checks td:first-child { color: var(--ink); font-weight: 600; width: 34%; }
.checks td:nth-child(2) { width: 120px; }
.next { margin: 0 22px 22px; padding: 16px 18px; border-radius: 10px; background: #FAF9FC; border: 1px solid var(--line); }
.next small { color: var(--muted); font-size: 13.5px; font-weight: 600; }
.next p { color: var(--ink); font-size: 16px; line-height: 1.6; margin: 4px 0 0; }

/* ---- tables ---- */
.scroll { overflow-x: auto; }
.tbl { width: 100%; border-collapse: collapse; min-width: 640px; }
.tbl th { text-align: left; color: var(--muted); font-size: 13.5px; font-weight: 600;
  padding: 12px 22px; background: #FAF9FC; border-bottom: 1px solid var(--line); }
.tbl td { padding: 13px 22px; border-bottom: 1px solid #EEEBF3; font-size: 15px; color: var(--body); }
.tbl tr:last-child td { border-bottom: none; }
.tbl td.r, .tbl th.r { text-align: right; font-variant-numeric: tabular-nums; }
.tbl td.id { color: var(--ink); font-weight: 600; }

/* ---- readiness banner ---- */
.ready { display: flex; gap: 14px; align-items: center; padding: 18px 22px; border-radius: 14px; margin-top: 18px; }
.ready.no  { background: var(--rev-bg); color: var(--rev); }
.ready.yes { background: var(--ok-bg); color: var(--ok); }
.ready b { font-size: 17px; }
.ready span { font-size: 15px; color: var(--body); }

/* ---- widgets ---- */
/* newer Streamlit (react-aria) + older Streamlit (baseweb) field wrappers */
.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stTextAreaRootElement"],
.stApp [data-testid="stSelectbox"] div[role="group"], .stApp [data-testid="stMultiSelect"] div[role="group"],
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"] {
  background: var(--surface) !important; border: 1px solid #CFC8DC !important; border-radius: 10px !important;
}
.stApp [data-baseweb="input"] > div, .stApp [data-baseweb="textarea"] > div, .stApp input, .stApp textarea {
  background: transparent !important; border: none !important;
}
.stApp [data-testid="stTextInputRootElement"]:focus-within, .stApp [data-testid="stTextAreaRootElement"]:focus-within,
.stApp [data-testid="stSelectbox"] div[role="group"]:focus-within, .stApp [data-testid="stMultiSelect"] div[role="group"]:focus-within,
.stApp [data-baseweb="select"] > div:focus-within, .stApp [data-baseweb="input"]:focus-within,
.stApp [data-baseweb="textarea"]:focus-within { border-color: var(--brand) !important; }
.stApp [data-baseweb="select"] div, .stApp input, .stApp textarea { color: var(--ink) !important; font-size: 15px !important; }
.stApp input::placeholder, .stApp textarea::placeholder { color: #8A8396 !important; }
.stApp [data-testid="stWidgetLabel"] p { color: var(--ink); font-weight: 600; font-size: 14.5px; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }

.foot { margin-top: 44px; padding-top: 18px; border-top: 1px solid var(--line);
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; color: var(--muted); font-size: 14px; }

/* ---- small screens ---- */
@media (max-width: 860px) {
  .block-container { padding: 2.4rem 1rem 3rem; }
  .close { grid-template-columns: 1fr; }
  .close-side { border-left: none; border-top: 1px solid var(--line); }
  .close-main, .close-side { padding: 28px 24px; }
  .close-main h1 { font-size: 34px; }
  .item { grid-template-columns: 1fr auto; }
  .item > div:first-child { grid-column: 1 / -1; display: flex; gap: 10px; align-items: baseline; }
  .item .vend { margin-top: 0; }
  .st-key-topbar [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 4px !important; }
  .st-key-topbar [data-testid="stColumn"], .st-key-topbar [data-testid="column"] {
    min-width: 0 !important; width: auto !important; flex: 1 1 40% !important; order: 2; }
  .st-key-topbar [data-testid="stColumn"]:first-child, .st-key-topbar [data-testid="column"]:first-child,
  .st-key-topbar [data-testid="stColumn"]:last-child, .st-key-topbar [data-testid="column"]:last-child {
    flex: 1 1 45% !important; order: 1; }
  .st-key-topbar button p { font-size: 13.5px !important; }
  .st-key-topbar button { padding: 0 4px !important; }
  .facts { grid-template-columns: 1fr 1fr; }
  .facts div:nth-child(2) { border-right: none; }
  .facts div:nth-child(-n+2) { border-bottom: 1px solid var(--line); }
  .who span.label { display: none; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
""")

# ---------------------------------------------------------------------------
# Shared pieces
# ---------------------------------------------------------------------------

PILL = {"Exception": "exc", "Needs review": "rev", "Clear": "ok"}
CHECK_PILL = {"Flagged": "exc", "Unclear": "rev", "Passed": "ok"}
DECISION_PILL = {"Approved": "ok", "Documents requested": "rev", "Escalated": "exc"}


def pill(text, cls):
    return f'<span class="pill {cls}">{text}</span>'


def status_pill_for(txn, status):
    d = st.session_state.decisions.get(txn)
    if d:
        return pill(d["decision"], DECISION_PILL[d["decision"]])
    return pill(status, PILL.get(status, "neu"))


counts = transactions["Status"].value_counts()
n_total = len(transactions)
n_clear = int(counts.get("Clear", 0))
n_exc = int(counts.get("Exception", 0))
n_rev = int(counts.get("Needs review", 0))
n_flagged = n_exc + n_rev
n_decided = sum(1 for t in flagged_ids if t in st.session_state.decisions)
n_open = n_flagged - n_decided
n_types = flagged["Finding"].nunique() if n_flagged else 0
PERIOD = "August 2026"


def topbar():
    with keyed_container("topbar"):
        c = columns([2.3, 1, 1.25, 1.2, 1, 2.3])
        with c[0]:
            html('<div class="brand"><div class="brand-mark"><span></span></div>FinPilot</div>')
        for col, name in zip(c[1:5], ["Overview", "Investigations", "Transactions", "Reports"]):
            with col:
                button(name, key=f"nav_{name}", primary=st.session_state.page == name,
                       on_click=go, args=(name,))
        with c[5]:
            html(f'<div class="who"><span class="label">{PERIOD} close</span>'
                 f'<div class="avatar" title="Signed in as JB">JB</div></div>')


def footer():
    html(f"""
    <div class="foot">
      <div>FinPilot prototype. Data source: {data_source}.</div>
      <div>FinPilot never moves money or approves payments.</div>
    </div>""")



# ---------------------------------------------------------------------------
# Live FinPilot engine integration
# ---------------------------------------------------------------------------

def run_live_investigation(txn: str) -> dict:
    """
    Run FinPilot's real investigation graph.
    Falls back to the deterministic tool if the graph is unavailable.
    """
    try:
        from agents.graph import finpilot_graph

        result = finpilot_graph.invoke(
            {
                "user_request": f"Review {txn} before month-end close",
                "transaction_id": txn,
                "evidence": [],
                "tools_called": [],
                "investigation_steps": [],
            }
        )

        finding = result.get("finding") or {}

        return {
            "available": True,
            "source": "LangGraph investigation",
            "status": result.get("status", "unknown"),
            "severity": result.get("severity", finding.get("severity", "NORMAL")),
            "vendor": result.get("vendor", ""),
            "amount": result.get("transaction_amount", 0),
            "evidence": result.get("evidence", []),
            "finding": finding,
            "error": "",
        }

    except Exception as graph_exc:
        try:
            from agents.tools import investigate_transaction

            result = investigate_transaction(txn)

            return {
                "available": True,
                "source": "Deterministic investigation tool",
                "status": result.get("status", "unknown"),
                "severity": result.get("severity", "NORMAL"),
                "vendor": result.get("vendor", ""),
                "amount": result.get("amount", 0),
                "evidence": result.get("evidence", []),
                "finding": {},
                "error": "",
            }

        except Exception as tool_exc:
            return {
                "available": False,
                "source": "Product evidence layer",
                "status": "engine_error",
                "severity": "UNKNOWN",
                "vendor": "",
                "amount": 0,
                "evidence": [],
                "finding": {},
                "error": (
                    f"Graph error: {graph_exc}; "
                    f"Tool error: {tool_exc}"
                ),
            }


def live_status_label(status: str) -> tuple[str, str]:
    mapping = {
        "exception_detected": ("Exception", "exc"),
        "review_required": ("Needs review", "rev"),
        "no_exception": ("Clear", "ok"),
        "exception": ("Exception", "exc"),
        "normal": ("Clear", "ok"),
    }
    return mapping.get(status, ("Engine result", "neu"))

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_overview():
    w = lambda n: f"{(n / n_total * 100) if n_total else 0:.2f}%"
    headline = (f"{n_open} transaction{'s' if n_open != 1 else ''} need{'s' if n_open == 1 else ''} "
                f"a decision before you close.") if n_open else "Every flagged transaction has a decision."
    html(f"""
    <div class="close">
      <div class="close-main">
        <div class="close-period">{PERIOD} month-end</div>
        <h1>{headline}</h1>
        <p>FinPilot checked every transaction against spending history, invoices and
        earlier payments. Each flag comes with the evidence, so you can decide quickly
        and close with confidence.</p>
      </div>
      <div class="close-side">
        <div class="tally"><b>{n_total}</b><span>transactions checked</span></div>
        <div class="bar" role="img" aria-label="{n_clear} clear, {n_exc} exceptions, {n_rev} need review">
          <i style="width:{w(n_clear)};background:#3E9A6A"></i>
          <i style="width:{w(n_exc)};background:#D2643A"></i>
          <i style="width:{w(n_rev)};background:#D9A21B"></i>
        </div>
        <div class="legend">
          <div><span class="sw" style="background:#3E9A6A"></span>Clear<em>{n_clear}</em></div>
          <div><span class="sw" style="background:#D2643A"></span>Exceptions<em>{n_exc}</em></div>
          <div><span class="sw" style="background:#D9A21B"></span>Needs review<em>{n_rev}</em></div>
        </div>
        <div class="decided"><b>{n_decided} of {n_flagged}</b> flagged transactions decided</div>
      </div>
    </div>""")

    st.write("")
    a, b, c, _ = st.columns([1.2, 1.2, 1.2, 1.4])
    with a:
        button("Start investigation", key="qa_start", primary=True,
               on_click=go, args=("Investigations", first_open_item()))
    with b:
        button("View all transactions", key="qa_tx", on_click=go, args=("Transactions",))
    with c:
        button("Open month-end report", key="qa_rep", on_click=go, args=("Reports",))

    left, right = st.columns([1.6, 1], gap="large")
    with left:
        rows = ""
        for _, r in flagged.iterrows():
            ev = evidence_for(r["Transaction"], r)
            rows += f"""
            <div class="item">
              <div><div class="id">{r['Transaction']}</div><div class="vend">{r['Vendor']}</div></div>
              <div><div class="what">{ev['finding']}</div>
                   <div class="why">{ev['summary']}</div></div>
              <div class="amt">{money(float(r['Amount']))}
                   <div>{status_pill_for(r['Transaction'], r['Status'])}</div></div>
            </div>"""
        if not rows:
            rows = '<div class="item"><div class="why">Nothing flagged this month.</div></div>'
        html(f"""
        <div class="card" style="margin-top:22px">
          <div class="card-head"><h3>What needs your attention</h3>
            <span>{n_flagged} flagged, {n_types} kinds of issue</span></div>
          {rows}
        </div>""")
    with right:
        steps = "".join(
            f'<div class="step"><div class="n">{i}</div><div><div class="t">{t}</div>'
            f'<div class="d">{d}</div></div></div>'
            for i, (t, d) in enumerate(STEPS, 1))
        html(f"""
        <div class="method" style="margin-top:22px">
          <h3>Evidence first, then the explanation</h3>
          <p>Each transaction runs through the same five checks. The AI only writes the
          summary after the evidence is in.</p>
          {steps}
        </div>""")

    html("""
    <div class="principle">
      <b>AI investigates. You decide.</b>
      <span>FinPilot never moves money, approves payments, edits accounting records or
      closes a period. It gathers evidence so your team can decide faster.</span>
    </div>""")


def page_investigations():
    html('<div class="page-title">Investigations</div>'
         '<p class="page-sub">Pick a flagged transaction, run the checks, then record your decision.</p>')

    if not flagged_ids:
        st.info("Nothing is flagged this month. Every transaction passed its checks.")
        return

    label = {
        r["Transaction"]: (
            f"{r['Transaction']}   {r['Vendor']}   {money(float(r['Amount']))}"
        )
        for _, r in flagged.iterrows()
    }

    s, b = columns([3, 1])

    with s:
        txn = st.selectbox(
            "Flagged transaction",
            flagged_ids,
            key="inv_select",
            format_func=lambda t: label[t],
        )

    with b:
        st.write("")
        run = button("Run investigation", key="run_inv", primary=True)

    if run:
        with st.status(f"Investigating {txn}", expanded=True) as status:
            for step_name, _ in STEPS[:4]:
                st.write(step_name)

            live_result = run_live_investigation(txn)
            st.session_state.live_results[txn] = live_result

            if live_result["available"]:
                st.write("Synthesizing evidence")
                status.update(
                    label=f"{txn} investigated",
                    state="complete",
                    expanded=False,
                )
            else:
                status.update(
                    label=f"{txn} investigated with product evidence",
                    state="complete",
                    expanded=False,
                )

        st.session_state.investigated[txn] = True

    if not st.session_state.investigated.get(txn):
        html(f"""
        <div class="card card-pad" style="margin-top:14px">
          <div class="what" style="color:var(--ink);font-size:17px;font-weight:600">
            {txn} has not been investigated yet
          </div>
          <p class="page-sub" style="margin-top:6px">
            Select <b>Run investigation</b> to check its history,
            invoice and possible duplicates.
          </p>
        </div>""")
        return

    row = flagged[flagged["Transaction"] == txn].iloc[0]
    ev = evidence_for(txn, row)

    checks = "".join(
        f"<tr><td>{name}</td>"
        f"<td>{pill(res, CHECK_PILL.get(res, 'neu'))}</td>"
        f"<td>{detail}</td></tr>"
        for name, res, detail in ev["checks"]
    )

    html(f"""
    <div class="card" style="margin-top:14px">
      <div class="card-head">
        <h3>{txn}</h3>
        {status_pill_for(txn, row['Status'])}
      </div>

      <div class="facts">
        <div><small>Vendor</small><b>{row['Vendor']}</b></div>
        <div><small>Amount</small><b>{money(float(row['Amount']))}</b></div>
        <div><small>Date</small><b>{row['Date']}</b></div>
        <div><small>Category</small><b>{row['Category'] or '—'}</b></div>
      </div>

      <div class="finding">
        <h4>{ev['finding']}</h4>
        <p>{ev['summary']}</p>
      </div>

      <div class="scroll">
        <table class="checks">{checks}</table>
      </div>

      <div class="next">
        <small>Recommended next step</small>
        <p>{ev['recommendation']}</p>
      </div>
    </div>""")

    live = st.session_state.live_results.get(txn)

    if live:
        live_label, live_cls = live_status_label(live.get("status", ""))

        if live.get("available"):
            engine_finding = live.get("finding") or {}
            engine_summary = engine_finding.get("summary", "")
            engine_recommendation = engine_finding.get("recommendation", "")

            evidence_rows = ""
            for item in live.get("evidence", []):
                if isinstance(item, dict):
                    item_type = item.get("type", "Evidence")
                    description = item.get("description", "")
                    value = item.get("value", "")
                    evidence_rows += (
                        f"<tr><td>{item_type}</td>"
                        f"<td>{description}</td>"
                        f"<td>{value}</td></tr>"
                    )
                else:
                    evidence_rows += (
                        f"<tr><td>Evidence</td>"
                        f"<td colspan='2'>{item}</td></tr>"
                    )

            if not evidence_rows:
                evidence_rows = (
                    "<tr><td>Evidence</td>"
                    "<td colspan='2'>No structured evidence returned.</td></tr>"
                )

            extra_text = ""
            if engine_summary:
                extra_text += f"<p>{engine_summary}</p>"
            if engine_recommendation:
                extra_text += (
                    f"<div class='next' style='margin:14px 0 0'>"
                    f"<small>Engine recommendation</small>"
                    f"<p>{engine_recommendation}</p>"
                    f"</div>"
                )

            html(f"""
            <div class="card" style="margin-top:18px">
              <div class="card-head">
                <h3>Live FinPilot engine</h3>
                <span class="pill {live_cls}">{live_label}</span>
              </div>

              <div class="finding">
                <div class="h2-sub">
                  Source: <b>{live.get("source", "FinPilot engine")}</b>
                </div>
                {extra_text}
              </div>

              <div class="scroll">
                <table class="checks">
                  <thead>
                    <tr>
                      <td style="font-weight:600">Type</td>
                      <td style="font-weight:600">Description</td>
                      <td style="font-weight:600">Value</td>
                    </tr>
                  </thead>
                  <tbody>{evidence_rows}</tbody>
                </table>
              </div>
            </div>""")
        else:
            html(f"""
            <div class="ready no" style="margin-top:18px">
              <b>Engine fallback</b>
              <span>
                The live engine could not be loaded in this runtime.
                The product evidence layer is shown instead.
                Detail: {live.get("error", "")}
              </span>
            </div>""")

    html(
        '<div class="h2">Your decision</div>'
        '<p class="h2-sub">'
        'FinPilot records the decision for the month-end report. '
        'It does not act on it.'
        '</p>'
    )

    existing = st.session_state.decisions.get(txn)

    if existing:
        note = f" Note: {existing['note']}" if existing["note"] else ""

        html(
            f'<div class="card card-pad">'
            f'{pill(existing["decision"], DECISION_PILL[existing["decision"]])}'
            f'<span style="margin-left:10px;color:var(--body);font-size:15px">'
            f'Recorded for {txn}.{note}</span></div>'
        )

        x, y, _ = st.columns([1, 1, 2])

        with x:
            button(
                "Change decision",
                key=f"undo_{txn}",
                on_click=undo_decision,
                args=(txn,),
            )

        with y:
            nxt = first_open_item()
            if nxt and nxt != txn and nxt not in st.session_state.decisions:
                button(
                    f"Next: {nxt}",
                    key=f"next_{txn}",
                    primary=True,
                    on_click=go,
                    args=("Investigations", nxt),
                )

    else:
        st.text_area(
            "Note for the reviewer (optional)",
            key=f"note_{txn}",
            placeholder=(
                "For example: confirmed with engineering, "
                "usage spike from load testing."
            ),
        )

        d1, d2, d3, _ = st.columns([1, 1.2, 1, 1.2])

        with d1:
            button(
                "Approve",
                key=f"ap_{txn}",
                primary=True,
                on_click=decide,
                args=(txn, "Approve"),
            )

        with d2:
            button(
                "Request documents",
                key=f"rd_{txn}",
                on_click=decide,
                args=(txn, "Request documents"),
            )

        with d3:
            button(
                "Escalate",
                key=f"es_{txn}",
                on_click=decide,
                args=(txn, "Escalate"),
            )


def page_transactions():
    html(f'<div class="page-title">Transactions</div>'
         f'<p class="page-sub">All {n_total} transactions for {PERIOD}, with the result of each check.</p>')
    f1, f2 = columns([2, 1.3])
    with f1:
        q = st.text_input("Search", placeholder="Transaction ID or vendor", key="tx_q")
    with f2:
        statuses = st.multiselect("Status", ["Clear", "Exception", "Needs review"],
                                  default=["Clear", "Exception", "Needs review"], key="tx_status")

    view = transactions[transactions["Status"].isin(statuses)].copy()
    if q:
        m = view["Transaction"].str.contains(q, case=False) | view["Vendor"].str.contains(q, case=False)
        view = view[m]
    view["Decision"] = view["Transaction"].map(
        lambda t: st.session_state.decisions.get(t, {}).get("decision", ""))
    view = view.sort_values("Transaction")

    html(f'<p class="h2-sub" style="margin-top:6px">Showing {len(view)} of {n_total}. '
         f'Total {money(float(view["Amount"].sum()))}.</p>')
    dataframe(
        view[["Transaction", "Date", "Vendor", "Category", "Amount", "Status", "Finding", "Decision"]],
        hide_index=True,
        height=min(560, 38 + 35 * max(len(view), 1)),
        column_config={
            "Amount": st.column_config.NumberColumn("Amount", format="dollar"),
            "Finding": st.column_config.TextColumn("Finding", width="medium"),
        },
    )
    _, dl = st.columns([3, 1])
    with dl:
        download_button("Download CSV", view.to_csv(index=False).encode("utf-8"),
                        f"finpilot_transactions_{PERIOD.replace(' ', '_').lower()}.csv",
                        "text/csv", "dl_tx")


def page_reports():
    html(f'<div class="page-title">Month-end report</div>'
         f'<p class="page-sub">Summary of the {PERIOD} investigation and the decisions your team recorded.</p>')

    approved = sum(1 for t in flagged_ids
                   if st.session_state.decisions.get(t, {}).get("decision") == "Approved")
    if n_flagged and approved == n_flagged:
        html('<div class="ready yes"><b>Ready to close</b>'
             '<span>Every flagged transaction has been approved.</span></div>')
    else:
        pending = n_flagged - approved
        html(f'<div class="ready no"><b>Not ready to close</b>'
             f'<span>{pending} of {n_flagged} flagged transactions still need approval.</span></div>')

    rows = ""
    for _, r in flagged.iterrows():
        d = st.session_state.decisions.get(r["Transaction"])
        rows += (f"<tr><td class='id'>{r['Transaction']}</td><td>{r['Vendor']}</td>"
                 f"<td>{r['Finding']}</td><td class='r'>{money(float(r['Amount']))}</td>"
                 f"<td>{pill(d['decision'], DECISION_PILL[d['decision']]) if d else pill('Open', 'neu')}</td>"
                 f"<td>{(d or {}).get('note', '') or '—'}</td></tr>")
    flagged_total = float(flagged["Amount"].sum()) if n_flagged else 0.0
    html(f"""
    <div class="card" style="margin-top:18px">
      <div class="card-head"><h3>Flagged transactions</h3>
        <span>{n_decided} of {n_flagged} decided, {money(flagged_total)} under review</span></div>
      <div class="scroll"><table class="tbl">
        <thead><tr><th>Transaction</th><th>Vendor</th><th>Finding</th><th class="r">Amount</th>
        <th>Decision</th><th>Note</th></tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
    </div>""")

    by_cat = (transactions.groupby("Category", dropna=False)["Amount"].agg(["count", "sum"])
              .sort_values("sum", ascending=False).reset_index())
    cat_rows = "".join(
        f"<tr><td>{c or '—'}</td><td class='r'>{int(n)}</td><td class='r'>{money(float(s))}</td></tr>"
        for c, n, s in by_cat.itertuples(index=False))
    html(f"""
    <div class="card" style="margin-top:18px">
      <div class="card-head"><h3>Spending by category</h3>
        <span>{money(float(transactions['Amount'].sum()))} across {n_total} transactions</span></div>
      <div class="scroll"><table class="tbl">
        <thead><tr><th>Category</th><th class="r">Transactions</th><th class="r">Amount</th></tr></thead>
        <tbody>{cat_rows}</tbody></table></div>
    </div>""")

    report = flagged[["Transaction", "Date", "Vendor", "Amount", "Status", "Finding"]].copy()
    report["Decision"] = report["Transaction"].map(
        lambda t: st.session_state.decisions.get(t, {}).get("decision", "Open"))
    report["Note"] = report["Transaction"].map(
        lambda t: st.session_state.decisions.get(t, {}).get("note", ""))
    md = [f"# FinPilot month-end report: {PERIOD}", "",
          f"- Transactions checked: {n_total}", f"- Clear: {n_clear}",
          f"- Exceptions: {n_exc}", f"- Needs review: {n_rev}",
          f"- Decided: {n_decided} of {n_flagged}", "",
          "| Transaction | Vendor | Finding | Amount | Decision | Note |", "|---|---|---|---:|---|---|"]
    for r in report.itertuples(index=False):
        md.append(f"| {r.Transaction} | {r.Vendor} | {r.Finding} | {money(float(r.Amount))} | {r.Decision} | {r.Note} |")

    st.write("")
    _, a, b = st.columns([2, 1, 1])
    with a:
        download_button("Download report (CSV)", report.to_csv(index=False).encode("utf-8"),
                        "finpilot_month_end_report.csv", "text/csv", "dl_rep_csv")
    with b:
        download_button("Download summary (.md)", "\n".join(md).encode("utf-8"),
                        "finpilot_month_end_summary.md", "text/markdown", "dl_rep_md")


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

topbar()
{
    "Overview": page_overview,
    "Investigations": page_investigations,
    "Transactions": page_transactions,
    "Reports": page_reports,
}[st.session_state.page]()
footer()
