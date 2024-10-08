import random
import pandas as pd
from datetime import datetime

class Strategy:
  
  def __init__(self) -> None:
    self.capital : float = 100_000_000
    self.portfolio_value : float = 0

    self.start_date : datetime = datetime(2024, 1, 1)
    self.end_date : datetime = datetime(2024, 3, 30)
  
    self.options : pd.DataFrame = pd.read_csv("data/cleaned_options_data.csv")
    
    parsed_data = self.options["symbol"].apply(self.parse_symbol)

    parsed_df = pd.DataFrame(parsed_data.tolist())
      
    self.options = pd.concat([self.options, parsed_df], axis=1)
  
    self.options["day"] = self.options["ts_recv"].apply(lambda x: x.split("T")[0])

    self.underlying = pd.read_csv("data/underlying_data_hour.csv")
    self.underlying.columns = self.underlying.columns.str.lower()
  

  def parse_symbol(self, symbol: str) -> dict:
        year = int("20" + symbol[6:8])
        month = int(symbol[8:10])
        day = int(symbol[10:12])
        option_type = symbol[12]
        strike_price = symbol[14:18]

        return {
            "expiration": datetime(year, month, day),
            "option_type": option_type,
            "strike_price": strike_price
        }

  def generate_orders(self) -> pd.DataFrame:
    orders = []
    num_orders = 100
    
    for _ in range(num_orders):
      row = self.options.sample(n=1).iloc[0]
      action = random.choice(["B", "S"])
      
      if action == "B":
        order_size = random.randint(1, int(row["ask_sz_00"]))
      else:
        order_size = random.randint(1, int(row["bid_sz_00"]))

      assert order_size <= int(row["ask_sz_00"]) or order_size <= int(row["bid_sz_00"])
      
      order = {
        "datetime" : row["ts_recv"],
        "option_symbol" : row["symbol"],
        "action" : action,
        "order_size" : order_size
      }
      orders.append(order)
    
    return pd.DataFrame(orders)