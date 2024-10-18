import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import numpy as np
import scipy.stats as si
from scipy.stats import norm

class Utkarsh_Strategy:
  def __init__(self):
        self.capital: float = 100_000_000
        self.portfolio_value: float = 0
        self.start_date: datetime = datetime(2024, 1, 1)
        self.end_date: datetime = datetime(2024, 3, 30)
        self.options: pd.DataFrame = pd.read_csv("data/cleaned_options_data.csv")
        self.options["day"] = self.options["ts_recv"].apply(lambda x: x.split("T")[0])
        self.underlying = pd.read_csv("data/underlying_data_hour.csv")
        self.underlying.columns = self.underlying.columns.str.lower()

  def parse_symbol(self, symbol: str) -> dict:
      numbers: str = symbol.split(" ")[3]
      date: str = numbers[:6]
      date_yymmdd: str = "20" + date[0:2] + "-" + date[2:4] + "-" + date[4:6]
      action: str = numbers[6]
      strike_price: float = float(numbers[7:]) / 1000
      return {
          "expiration": datetime.strptime(date_yymmdd, "%Y-%m-%d"),
          "option_type": action,
          "strike_price": strike_price,
      }

  def black_scholes(self, S, K, T, r, sigma, option_type='C'):
      d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
      d2 = d1 - sigma * np.sqrt(T)

      if option_type == 'C':
          return S * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)
      elif option_type == 'P':
          return K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)

  def get_spot_price(self, date):
      # Calculate spot price for a given date from underlying data
      self.underlying['date'] = pd.to_datetime(self.underlying['date'])
      daily_data = self.underlying[self.underlying['date'].dt.date == pd.to_datetime(date).date()]
      
      if not daily_data.empty:
          return daily_data['close'].iloc[-1]
      else:
          return None

  def calculate_annualized_volatility_until(self, option_date):
      # Calculate annualized volatility up until a given option date
      self.underlying['date'] = pd.to_datetime(self.underlying['date'])
      self.underlying['day'] = self.underlying['date'].dt.date
      filtered_df = self.underlying[self.underlying['date'] < pd.to_datetime(option_date)]
      
      daily_prices = filtered_df.groupby('day')['adj close'].last()
      daily_returns = daily_prices.pct_change().dropna()
      
      # Annualize the volatility by multiplying by the square root of the number of trading days in a year (e.g., 252)
      annualized_volatility = daily_returns.std() * np.sqrt(252)
      
      return annualized_volatility

  def generate_orders(self) -> pd.DataFrame:
      orders = []
      
      # Ensure we have data for at least 5 days before starting trading
      min_trading_day = pd.to_datetime(self.start_date) + timedelta(days=5)

      for row in self.options.itertuples():
          this_day = datetime.strptime(row.day, "%Y-%m-%d")

          if this_day < min_trading_day:
              continue

          # Parse option details from symbol
          parsed_symbol = self.parse_symbol(row.symbol)
          expiration_date = parsed_symbol["expiration"]
          strike_price = parsed_symbol["strike_price"]
          option_type = parsed_symbol["option_type"]

          # Calculate time to expiration in years
          T = (expiration_date - this_day).days / 365.25

          # Get spot price and annualized volatility up to this day
          S = self.get_spot_price(row.day)
          if S is None:
              continue
          sigma = self.calculate_annualized_volatility_until(row.day)
          
          r = 0.03  # Given risk-free rate

          # Calculate theoretical price using Black-Scholes
          theoretical_price = self.black_scholes(S, strike_price, T, r, sigma, option_type)

          # Determine action based on comparison with market prices
          print(theoretical_price, row.ask_px_00)
          if theoretical_price > row.ask_px_00:
              action = "B"
              order_size = 10
              if order_size == 0:
                  continue

              order = {
                  "datetime": row.ts_recv,
                  "option_symbol": row.symbol,
                  "action": action,
                  "order_size": order_size
              }
              orders.append(order)
              print("Order:", order)

      return pd.DataFrame(orders)