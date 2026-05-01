import streamlit as st
import pandas as pd
import time

st.set_page_config(layout="wide")

st.title("Financial Decision System - Real Engine")

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
stock = st.text_input("Stock", "tata").lower()
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Price", min_value=0.0, value=100.0)
qty = st.number_input("Quantity", min_value=1, value=1)
market = st.selectbox("Market", ["LOW", "HIGH"])
current_price = st.number_input("Current Price", min_value=0.0, value=price)

positions = st.session_state.positions
capital = st.session_state.capital

# ---------------- VALIDATION ----------------
invalid = False

if price <= 0:
    st.error("Price must be > 0")
    invalid = True

if stock == "":
    st.error("Stock required")
    invalid = True

# price sanity (prevent nonsense inputs)
if stock in positions:
    avg = positions[stock]["avg_price"]
    if price > avg * 5 or price < avg * 0.2:
        st.warning("Unrealistic price vs previous trades")

# ---------------- CALCULATIONS ----------------
total_exposure = sum(p["avg_price"] * p["qty"] for p in positions.values())

stock_exposure = positions[stock]["avg_price"] * positions[stock]["qty"] if stock in positions else 0
trade_value = price * qty

# ---------------- DECISION ENGINE ----------------
score = 60
reasons = []

if market == "HIGH":
    score -= 10
    reasons.append("High volatility")

if trade_value > capital:
    score -= 40
    reasons.append("Not enough capital")

if (stock_exposure + trade_value) > capital * 0.3:
    score -= 25
    reasons.append("Overexposed stock")

# cooldown
now = time.time()
if stock in st.session_state.last_trade_time:
    if now - st.session_state.last_trade_time[stock] < 10:
        score -= 50
        reasons.append("Cooldown active")

score = max(0, min(score, 100))
confidence = int(score * 0.8)

if score >= 70:
    rec = "STRONG"
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
    st.success("Good setup")

# ---------------- EXECUTION ----------------
execute = False

if not invalid:
    if rec == "STRONG":
        if st.button("Execute"):
            execute = True
    elif rec == "CAUTION":
        if st.checkbox("Accept Risk") and st.button("Force Execute"):
            execute = True
    else:
        st.error("Trade blocked")

# ---------------- APPLY TRADE ----------------
if execute:

    if action == "BUY":

        if trade_value > capital:
            st.error("Not enough capital")
        else:
            # Deduct capital
            st.session_state.capital -= trade_value

            if stock in positions:
                old_qty = positions[stock]["qty"]
                old_price = positions[stock]["avg_price"]

                new_qty = old_qty + qty
                new_price = ((old_price * old_qty) + trade_value) / new_qty

                positions[stock]["qty"] = new_qty
                positions[stock]["avg_price"] = new_price
            else:
                positions[stock] = {"qty": qty, "avg_price": price}

            st.success("BUY executed")

    elif action == "SELL":

        if stock not in positions:
            st.error("No position to sell")
        else:
            p = positions[stock]

            sell_qty = min(qty, p["qty"])
            pnl = (price - p["avg_price"]) * sell_qty

            # Add capital back
            st.session_state.capital += sell_qty * price

            p["qty"] -= sell_qty

            if p["qty"] == 0:
                del positions[stock]

            st.success(f"SELL executed | PnL: ₹{pnl}")

    st.session_state.last_trade_time[stock] = time.time()

    st.session_state.history.append({
        "stock": stock,
        "action": action,
        "price": price,
        "qty": qty
    })

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

# ---------------- SUMMARY ----------------
st.subheader("Summary")

total_exposure = sum(p["avg_price"] * p["qty"] for p in positions.values())

st.write(f"Capital: ₹{st.session_state.capital}")
st.write(f"Exposure: ₹{total_exposure}")
st.write(f"Total Equity: ₹{st.session_state.capital + total_exposure}")

# ---------------- HISTORY ----------------
st.subheader("Trade History")

if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history))
