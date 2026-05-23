# accounts.py – Design Overview  

This module implements a **self‑contained** account management system for a trading‑simulation platform. All logic resides in a single Python file (`accounts.py`) and the public API is the **`Account`** class. The design follows the stated requirements and anticipates common runtime errors (e.g., import‑time failures from dataclass field ordering).

---  

## 1. High‑Level Structure  

| Component | Purpose |
|-----------|---------|
| **`Transaction` dataclass** | Immutable record of a single trade (buy or sell). |
| **`Account` dataclass** | Core entity representing a user’s account; holds balance, share holdings, and a chronological list of `Transaction` objects. |
| **`get_share_price(symbol)`** | External API stub (provided by the platform) that returns the current price of a share. A test implementation returns fixed prices for **AAPL**, **TSLA**, **GOOGL**. |
| **Helper methods** (private) | Validate operations (withdrawal, purchase, sale) and update state atomically. |

All classes are defined with **dataclasses** to keep the code concise and type‑safe.  

---  

## 2. Dataclass Design (field ordering compliance)  

### 2.1 `Transaction`  

```text
@dataclass
class Transaction:
    symbol: str                     # required – identifier of the security
    quantity: int                   # required – number of shares traded
    price: float                    # required – execution price per share
    timestamp: datetime = field(default_factory=datetime.now)  # defaulted
```

*Required fields (`symbol`, `quantity`, `price`) appear first.*  
*The only field with a default (`timestamp`) follows them, satisfying the “required‑first” rule.*

### 2.2 `Account`  

```text
@dataclass
class Account:
    user_id: str                                 # required – unique identifier
    initial_balance: float                       # required – deposit made at creation
    balance: float = field(init=False, default=0.0)   # derived, not user‑set
    holdings: Dict[str, int] = field(default_factory=dict)  # required‑like, defaulted
    transactions: List[Transaction] = field(default_factory=list)  # required‑like, defaulted
```

*Required fields (`user_id`, `initial_balance`) are listed first.*  
*Fields that are automatically created (`balance`, `holdings`, `transactions`) are placed after the required ones and use `default_factory` to avoid mutable default values.*

---  

## 3. Public Methods of `Account`  

| Method | Signature | Description |
|--------|-----------|-------------|
| **Constructor** | `__init__(self, user_id: str, initial_balance: float = 0.0) -> None` | Validates `initial_balance >= 0`, sets `balance` = `initial_balance`, creates empty `holdings` and `transactions`. |
| **deposit** | `def deposit(self, amount: float) -> None` | Adds `amount` to `balance`; records a *deposit* transaction (type can be inferred by sign of quantity). |
| **withdraw** | `def withdraw(self, amount: float) -> None` | Checks `balance >= amount`; if true, subtracts `amount` from `balance` and records a withdrawal transaction. Raises `ValueError` otherwise. |
| **buy_share** | `def buy_share(self, symbol: str, quantity: int) -> None` | 1. Retrieves current price via `get_share_price(symbol)`.<br>2. Computes `cost = price * quantity`.<br>3. Validates `balance >= cost`; otherwise raises `ValueError`.<br>4. Updates `balance` (`balance -= cost`).<br>5. Increments `holdings[symbol]` (create entry if missing).<br>6. Records a `Transaction` with **negative** quantity to indicate cash outflow. |
| **sell_share** | `def sell_share(self, symbol: str, quantity: int) -> None` | 1. Ensures `symbol` exists in `holdings` and `holdings[symbol] >= quantity`; otherwise raises `ValueError`.<br>2. Retrieves current price via `get_share_price(symbol)`.<br>3. Computes `proceeds = price * quantity`.<br>4. Adds `proceeds` to `balance`.<br>5. Decrements `holdings[symbol]`; removes the key if quantity reaches 0.<br>6. Records a `Transaction` with **positive** quantity to indicate cash inflow. |
| **get_holdings** | `def get_holdings(self) -> Dict[str, int]` | Returns a **copy** of the internal `holdings` dictionary (read‑only). |
| **get_portfolio_value** | `def get_portfolio_value(self) -> float` | Calculates total market value: Σ (quantity × current price) for all held symbols, using `get_share_price`. |
| **get_profit_loss** | `def get_profit_loss(self, initial_deposit: float) -> float` | Returns `portfolio_value - initial_deposit`. The `initial_deposit` argument mirrors the `initial_balance` at account creation, keeping the API flexible. |
| **list_transactions** | `def list_transactions(self) -> List[Transaction]` | Returns a **copy** of the transaction list ordered chronologically (the list itself is already ordered by insertion). |
| **__repr__** (optional) | `def __repr__(self) -> str` | Human‑readable summary of account state (balance, holdings, transaction count). |

---  

## 4. Internal Helper (Private) Methods  

*These are not part of the public API but are essential to guarantee the invariants required by the specifications.*

| Helper | Purpose |
|--------|---------|
| `_ensure_funds(self, amount: float) -> None` | Raises `ValueError` if `self.balance < amount`. Used by `withdraw`, `buy_share`. |
| `_record_transaction(self, symbol: str, quantity: int, price: float) -> None` | Creates a `Transaction` object (with appropriate sign) and appends it to `self.transactions`. |
| `_update_holdings(self, symbol: str, quantity: int) -> None` | Adjusts the `holdings` dict; adds a new key if necessary, removes the key when quantity reaches zero. |

---  

## 5. External Dependency – `get_share_price(symbol)`  

*The platform supplies this function.*  

- **Signature**: `def get_share_price(symbol: str) -> float`  
- **Behaviour**: Returns the latest market price for the given ticker.  
- **Test implementation (included in the module)**:  

  ```python
  def get_share_price(symbol: str) -> float:
      prices = {
          "AAPL": 150.0,
          "TSLA": 800.0,
          "GOOGL": 2800.0,
      }
      if symbol.upper() not in prices:
          raise KeyError(f"Unsupported symbol: {symbol}")
      return prices[symbol.upper()]
  ```

The design treats `get_share_price` as a **dependency injection point**, making the `Account` class easy to test with a mock implementation.

---  

## 6. Error‑Prevention Rules (enforced by the design)  

1. **Negative balance** – `withdraw` and `buy_share` call `_ensure_funds`; a `ValueError` aborts the operation.  
2. **Over‑buying** – `buy_share` checks `balance >= cost` before any state change.  
3. **Insufficient holdings** – `sell_share` checks `holdings[symbol] >= quantity`.  
4. **Invalid symbols** – `get_share_price` raises `KeyError` for unsupported symbols; `Account` methods propagate this, preventing undefined behaviour.  
5. **Dataclass import safety** – Required fields are listed before any defaulted fields, guaranteeing that the module imports successfully even when the Python interpreter evaluates field defaults.

---  

## 7. Summary  

- **One module** (`accounts.py`) containing the `Transaction` and `Account` dataclasses, plus the `get_share_price` stub.  
- **Field ordering** in both dataclasses complies with the “required‑first” rule.  
- **Public API** (`Account` methods) satisfies every functional requirement: account creation, deposit/withdrawal, share purchase/sale, portfolio valuation, profit/loss calculation, holdings reporting, and transaction listing.  
- **Runtime safety** is built‑in via explicit checks that prevent negative balances, unaffordable purchases, and naked short sales.  

The design is ready for immediate implementation, unit testing, and integration with a simple UI.