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

    required_cols = ["stock","action","price","qty","market","pnl","open"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
else:
    df = pd.DataFrame(columns=["stock","action","price","qty","market","pnl","open"])

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
# PORTFOLIO CALCULATION
# -----------------------------
open_positions = df[df["open"] == True]

# total exposure
total_exposure = (open_positions["price"] * open_positions["qty"]).sum()

# stock-wise exposure
if not open_positions.empty:
    stock_exposure = open_positions.groupby("stock").apply(
        lambda x: (x["price"] * x["qty"]).sum()
    ).reset_index(name="exposure")
else:
    stock_exposure = pd.DataFrame(columns=["stock","exposure"])

# capital
total_pnl = df["pnl"].sum() if "pnl" in df.columns else 0
current_capital = capital + total_pnl
available_capital = current_capital - total_exposure

# -----------------------------
# Submit logic
# -----------------------------
if st.button("Submit"):

    pnl = 0

    # -------- SELL LOGIC --------
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

        # Capital check
        if required_amount > available_capital:
            st.error("Not enough capital")
            st.stop()

        # 🔥 Concentration Risk Check
        current_stock_exp = 0

        if stock in stock_exposure["stock"].values:
            current_stock_exp = stock_exposure[
                stock_exposure["stock"] == stock
            ]["exposure"].values[0]

        new_stock_exp = current_stock_exp + required_amount
        max_allowed = current_capital * 0.3   # 30% limit

        if new_stock_exp > max_allowed:
            st.error("Too much exposure in this stock (limit 30%)")
            st.stop()

    # -------- SAVE TRADE --------
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
        last_trades = df.tail(3)

        if (last_trades["action"] == "BUY").sum() >= 3:
            warning = "Over-buying behavior detected"

        if last_trades["pnl"].sum() < 0:
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
# Trade History
# -----------------------------
st.subheader("Trade History")
st.dataframe(df)
