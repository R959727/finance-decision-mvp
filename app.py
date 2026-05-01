import streamlit as st
import pandas as pd
import time

st.set_page_config(layout="wide")

st.title("Financial Decision MVP - Pro")

# ---------------- STATE ----------------
if "positions" not in st.session_state:
    st.session_state.positions = {}

if "history" not in st.session_state:
    st.session_state.history = []

if "capital" not in st.session_state:
    st.session_state.capital = 10000.0

if "last_trade_time" not in st.session_state:
    st.session_state.last_trade_time = {}

# ---------------- INPUT ----------------
capital = st.number_input("Capital", value=st.session_state.capital)

stock = st.text_input("Stock", "tata").lower()
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Price", min_value=0.0, value=100.0)
qty = st.number_input("Quantity", min_value=1, value=1)
market = st.selectbox("Market", ["LOW", "HIGH"])
current_price = st.number_input("Current Price", min_value=0.0, value=price)

positions = st.session_state.positions

# ---------------- CALCULATIONS ----------------
total_exposure = sum(p["avg_price"] * p["qty"] for p in positions.values())
available_capital = capital - total_exposure

stock_exposure = 0
if stock in positions:
    stock_exposure = positions[stock]["avg_price"] * positions[stock]["qty"]

trade_value = price * qty

# ---------------- DECISION ENGINE ----------------
score = 60
reasons = []

# Volatility penalty
if market == "HIGH":
    score -= 10
    reasons.append("High volatility")

# Position size check
if trade_value > capital * 0.2:
    score -= 20
    reasons.append("Too large position")

# Capital check
if trade_value > available_capital:
    score -= 40
    reasons.append("Insufficient capital")

# Stock exposure limit (30%)
if (stock_exposure + trade_value) > capital * 0.3:
    score -= 30
    reasons.append("Overexposed stock")

# Cooldown check (10 seconds demo)
now = time.time()
if stock in st.session_state.last_trade_time:
    if now - st.session_state.last_trade_time[stock] < 10:
        score -= 50
        reasons.append("Cooldown active")

score = max(0, min(score, 100))
confidence = int(score * 0.8)

# ---------------- RECOMMENDATION ----------------
if score >= 70:
    rec = "STRONG TRADE"
elif score >= 50:
    rec = "CAUTION"
else:
    rec = "BLOCKED"

# ---------------- DISPLAY ----------------
st.subheader("Pre-Trade Analysis")
st.write(f"Score: {score}/100")
st.write(f"Confidence: {confidence}%")
st.write(f"Recommendation: {rec}")

if reasons:
    st.warning(", ".join(reasons))
else:
    st.success("Strong setup")

# ---------------- EXECUTION LOGIC ----------------
execute = False

if rec == "STRONG TRADE":
    if st.button("Execute Trade"):
        execute = True

elif rec == "CAUTION":
    st.warning("Manual override required")
    if st.checkbox("Accept Risk") and st.button("Execute Anyway"):
        execute = True

else:
    st.error("Trade blocked — system protection")

# ---------------- EXECUTE ----------------
if execute:

    # BUY
    if action == "BUY":
        if stock in positions:
            old_qty = positions[stock]["qty"]
            old_price = positions[stock]["avg_price"]

            new_qty = old_qty + qty
            new_price = ((old_price * old_qty) + (price * qty)) / new_qty

            positions[stock]["qty"] = new_qty
            positions[stock]["avg_price"] = new_price
        else:
            positions[stock] = {"qty": qty, "avg_price": price}

    # Track cooldown
    st.session_state.last_trade_time[stock] = time.time()

    # Log
    st.session_state.history.append({
        "stock": stock,
        "action": action,
        "price": price,
        "qty": qty
    })

    st.success("Trade executed")

# ---------------- PORTFOLIO ----------------
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

df = pd.DataFrame(rows)
if not df.empty:
    st.dataframe(df)

# ---------------- CLOSE ----------------
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

# ---------------- SUMMARY ----------------
st.subheader("Summary")
st.write(f"Capital: ₹{st.session_state.capital}")
st.write(f"Exposure: ₹{total_exposure}")
st.write(f"Available: ₹{available_capital}")

# ---------------- HISTORY ----------------
st.subheader("Trade History")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history))
