import unittest
from datetime import datetime
from accounts import Transaction, Account, get_share_price

class TestAccounts(unittest.TestCase):

    def test_transaction_creation(self):
        txn = Transaction(symbol="AAPL", quantity=10, price=150.0)
        self.assertEqual(txn.symbol, "AAPL")
        self.assertEqual(txn.quantity, 10)
        self.assertEqual(txn.price, 150.0)
        self.assertIsInstance(txn.timestamp, datetime)

    def test_account_initial_balance_validation(self):
        with self.assertRaises(ValueError):
            Account(user_id="u1", initial_balance=-5.0)

    def test_deposit_and_withdraw(self):
        acc = Account(user_id="u1", initial_balance=100.0)
        acc.deposit(50.0)
        self.assertEqual(acc.balance, 150.0)
        self.assertEqual(len(acc.transactions), 1)
        txn = acc.transactions[0]
        self.assertEqual(txn.symbol, "CASH")
        self.assertEqual(txn.quantity, -1)
        self.assertEqual(txn.price, 50.0)

        acc.withdraw(30.0)
        self.assertEqual(acc.balance, 120.0)
        self.assertEqual(len(acc.transactions), 2)
        txn2 = acc.transactions[-1]
        self.assertEqual(txn2.symbol, "CASH")
        self.assertEqual(txn2.quantity, 1)
        self.assertEqual(txn2.price, 30.0)

    def test_deposit_negative_amount(self):
        acc = Account(user_id="u1", initial_balance=100.0)
        with self.assertRaises(ValueError):
            acc.deposit(-10.0)

    def test_withdraw_insufficient_funds(self):
        acc = Account(user_id="u1", initial_balance=20.0)
        with self.assertRaises(ValueError):
            acc.withdraw(30.0)

    def test_buy_share_success(self):
        acc = Account(user_id="u1", initial_balance=1000.0)
        acc.buy_share("AAPL", 5)  # price 150.0 => cost 750
        self.assertEqual(acc.balance, 250.0)
        self.assertEqual(acc.holdings.get("AAPL", 0), 5)
        self.assertEqual(len(acc.transactions), 1)
        txn = acc.transactions[0]
        self.assertEqual(txn.symbol, "AAPL")
        self.assertEqual(txn.quantity, -5)
        self.assertEqual(txn.price, 150.0)

    def test_buy_share_insufficient_funds(self):
        acc = Account(user_id="u1", initial_balance=100.0)
        with self.assertRaises(ValueError):
            acc.buy_share("TSLA", 1)  # price 800

    def test_sell_share_success(self):
        acc = Account(user_id="u1", initial_balance=6000.0)
        acc.buy_share("GOOGL", 2)  # cost 5600, balance 400
        acc.sell_share("GOOGL", 1)  # proceeds 2800, balance 3200
        self.assertEqual(acc.balance, 3200.0)
        self.assertEqual(acc.holdings.get("GOOGL", 0), 1)

    def test_sell_insufficient_shares(self):
        acc = Account(user_id="u1", initial_balance=1000.0)
        acc.buy_share("AAPL", 5)  # holds 5
        with self.assertRaises(ValueError):
            acc.sell_share("AAPL", 6)

    def test_invalid_symbol(self):
        with self.assertRaises(KeyError):
            get_share_price("XYZ")

    def test_portfolio_value(self):
        acc = Account(user_id="u1", initial_balance=0.0)
        acc.buy_share("AAPL", 1)  # 150
        acc.buy_share("TSLA", 2)  # 1600
        value = acc.get_portfolio_value()
        self.assertAlmostEqual(value, 150 + 1600)

    def test_profit_loss(self):
        initial = 1000.0
        acc = Account(user_id="u1", initial_balance=initial)
        acc.buy_share("AAPL", 1)  # cost 150, balance 850
        acc.sell_share("AAPL", 1)  # proceeds 150, balance 1000
        self.assertEqual(acc.get_profit_loss(initial), 0.0)

    def test_list_transactions_copy(self):
        acc = Account(user_id="u1", initial_balance=0.0)
        acc.deposit(100)
        acc.withdraw(20)
        transactions = acc.list_transactions()
        self.assertEqual(len(transactions), 2)
        # ensure it's a copy: modifying original should not affect copy
        acc.transactions.append(Transaction("CASH", 0, 0.0))
        self.assertEqual(len(acc.transactions), 3)
        self.assertEqual(len(transactions), 2)

    def test_holdings_update(self):
        acc = Account(user_id="u1", initial_balance=0.0)
        acc.buy_share("MSFT", 3)  # holdings 3
        self.assertEqual(acc.holdings.get("MSFT", 0), 3)
        acc.sell_share("MSFT", 1)  # holdings 2
        self.assertEqual(acc.holdings.get("MSFT", 0), 2)
        acc.sell_share("MSFT", 2)  # holdings 0 -> key removed
        self.assertNotIn("MSFT", acc.holdings)
        # selling more than held should raise
        with self.assertRaises(ValueError):
            acc.sell_share("MSFT", 1)

if __name__ == "__main__":
    unittest.main()