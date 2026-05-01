import streamlit as st
import pandas as pd

st.set_page_config(page_title="Financial Decision MVP", layout="wide")

st.title("Financial Decision MVP")

# -----------------------------
# SESSION STATE
# -----------------------------
if "trades" not in st.session_state:
    st.session_state.trades = []

if "capital" not in st.session_state:
    st.session_state.capital = 10000.0


# -----------------------------
# INPUTS
# -----------------------------
capital = st.number_input("Enter Your Capital (₹)", value=st.session_state.capital)

stock = st.text_input("Stock Name", value="tata")
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Price", min_value=0.0, value=100.0)
qty = st.number_input("Quantity", min_value=1, value=1)
market = st.selectbox("Market Condition", ["LOW", "HIGH"])

# -----------------------------
# RESET
# -----------------------------
if st.button("Reset Data"):
    st.session_state.trades = []
    st.session_state.capital = 10000.0
    st.success("Data reset")

# -----------------------------
# DATAFRAME
# -----------------------------
df = pd.DataFrame(st.session_state.trades)

if not df.empty:
    open_positions = df[df["open"] == True].copy()
    open_positions["value"] = open_positions["price"] * open_positions["qty"]
else:
    open_positions = pd.DataFrame()

# -----------------------------
# CAPITAL CALCULATION
# -----------------------------
if not open_positions.empty:
    total_exposure = open_positions["value"].sum()
else:
    total_exposure = 0

available_capital = capital - total_exposure

# -----------------------------
# VALIDATION
# -----------------------------
invalid_input = False

if price <= 0:
    st.error("Price must be > 0")
    invalid_input = True

# -----------------------------
# DECISION ENGINE (RUN ONCE)
# -----------------------------
execute_trade = False

if not invalid_input:

    score = 60
    reasons = []

    trade_value = price * qty

    # MARKET LOGIC
    if market == "HIGH":
        if action == "BUY":
            score -= 15
            reasons.append("Buying in high volatility")
        else:
            score += 10

    if market == "LOW":
        if action == "BUY":
            score += 10
        else:
            score -= 10
            reasons.append("Selling in low momentum")

    # SIZE CONTROL
    if trade_value > capital * 0.2:
        score -= 20
        reasons.append("Position too large")

    if trade_value > available_capital:
        score -= 40
        reasons.append("Insufficient capital")

    # LOSS STREAK
    if not df.empty:
        last_3 = df.tail(3)["pnl"].fillna(0)
        if (last_3 < 0).sum() >= 2:
            score -= 20
            reasons.append("Losing streak")

    score = max(0, min(score, 100))
    confidence = int(score * 0.8)

    if score >= 70:
        rec = "STRONG TRADE"
    elif score >= 50:
        rec = "CAUTION"
    else:
        rec = "AVOID"

    # -----------------------------
    # DISPLAY ANALYSIS
    # -----------------------------
    st.subheader("Pre-Trade Analysis")
    st.write(f"Score: {score}/100")
    st.write(f"Confidence: {confidence}%")
    st.write(f"Recommendation: {rec}")

    if reasons:
        st.warning(", ".join(reasons))
    else:
        st.success("High quality setup")

    # -----------------------------
    # EXECUTION CONTROL
    # -----------------------------
    if rec == "STRONG TRADE":
        if st.button("Execute Trade"):
            execute_trade = True

    elif rec == "CAUTION":
        confirm = st.checkbox("I understand the risk")
        if confirm and st.button("Execute Anyway"):
            execute_trade = True

    else:
        st.error("Trade blocked — too risky")

# -----------------------------
# EXECUTION
# -----------------------------
if execute_trade:

    new_trade = {
        "stock": stock,
        "action": action,
        "price": price,
        "qty": qty,
        "market": market,
        "pnl": 0,
        "open": True
    }

    st.session_state.trades.append(new_trade)
    st.success("Trade executed")

# -----------------------------
# PORTFOLIO OVERVIEW
# -----------------------------
st.subheader("Portfolio Overview")
st.write(f"Total Exposure: ₹{total_exposure}")
st.write(f"Available Capital: ₹{available_capital}")

# -----------------------------
# OPEN POSITIONS
# -----------------------------
st.subheader("Open Positions")
if not open_positions.empty:
    st.dataframe(open_positions)
else:
    st.write("No open positions")

# -----------------------------
# TRADE HISTORY
# -----------------------------
st.subheader("Trade History")
if not df.empty:
    st.dataframe(df)
else:
    st.write("No trades yet")
