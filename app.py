import streamlit as st
import pandas as pd
import os

st.title("Financial Decision MVP")

# -----------------------------
# USER CAPITAL INPUT
# -----------------------------
capital = st.number_input("Enter Your Capital (₹)", min_value=100.0, value=10000.0)

# -----------------------------
# FILE SETUP (robust)
# -----------------------------
FILE = "trades.csv"

required_cols = ["stock","action","price","qty","market","pnl","open"]

if os.path.exists(FILE):
    df = pd.read_csv(FILE)

    # ensure schema consistency
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
    st.success("Data reset. Refresh page.")
    st.stop()

# -----------------------------
# PORTFOLIO CALCULATION (SAFE)
# -----------------------------
open_positions = df[df["open"] == True]

# exposure
if not open_positions.empty:
    open_positions["value"] = open_positions["price"] * open_positions["qty"]
    total_exposure = open_positions["value"].sum()

    stock_exposure = open_positions.groupby("stock")["value"].sum().reset_index()
    stock_exposure.rename(columns={"value": "exposure"}, inplace=True)
else:
    total_exposure = 0
    stock_exposure = pd.DataFrame(columns=["stock","exposure"])

# capital
total_pnl = df["pnl"].fillna(0).sum()
current_capital = capital + total_pnl
available_capital = current_capital - total_exposure

# -----------------------------
# SUBMIT LOGIC
# -----------------------------
if st.button("Submit"):

    pnl = 0

    # -------- SELL --------
    if action == "SELL":
        open_trades = df[(df["open"] == True) & (df["stock"] == stock)]

        if open_trades.empty:
            st.error("No open BUY for this stock")
            st.stop()

        buy_trade = open_trades.iloc[-1]
        pnl = (price - buy_trade["price"]) * qty

        df.loc[buy_trade.name, "open"] = False

    # -------- BUY VALIDATION --------
    if action == "BUY":

        required_amount = price * qty

        if required_amount > available_capital:
            st.error("Not enough capital")
            st.stop()

        # concentration risk (30%)
        current_stock_exp = 0

        if not stock_exposure.empty and stock in stock_exposure["stock"].values:
            current_stock_exp = stock_exposure[
                stock_exposure["stock"] == stock
            ]["exposure"].values[0]

        new_exp = current_stock_exp + required_amount
        max_allowed = current_capital * 0.3

        if new_exp > max_allowed:
            st.error("Too much exposure in this stock (limit 30%)")
            st.stop()

    # -------- SAVE --------
    new_trade = {
        "stock": stock,
        "action": action,
        "price": price,
        "qty": qty,
        "market": market,
        "pnl": pnl,
        "open": True if action == "BUY" else False
    }

    df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
    df.to_csv(FILE, index=False)

    # -------- BEHAVIOR --------
    warning = None

    if len(df) >= 3:
        last = df.tail(3)

        if (last["action"] == "BUY").sum() >= 3:
            warning = "Over-buying behavior"

        if last["pnl"].fillna(0).sum() < 0:
            warning = "Losing streak detected"

    # -------- RISK ENGINE --------
    position_size_pct = 10

    if market == "HIGH":
        position_size_pct = 5

    if warning:
        position_size_pct = 1

    position_amount = current_capital * (position_size_pct / 100)

    # -------- CONFIDENCE --------
    confidence = 70

    if market == "HIGH":
        confidence -= 15

    if warning:
        confidence -= 30

    confidence = max(10, min(confidence, 95))

    # -------- OUTPUT --------
    st.subheader("Decision Output")
    st.write(f"STOCK: {stock}")
    st.write(f"ACTION: {action}")
    st.write(f"POSITION SIZE: {position_size_pct}% (₹{round(position_amount,2)})")
    st.write(f"CURRENT CAPITAL: ₹{round(current_capital,2)}")
    st.write(f"AVAILABLE CAPITAL: ₹{round(available_capital,2)}")
    st.write(f"CONFIDENCE: {confidence}%")

    if warning:
        st.warning(warning)
    else:
        st.success("No risk detected")

# -----------------------------
# PORTFOLIO VIEW
# -----------------------------
st.subheader("Portfolio Overview")
st.write(f"Total Exposure: ₹{round(total_exposure,2)}")
st.write(f"Available Capital: ₹{round(available_capital,2)}")

st.subheader("Stock-wise Exposure")
st.dataframe(stock_exposure)

st.subheader("Open Positions")
st.dataframe(open_positions)

# -----------------------------
# TRADE HISTORY
# -----------------------------
st.subheader("Trade History")
st.dataframe(df)
