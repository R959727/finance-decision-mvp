import streamlit as st

st.title("Financial Decision MVP")

stock = st.text_input("Stock Name")
action = st.selectbox("Action", ["BUY", "SELL"])
price = st.number_input("Price", min_value=0.0)
qty = st.number_input("Quantity", min_value=1)
market = st.selectbox("Market Condition", ["LOW", "HIGH"])

if st.button("Submit"):

    warning = None

    # Basic behavior rule
    if action == "BUY" and market == "HIGH":
        warning = "Risky entry in high volatility"

    # Risk logic
    if market == "HIGH":
        position_size = "5%"
    else:
        position_size = "10%"

    if warning:
        position_size = "3%"

    st.subheader("Decision Output")
    st.write(f"ACTION: {action}")
    st.write(f"POSITION SIZE: {position_size}")

    if warning:
        st.warning(warning)
