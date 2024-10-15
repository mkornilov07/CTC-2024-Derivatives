import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import numpy as np
from scipy.stats import norm

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
    self.options["date"] = pd.to_datetime(self.options["ts_recv"])

    self.underlying = pd.read_csv("data/underlying_data_hour.csv")
    self.underlying.columns = self.underlying.columns.str.lower()
    self.underlying.index = pd.to_datetime(self.underlying.date)
    print(self.underlying.index.duplicated())
    # self.options["underlying_price"] = self.underlying.open[self.options.day.values]
    self.options.insert(1, "underlying_price",self.underlying.open[self.options.reset_index().day.to_numpy()].to_numpy() , allow_duplicates = True)
    self.underlying["volatility"] = self.underlying.open.pct_change().rolling(10, min_periods = 10).std() * np.sqrt(252)
    self.options["time_to_exp_percentage"] = self.time_to_expiration()
    print("Done with time to expiration")
    call, put = self.black_scholes()
    self.options["call"] = call
    self.options["put"] = put
    # self.underlying.drop(columns="date", inplace=True)
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
    S = self.options["underlying_price"][self.options.day>self.start_date+timedelta(days=11)]
    K = self.options["strike_price"][self.options.day>self.start_date+timedelta(days=11)]
    volatility = self.underlying.volatility[self.options[self.options.day>self.start_date+timedelta(days=11)].reset_index().day.to_numpy()].to_numpy()
    print(self.underlying.volatility)
    print(volatility)
    r = 0.03 #  continuously compounded risk-free interest rate (% p.a.), stated as 3%
    q = 0. #  continuously compounded dividend yield (% p.a.), no dividend yield
    t = self.options["time_to_exp_percentage"][self.options.day>self.start_date+timedelta(days=11)].to_numpy()
    print("AAAAAAAAAAAAAAAAA")
    print(S.dtype, K.dtype, volatility.dtype, t.dtype)
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
    put = K * np.exp(-r * t) * norm.cdf(-d2) - S * np.exp(-q * t) * norm.cdf(d1)
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
    return pd.read_csv("data/arbitrage_test_orders.csv")
    # orders = []
    # num_orders = 1000
    
    # for _ in range(num_orders):
    #   row = self.options.sample(n=1).iloc[0]
    #   action = random.choice(["B", "S"])
      
    #   if action == "B":
    #     order_size = random.randint(1, int(row["ask_sz_00"]))
    #   else:
    #     order_size = random.randint(1, int(row["bid_sz_00"]))

    #   assert order_size <= int(row["ask_sz_00"]) or order_size <= int(row["bid_sz_00"])
      
    #   order = {
    #     "datetime" : row["ts_recv"],
    #     "option_symbol" : row["symbol"],
    #     "action" : action,
    #     "order_size" : order_size
    #   }
    #   orders.append(order)
    
    # return pd.DataFrame(orders)