import streamlit as st
import pandas as pd
import os

st.title("Financial Decision MVP")

# File setup
FILE = "trades.csv"

if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame(columns=["action", "price", "qty", "market"])

# Input
stock = st.text_input("Stock Name")
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Price", min_value=0.0)
qty = st.number_input("Quantity", min_value=1)
market = st.selectbox("Market Condition", ["LOW", "HIGH"])

if st.button("Submit"):

    # Save trade
    new_trade = {
        "action": action,
        "price": price,
        "qty": qty,
        "market": market
    }

    df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
    df.to_csv(FILE, index=False)

    # Behavior detection
    warning = None

    if len(df) >= 3:
        last_trades = df.tail(3)

        if (last_trades["action"] == "BUY").sum() >= 3 and (last_trades["market"] == "HIGH").sum() >= 2:
            warning = "You are repeatedly buying in high-risk conditions"

    # Risk engine
    position_size = "10%"

    if market == "HIGH":
        position_size = "5%"

    if warning:
        position_size = "2%"

    # Output
    st.subheader("Decision Output")
    st.write(f"ACTION: {action}")
    st.write(f"POSITION SIZE: {position_size}")

    if warning:
        st.warning(warning)
