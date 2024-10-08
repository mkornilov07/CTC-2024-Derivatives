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
  
    self.options["day"] = pd.to_datetime(self.options["ts_recv"].apply(lambda x: x.split("T")[0]))
    self.options["ts_recv"] = pd.to_datetime(self.options["ts_recv"])

    self.underlying = pd.read_csv("data/underlying_data_hour.csv")
    self.underlying.columns = self.underlying.columns.str.lower()
    self.underlying.date = pd.to_datetime(self.underlying.date)

  def parse_symbol(self, symbol: str) -> dict:
    numbers : str = symbol.split(" ")[3]
    date : str = numbers[:6]
    date_yymmdd : str = "20" + date[0:2] + "-" + date[2:4] + "-" + date[4:6]
    action : str = numbers[6]
    strike_price : float = float(numbers[7:]) / 1000
    return {
        "expiration": datetime.strptime(date_yymmdd, "%Y-%m-%d"),
        "option_type": action,
        "strike_price": strike_price,
    }
  def getOptions(self):
    return self.options
  def getUnderlying(self):
    return self.underlying
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