import streamlit as st
import pandas as pd
import os

st.title("Financial Decision MVP")

# -----------------------------
# USER CAPITAL INPUT
# -----------------------------
capital = st.number_input("Enter Your Capital (₹)", min_value=100.0, value=10000.0)

# -----------------------------
# File setup
# -----------------------------
FILE = "trades.csv"

if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame(columns=["action", "price", "qty", "market", "pnl", "open"])

# -----------------------------
# Input
# -----------------------------
stock = st.text_input("Stock Name")
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Price", min_value=0.0)
qty = st.number_input("Quantity", min_value=1)
market = st.selectbox("Market Condition", ["LOW", "HIGH"])

# -----------------------------
# Reset Data
# -----------------------------
if st.button("Reset Data"):
    if os.path.exists(FILE):
        os.remove(FILE)
    st.success("Data reset. Refresh page.")
    st.stop()

# -----------------------------
# Submit logic
# -----------------------------
if st.button("Submit"):

    pnl = 0

    # -------- Prevent invalid SELL --------
    if action == "SELL":
        open_trades = df[df["open"] == True]

        if open_trades.empty:
            st.error("No open BUY trade to sell")
            st.stop()

        buy_trade = open_trades.iloc[-1]
        pnl = (price - buy_trade["price"]) * qty

        df.loc[buy_trade.name, "open"] = False

    # -------- Create Trade --------
    new_trade = {
        "action": action,
        "price": price,
        "qty": qty,
        "market": market,
        "pnl": pnl,
        "open": True if action == "BUY" else False
    }

    # -------- Save --------
    df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
    df.to_csv(FILE, index=False)

    # -------- BEHAVIOR DETECTION --------
    warning = None

    if len(df) >= 3:
        last_trades = df.tail(3)

        if (last_trades["action"] == "BUY").sum() >= 3 and (last_trades["market"] == "HIGH").sum() >= 2:
            warning = "You are repeatedly buying in high-risk conditions"

    if len(df) >= 3:
        if df.tail(3)["pnl"].sum() < 0:
            warning = "You are in a losing streak — reduce risk"

    # -------- EMOTIONAL DETECTION --------
    if len(df) >= 2:
        last_trade = df.iloc[-1]
        prev_trade = df.iloc[-2]

        if prev_trade["action"] == "BUY" and last_trade["action"] == "SELL":
            if last_trade["pnl"] < 0:
                warning = "Panic selling detected"

        if prev_trade["pnl"] < 0 and last_trade["action"] == "BUY":
            warning = "Revenge trading detected"

    # -------- RISK ENGINE --------
    position_size_pct = 10

    if market == "HIGH":
        position_size_pct = 5

    if warning:
        position_size_pct = 1

    # -------- CAPITAL CALCULATION --------
    position_amount = capital * (position_size_pct / 100)

    total_pnl = df["pnl"].sum()
    current_capital = capital + total_pnl

    # -------- CONFIDENCE SYSTEM --------
    confidence = 70

    if market == "HIGH":
        confidence -= 15

    if warning:
        confidence -= 30

    if len(df) >= 3:
        if df.tail(3)["pnl"].sum() < 0:
            confidence -= 20

    confidence = max(10, min(confidence, 95))

    # -------- OUTPUT --------
    st.subheader("Decision Output")
    st.write(f"ACTION: {action}")
    st.write(f"POSITION SIZE: {position_size_pct}% (₹{round(position_amount,2)})")
    st.write(f"CURRENT CAPITAL: ₹{round(current_capital,2)}")
    st.write(f"CONFIDENCE: {confidence}%")

    if warning:
        st.warning(warning)
    else:
        st.success("No risky behavior detected")

# -----------------------------
# Trade History
# -----------------------------
st.subheader("Trade History")
st.dataframe(df)
