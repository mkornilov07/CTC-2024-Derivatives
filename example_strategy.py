import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import numpy as np
from scipy.stats import norm

class Strategy:
  DAYS_TO_SKIP = 10
  def __init__(self, start_date, end_date, options_data = "data/cleaned_options_data.csv", underlying = "data/underlying_data_hour.csv") -> None:
    self.capital : float = 100_000_000
    self.portfolio_value : float = 0

    self.start_date : datetime = start_date
    self.end_date : datetime = end_date
    self.start_date : datetime = start_date
    self.end_date : datetime = end_date
  
    self.options : pd.DataFrame = pd.read_csv(options_data)
    
    parsed_data = self.options["symbol"].apply(self.parse_symbol)

    parsed_df = pd.DataFrame(parsed_data.tolist())
    
    self.options = pd.concat([self.options, parsed_df], axis=1)
  
    self.options["day"] = pd.to_datetime(self.options["ts_recv"].apply(lambda x: x.split("T")[0]))
    print(f"options.day is {self.options.day.dtype}")
    
    self.options["date"] = pd.to_datetime(self.options["ts_recv"])
    self.underlying = pd.read_csv(underlying)
    self.underlying.index = pd.to_datetime(self.underlying["date"].str.slice(stop=-6))
    self.underlying.columns = self.underlying.columns.str.lower()
    self.underlying_price_daily = self.underlying.open.resample("B").mean()
    self.options = self.options.merge(self.underlying_price_daily, left_on = "day", right_index = True)
    self.options.rename(columns = {"open" : "underlying_price"}, inplace=True)

    self.vol_daily = np.log(self.underlying_price_daily.pct_change()+1).rolling(self.DAYS_TO_SKIP, min_periods = self.DAYS_TO_SKIP).std() * np.sqrt(252)
    self.options["time_to_exp_percentage"] = self.time_to_expiration()
    print("Done with time to expiration")
    call, put = self.black_scholes()
    self.options["call"] = call
    self.options["put"] = put
    self.options["theo"] = self.options.call.where(self.options.option_type == "C", self.options.put)
    self.underlying.drop(columns="date", inplace=True)
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
  def black_scholes(self) -> float:
    S = self.options["underlying_price"][self.options.day>self.start_date+timedelta(days=self.DAYS_TO_SKIP+2)]
    K = self.options["strike_price"][self.options.day>self.start_date+timedelta(days=self.DAYS_TO_SKIP+2)]
    volatility = self.vol_daily[self.options[self.options.day>self.start_date+timedelta(days=self.DAYS_TO_SKIP+2)].reset_index().day.to_numpy()].to_numpy()
    print(volatility)
    r = 0.03 #  continuously compounded risk-free interest rate (% p.a.), stated as 3%
    q = 0. #  continuously compounded dividend yield (% p.a.), no dividend yield
    t = self.options["time_to_exp_percentage"][self.options.day>self.start_date+timedelta(days=self.DAYS_TO_SKIP+2)].to_numpy()
    # print("AAAAAAAAAAAAAAAAA")
    # print(S.dtype, K.dtype, volatility.dtype, t.dtype)
    # S,K,volatility,t = S[10000:], K[10000:], volatility[10000:], t[10000:]
    a=(np.log(S) - np.log(K))
    b=(r - q + np.square(volatility) * 0.5)
    print(volatility)
    print(t)
    d=volatility * np.sqrt(t)
    c=np.reciprocal(d)
    d1 = (a + t * b) * c
    d2 = d1 - volatility * np.sqrt(t)
    print("BBBBBBBBBBBBBBBBBB")
    call = S * np.exp(-q * t) * norm.cdf(d1) - K * np.exp(-r * t) * norm.cdf(d2)
    put = K * np.exp(-r * t) * norm.cdf(-d2) - S * np.exp(-q * t) * norm.cdf(-d1)
    return call, put

  def time_to_expiration(self) -> float:
        expiration = self.options["expiration"]
        current = self.options.day

        return (expiration - current).dt.days / 365.25
  def getOptions(self):
    return self.options
  
  def getUnderlying(self):
    return self.underlying
  def generate_orders(self) -> pd.DataFrame:
    orders = []
    num_orders = 200
    num_orders = 200
    
    for _ in range(num_orders):
      row = self.options.sample(n=1).iloc[0]
      action = random.choice(["B", "S"])
      
      if action == "B":
        if int(row["ask_sz_00"]) > 1:
          order_size = random.randint(1, int(row["ask_sz_00"]))
        if int(row["ask_sz_00"]) > 1:
          order_size = random.randint(1, int(row["ask_sz_00"]))
      else:
        if int(row["bid_sz_00"]) > 1:
          order_size = random.randint(1, int(row["bid_sz_00"]))
        if int(row["bid_sz_00"]) > 1:
          order_size = random.randint(1, int(row["bid_sz_00"]))
      
      order = {
        "datetime" : row["ts_recv"],
        "option_symbol" : row["symbol"],
        "action" : action,
        "order_size" : order_size
      }
      orders.append(order)
    
    return pd.DataFrame(orders)