from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

def get_share_price(symbol: str) -> float:
    prices = {
        "AAPL": 150.0,
        "TSLA": 800.0,
        "GOOGL": 2800.0,
    }
    symbol_upper = symbol.upper()
    if symbol_upper not in prices:
        raise KeyError(f"Unsupported symbol: {symbol}")
    return prices[symbol_upper]

@dataclass
class Transaction:
    symbol: str
    quantity: int
    price: float
    timestamp: datetime = field(default_factory=lambda: datetime.now())

@dataclass
class Account:
    user_id: str
    initial_balance: float
    balance: float = field(init=False, default=0.0)
    holdings: Dict[str, int] = field(default_factory=dict)
    transactions: List[Transaction] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.initial_balance < 0:
            raise ValueError("initial_balance must be non‑negative")
        self.balance = self.initial_balance

    # ----- public API -----
    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self._record_transaction(symbol="CASH", quantity=-1, price=amount)

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        self._ensure_funds(amount)
        self.balance -= amount
        self._record_transaction(symbol="CASH", quantity=1, price=amount)

    def buy_share(self, symbol: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        price = get_share_price(symbol)
        cost = price * quantity
        self._ensure_funds(cost)
        self.balance -= cost
        self._update_holdings(symbol, quantity)
        self._record_transaction(symbol=symbol, quantity=-quantity, price=price)

    def sell_share(self, symbol: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError("Insufficient shares to sell")
        price = get_share_price(symbol)
        proceeds = price * quantity
        self.balance += proceeds
        self._update_holdings(symbol, -quantity)
        self._record_transaction(symbol=symbol, quantity=quantity, price=price)

    def get_holdings(self) -> Dict[str, int]:
        return self.holdings.copy()

    def get_portfolio_value(self) -> float:
        total = 0.0
        for symbol, qty in self.holdings.items():
            total += qty * get_share_price(symbol)
        return total

    def get_profit_loss(self, initial_deposit: float) -> float:
        return self.get_portfolio_value() - initial_deposit

    def list_transactions(self) -> List[Transaction]:
        return self.transactions.copy()

    # ----- helpers -----
    def _ensure_funds(self, amount: float) -> None:
        if self.balance < amount:
            raise ValueError("Insufficient funds for operation")

    def _record_transaction(self, symbol: str, quantity: int, price: float) -> None:
        txn = Transaction(symbol=symbol, quantity=quantity, price=price)
        self.transactions.append(txn)

    def _update_holdings(self, symbol: str, quantity: int) -> None:
        current = self.holdings.get(symbol, 0)
        new_total = current + quantity
        if new_total > 0:
            self.holdings[symbol] = new_total
        elif new_total == 0:
            if symbol in self.holdings:
                del self.holdings[symbol]
        else:
            raise ValueError("Holdings cannot become negative")

    def __repr__(self) -> str:
        return (f"Account(user_id={self.user_id}, "
                f"balance={self.balance:.2f}, "
                f"holdings={self.holdings}, "
                f"transactions={len(self.transactions)})")