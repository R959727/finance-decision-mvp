import streamlit as st
import pandas as pd

st.set_page_config(page_title="Financial Decision MVP", layout="wide")

st.title("Financial Decision MVP")

# -----------------------------
# SESSION STATE
# -----------------------------
if "positions" not in st.session_state:
    st.session_state.positions = {}

if "history" not in st.session_state:
    st.session_state.history = []

if "capital" not in st.session_state:
    st.session_state.capital = 10000.0

# -----------------------------
# INPUTS
# -----------------------------
capital = st.number_input("Capital (₹)", value=st.session_state.capital)

stock = st.text_input("Stock", "tata")
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Entry Price", min_value=0.0, value=100.0)
qty = st.number_input("Quantity", min_value=1, value=1)
market = st.selectbox("Market", ["LOW", "HIGH"])

# Live price (IMPORTANT)
current_price = st.number_input("Current Market Price", min_value=0.0, value=price)

# -----------------------------
# RESET
# -----------------------------
if st.button("Reset"):
    st.session_state.positions = {}
    st.session_state.history = []
    st.session_state.capital = 10000.0
    st.success("Reset done")

# -----------------------------
# POSITION DATA
# -----------------------------
positions = st.session_state.positions

total_exposure = sum(
    p["avg_price"] * p["qty"] for p in positions.values()
)

available_capital = capital - total_exposure

# -----------------------------
# VALIDATION
# -----------------------------
invalid = False
if price <= 0:
    st.error("Price must be > 0")
    invalid = True

# -----------------------------
# DECISION ENGINE
# -----------------------------
execute = False

if not invalid:

    score = 60
    reasons = []
    trade_value = price * qty

    if market == "HIGH" and action == "BUY":
        score -= 15
        reasons.append("High volatility")

    if trade_value > capital * 0.2:
        score -= 20
        reasons.append("Too large position")

    if trade_value > available_capital:
        score -= 40
        reasons.append("Not enough capital")

    if stock in positions:
        if (positions[stock]["avg_price"] * positions[stock]["qty"] + trade_value) > capital * 0.3:
            score -= 25
            reasons.append("Overexposed stock")

    score = max(0, min(score, 100))
    confidence = int(score * 0.8)

    if score >= 70:
        rec = "STRONG TRADE"
    elif score >= 50:
        rec = "CAUTION"
    else:
        rec = "AVOID"

    # -----------------------------
    # DISPLAY
    # -----------------------------
    st.subheader("Pre-Trade Analysis")
    st.write(f"Score: {score}/100")
    st.write(f"Confidence: {confidence}%")
    st.write(f"Recommendation: {rec}")

    if reasons:
        st.warning(", ".join(reasons))
    else:
        st.success("High quality setup")

    if rec == "STRONG TRADE":
        if st.button("Execute Trade"):
            execute = True

    elif rec == "CAUTION":
        if st.checkbox("Accept Risk") and st.button("Execute Anyway"):
            execute = True

    else:
        st.error("Blocked")

# -----------------------------
# EXECUTE TRADE
# -----------------------------
if execute:

    if action == "BUY":
        if stock in positions:
            old_qty = positions[stock]["qty"]
            old_price = positions[stock]["avg_price"]

            new_qty = old_qty + qty
            new_price = ((old_price * old_qty) + (price * qty)) / new_qty

            positions[stock]["qty"] = new_qty
            positions[stock]["avg_price"] = new_price
        else:
            positions[stock] = {
                "qty": qty,
                "avg_price": price
            }

    st.session_state.history.append({
        "stock": stock,
        "action": action,
        "price": price,
        "qty": qty
    })

    st.success("Trade executed")

# -----------------------------
# PORTFOLIO VIEW
# -----------------------------
st.subheader("Portfolio")

rows = []

for s, p in positions.items():
    unrealized = (current_price - p["avg_price"]) * p["qty"]
    rows.append({
        "stock": s,
        "qty": p["qty"],
        "avg_price": p["avg_price"],
        "current_price": current_price,
        "unrealized_pnl": unrealized
    })

portfolio_df = pd.DataFrame(rows)

if not portfolio_df.empty:
    st.dataframe(portfolio_df)

# -----------------------------
# CLOSE POSITIONS
# -----------------------------
st.subheader("Close Positions")

for s in list(positions.keys()):
    if st.button(f"Close {s}"):

        p = positions[s]
        pnl = (current_price - p["avg_price"]) * p["qty"]

        st.session_state.capital += pnl

        st.session_state.history.append({
            "stock": s,
            "action": "SELL",
            "price": current_price,
            "qty": p["qty"],
            "pnl": pnl
        })

        del positions[s]

        st.success(f"Closed {s} | PnL: ₹{pnl}")

# -----------------------------
# SUMMARY
# -----------------------------
st.subheader("Summary")
st.write(f"Capital: ₹{st.session_state.capital}")
st.write(f"Exposure: ₹{total_exposure}")
st.write(f"Available: ₹{available_capital}")

# -----------------------------
# HISTORY
# -----------------------------
st.subheader("Trade History")

if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history))
