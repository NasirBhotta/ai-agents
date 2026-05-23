from accounts import Account
import gradio as gr
from datetime import datetime
from typing import Dict, List

def get_share_price(symbol: str) -> float:
    prices = { "AAPL": 150.0, "TSLA": 800.0, "GOOGL": 2800.0, }
    symbol_upper = symbol.upper()
    if symbol_upper not in prices:
        raise KeyError(f"Unsupported symbol: {symbol}")
    return prices[symbol_upper]

def init_state():
    return None


def safe_create_account(initial_balance):
    acc = Account(user_id="user1", initial_balance=initial_balance)
    return "Account created", gr.update(value=acc)

def safe_deposit(state, amount):
    if state is None:
        return "Please create an account first", gr.update(value=None)
    state.deposit(amount)
    return "Deposited", gr.update(value=state)

def safe_withdraw(state, amount):
    if state is None:
        return "Please create an account first", gr.update(value=None)
    try:
        state.withdraw(amount)
        return "Withdrawn", gr.update(value=state)
    except ValueError as e:
        return str(e), gr.update(value=state)

def safe_buy(state, symbol, quantity):
    if state is None:
        return "Please create an account first", gr.update(value=None)
    try:
        state.buy_share(symbol, quantity)
        return "Bought", gr.update(value=state)
    except ValueError as e:
        return str(e), gr.update(value=state)

def safe_sell(state, symbol, quantity):
    if state is None:
        return "Please create an account first", gr.update(value=None)
    try:
        state.sell_share(symbol, quantity)
        return "Sold", gr.update(value=state)
    except ValueError as e:
        return str(e), gr.update(value=state)

def safe_show_holdings(state):
    if state is None:
        return "Please create an account first"
    return f"Holdings: {state.get_holdings()}"

def safe_portfolio(state):
    if state is None:
        return "Please create an account first"
    return f"Portfolio Value: ${state.get_portfolio_value():.2f}"

def safe_profit(state):
    if state is None:
        return "Please create an account first"
    return f"Profit/Loss: ${state.get_profit_loss(state.initial_balance):.2f}"

def safe_transactions(state):
    if state is None:
        return "Please create an account first"
    trans = state.list_transactions()
    lines = [f"{t.timestamp} | {t.symbol} | Qty: {t.quantity} | Price: {t.price:.2f}" for t in trans]
    return "\n".join(lines) if lines else "No transactions"

with gr.Blocks() as demo:
    gr.Markdown("## Create Account")
    init_balance = gr.Number(label="Initial Balance", value=1000.0)
    btn_create = gr.Button("Create Account")
    status_box = gr.Textbox(label="Status", interactive=False)
    state = gr.State(None)
    btn_create.click(fn=safe_create_account, inputs=init_balance, outputs=[status_box, state])

    # Deposit
    gr.Markdown("## Deposit")
    deposit_amt = gr.Number(label="Deposit Amount")
    btn_deposit = gr.Button("Deposit")
    deposit_status = gr.Textbox(label="Deposit Result", interactive=False)
    btn_deposit.click(fn=safe_deposit, inputs=[state, deposit_amt], outputs=[deposit_status, state])

    # Withdraw
    gr.Markdown("## Withdraw")
    withdraw_amt = gr.Number(label="Withdraw Amount")
    btn_withdraw = gr.Button("Withdraw")
    withdraw_status = gr.Textbox(label="Withdraw Result", interactive=False)
    btn_withdraw.click(fn=safe_withdraw, inputs=[state, withdraw_amt], outputs=[withdraw_status, state])

    # Buy Share
    gr.Markdown("## Buy Share")
    buy_symbol = gr.Textbox(label="Symbol (e.g., AAPL)")
    buy_qty = gr.Number(label="Quantity")
    btn_buy = gr.Button("Buy")
    buy_status = gr.Textbox(label="Buy Result", interactive=False)
    btn_buy.click(fn=safe_buy, inputs=[state, buy_symbol, buy_qty], outputs=[buy_status, state])

    # Sell Share
    gr.Markdown("## Sell Share")
    sell_symbol = gr.Textbox(label="Symbol")
    sell_qty = gr.Number(label="Quantity")
    btn_sell = gr.Button("Sell")
    sell_status = gr.Textbox(label="Sell Result", interactive=False)
    btn_sell.click(fn=safe_sell, inputs=[state, sell_symbol, sell_qty], outputs=[sell_status, state])

    # Show Holdings
    btn_holdings = gr.Button("Show Holdings")
    holdings_md = gr.Markdown(label="Holdings")
    btn_holdings.click(fn=safe_show_holdings, inputs=state, outputs=holdings_md)

    # Portfolio Value
    btn_portfolio = gr.Button("Portfolio Value")
    portfolio_md = gr.Markdown(label="Portfolio Value")
    btn_portfolio.click(fn=safe_portfolio, inputs=state, outputs=portfolio_md)

    # Profit/Loss
    btn_pl = gr.Button("Profit/Loss")
    pl_md = gr.Markdown(label="Profit/Loss")
    btn_pl.click(fn=safe_profit, inputs=state, outputs=pl_md)

    # List Transactions
    btn_transactions = gr.Button("List Transactions")
    trans_md = gr.Markdown(label="Transactions")
    btn_transactions.click(fn=safe_transactions, inputs=state, outputs=trans_md)

if __name__ == "__main__":
    demo.launch()