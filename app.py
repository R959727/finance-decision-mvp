import streamlit as st
import pandas as pd
import os

st.title("Financial Decision MVP")

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

    # -------- TRADE PAIRING LOGIC --------
    if action == "SELL":
        open_trades = df[df["open"] == True]

        if not open_trades.empty:
            buy_trade = open_trades.iloc[-1]

            pnl = (price - buy_trade["price"]) * qty

            # Mark that BUY as closed
            df.loc[buy_trade.name, "open"] = False

    # -------- CREATE TRADE --------
    new_trade = {
        "action": action,
        "price": price,
        "qty": qty,
        "market": market,
        "pnl": pnl,
        "open": True if action == "BUY" else False
    }

    # -------- SAVE --------
    df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
    df.to_csv(FILE, index=False)

    # -------- BEHAVIOR DETECTION --------
    warning = None

    # Pattern 1: Risky repeated buying
    if len(df) >= 3:
        last_trades = df.tail(3)

        if (last_trades["action"] == "BUY").sum() >= 3 and (last_trades["market"] == "HIGH").sum() >= 2:
            warning = "You are repeatedly buying in high-risk conditions"

    # Pattern 2: Losing streak
    if len(df) >= 3:
        recent_pnl = df.tail(3)["pnl"].sum()

        if recent_pnl < 0:
            warning = "You are in a losing streak — reduce risk"

    # -------- RISK ENGINE --------
    position_size = "10%"

    if market == "HIGH":
        position_size = "5%"

    if warning:
        position_size = "2%"

    # -------- OUTPUT --------
    st.subheader("Decision Output")
    st.write(f"ACTION: {action}")
    st.write(f"POSITION SIZE: {position_size}")

    if warning:
        st.warning(warning)
    else:
        st.success("No risky behavior detected")

# -----------------------------
# SHOW TRADE HISTORY
# -----------------------------
st.subheader("Trade History")
st.dataframe(df)
