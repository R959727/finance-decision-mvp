import streamlit as st
import pandas as pd
import os

st.title("Financial Decision MVP")

# -----------------------------
# CAPITAL INPUT
# -----------------------------
capital = st.number_input("Enter Your Capital (₹)", min_value=100.0, value=10000.0)

FILE = "trades.csv"
required_cols = ["stock","action","price","qty","market","pnl","open"]

# -----------------------------
# LOAD DATA
# -----------------------------
if os.path.exists(FILE):
    df = pd.read_csv(FILE)
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
else:
    df = pd.DataFrame(columns=required_cols)

# -----------------------------
# INPUT
# -----------------------------
stock = st.text_input("Stock Name")
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Price", min_value=0.0)
qty = st.number_input("Quantity", min_value=1)
market = st.selectbox("Market Condition", ["LOW", "HIGH"])

# -----------------------------
# RESET
# -----------------------------
if st.button("Reset Data"):
    if os.path.exists(FILE):
        os.remove(FILE)
    st.success("Reset done. Refresh.")
    st.stop()

# -----------------------------
# PORTFOLIO CALCULATION
# -----------------------------
open_positions = df[df["open"] == True]

if not open_positions.empty:
    open_positions = open_positions.copy()
    open_positions["value"] = open_positions["price"] * open_positions["qty"]
    total_exposure = open_positions["value"].sum()

    stock_exposure = open_positions.groupby("stock")["value"].sum().reset_index()
    stock_exposure.rename(columns={"value": "exposure"}, inplace=True)
else:
    total_exposure = 0
    stock_exposure = pd.DataFrame(columns=["stock","exposure"])

total_pnl = df["pnl"].fillna(0).sum()
current_capital = capital + total_pnl
available_capital = current_capital - total_exposure

# -----------------------------
# INPUT VALIDATION (NON-BLOCKING)
# -----------------------------
invalid_input = False

if not stock or stock.strip() == "":
    st.error("Stock required")
    invalid_input = True

if price <= 0:
    st.error("Price must be > 0")
    invalid_input = True

if qty <= 0:
    st.error("Quantity must be >= 1")
    invalid_input = True

# -----------------------------
# DECISION ENGINE (ONLY IF VALID)
# -----------------------------
if not invalid_input:

    score = 70
    reasons = []

    trade_value = price * qty

    # volatility
    if market == "HIGH":
        score -= 25
        reasons.append("High volatility")

    # size
    if trade_value > current_capital * 0.2:
        score -= 20
        reasons.append("Too large position")

    # capital pressure
    if trade_value > available_capital:
        score -= 30
        reasons.append("Not enough capital")

    # concentration
    current_stock_exp = 0
    if not stock_exposure.empty and stock in stock_exposure["stock"].values:
        current_stock_exp = stock_exposure[
            stock_exposure["stock"] == stock
        ]["exposure"].values[0]

    if current_stock_exp > current_capital * 0.3:
        score -= 20
        reasons.append("Overexposed stock")

    # recent losses
    recent_losses = df.tail(3)["pnl"].fillna(0).sum()
    if recent_losses < 0:
        score -= 20
        reasons.append("Recent losses")

    score = max(0, min(score, 100))

    # recommendation
    if score >= 70:
        rec = "TAKE TRADE"
    elif score >= 50:
        rec = "CAUTION"
    else:
        rec = "AVOID"

    # display
    st.subheader("Pre-Trade Analysis")
    st.write(f"Score: {score}/100")
    st.write(f"Recommendation: {rec}")

    if reasons:
        st.warning(", ".join(reasons))
    else:
        st.success("Strong setup")

# -----------------------------
# EXECUTION FUNCTION
# -----------------------------
def execute_trade(exec_qty):
    global df

    if not stock or stock.strip() == "":
        st.error("Stock required")
        return

    if price <= 0:
        st.error("Price must be > 0")
        return

    if exec_qty <= 0:
        st.error("Qty must be >= 1")
        return

    pnl = 0

    # SELL
    if action == "SELL":
        open_trades = df[(df["open"] == True) & (df["stock"] == stock)]

        if open_trades.empty:
            st.error("No BUY to sell")
            return

        buy_trade = open_trades.iloc[-1]
        pnl = (price - buy_trade["price"]) * exec_qty
        df.loc[buy_trade.name, "open"] = False

    # BUY
    if action == "BUY":
        required = price * exec_qty

        if required > available_capital:
            st.error("Not enough capital")
            return

    # SAVE
    new_trade = {
        "stock": stock.strip(),
        "action": action,
        "price": price,
        "qty": exec_qty,
        "market": market,
        "pnl": pnl,
        "open": True if action == "BUY" else False
    }

    df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
    df.to_csv(FILE, index=False)

    st.success("Trade executed")

# -----------------------------
# EXECUTION CONTROL
# -----------------------------
if not invalid_input:

    if score >= 70:
        if st.button("Execute Trade"):
            execute_trade(qty)

    elif 50 <= score < 70:
        st.warning("Medium risk → size reduced")

        confirm = st.checkbox("Proceed anyway")

        if confirm and st.button("Execute Limited Trade"):
            reduced_qty = max(1, int(qty * 0.5))
            execute_trade(reduced_qty)

    else:
        st.error("Blocked: bad trade")

# -----------------------------
# PORTFOLIO VIEW (ALWAYS VISIBLE)
# -----------------------------
st.subheader("Portfolio Overview")
st.write(f"Total Exposure: ₹{round(total_exposure,2)}")
st.write(f"Available Capital: ₹{round(available_capital,2)}")

st.subheader("Stock-wise Exposure")
st.dataframe(stock_exposure)

st.subheader("Open Positions")
st.dataframe(open_positions)

st.subheader("Trade History")
st.dataframe(df)
