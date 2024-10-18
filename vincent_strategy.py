import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import norm
import pandas as pd
from datetime import datetime, timedelta

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
        r = 0.03 #    continuously compounded risk-free interest rate (% p.a.), stated as 3%
        q = 0. #    continuously compounded dividend yield (% p.a.), no dividend yield
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
    def generate_orders(self) -> pd.DataFrame:
        orders = []

        row = self.options.sample(n=1).iloc[0]
        '''
        row data example
        -----------------------------------------------
        ts_recv          2024-03-14T17:56:35.981492593Z
        instrument_id                        1174439511
        bid_px_00                                  12.4
        ask_px_00                                  12.8
        bid_sz_00                                   409
        ask_sz_00                                   318
        symbol                    SPX   240315C05150000
        expiration                  2024-03-15 00:00:00
        option_type                                   C
        strike_price                             5150.0
        day                                  2024-03-14
        '''
        print("vincent v1.0.2")
        max_investment = 5e4
        min_buy_edge = 30
        min_ask_edge = 50
        min_neut_edge = 0
    
        seen = set()
        seen_exps = set()
        most_recent = None
        ct = 0
        p = 0
        for row in self.options.itertuples():
            p += 1
            if p % 65536 == 0:
                 print("iter: ", p) 
                 print(int(row.ask_sz_00), int(row.bid_sz_00))

            # Single-Instrument Strat
            #if not chosen_id:
            #    chosen_id = row.instrument_id
            #if row.instrument_id != chosen_id:
            #    continue
        
            #action = "B"

            date = lambda dateStr: datetime.strptime(dateStr, "%Y-%m-%d")

            if self.parse_symbol(row.symbol)["expiration"] > date("2024-03-30"):
                # option expires past the end date
                continue

            #else:
                # print(self.parse_symbol(row["symbol"]))
                # print(row["day"])
                # print()
            #    pass

            #if row.expiration > date(row.day) + timedelta(days=4):
            #    continue

            #if row.expiration in seen_exps:
            #    continue

            # be willing to make more trades on days where options expire
            # still can't make too many as to not go over 10 min on backtester
            # this_day = date(row.day)
            this_time =  datetime.strptime(row.ts_recv[:-4], "%Y-%m-%dT%H:%M:%S.%f")
            if most_recent is not None and this_time - timedelta(minutes=5) < most_recent:
                continue
            #if this_day in seen_exps and this_time - timedelta(seconds=15) < most_recent:
            #    continue
            most_recent = this_time
            #seen_exps.add(row.expiration)

            #if action == "B":
                #order_size = 1 # random.randint(1, int(row.ask_sz_00))
            #else:
                #order_size = 1 # random.randint(1, int(row.bid_sz_00))

            order_size = min(int(row.ask_sz_00), int(row.bid_sz_00), 100) # don't spend more than 80k on one transaction
            if order_size == 0:
                continue

            
           

            # ACTUAL BLACK SCHOLES STUFF
            buy_edge = -(row.theo - row.ask_px_00) 
            ask_edge = -(row.bid_px_00 - row.theo) 

            action = None
            if buy_edge > min_buy_edge:
                 action = "B"
            elif ask_edge > min_ask_edge:
                 action = "S"
                 
            if buy_edge == float("nan") or ask_edge == float("nan"):
                 continue

            
            
            if action is not None:
                ct += 1
                order = {
                "datetime" : row.ts_recv,
                "option_symbol" : row.symbol,
                "action" : action,
                "order_size" : order_size
                }

                #net_size = order_size * {"B": 1, "S": -1}[action]
                #if row.instrument_id not in exposures:
                #    exposures[row.instrument_id] = net_size
                #else:
                #    exposures[row.instrument_id] += net_size
                
                print("Theo: ", row.theo)
                print("Order:", ct, order)
                print("Buy/Ask edge:", buy_edge, ask_edge)
                orders.append(order)

            '''
            elif row.instrument_id in exposures and exposures[row.instrument_id] > 0 and \
                ask_edge > min_neut_edge:
                ct += 1
                order = {
                "datetime" : row.ts_recv,
                "option_symbol" : row.symbol,
                "action" : "S",
                "order_size" : min(order_size, exposures[row.instrument_id])
                }
                exposures[row.instrument_id] -= min(order_size, exposures[row.instrument_id])
                print("Theo: ", row.theo)
                print("Order:", ct, order)
                orders.append(order)
            elif row.instrument_id in exposures and exposures[row.instrument_id] < 0 and buy_edge > min_neut_edge:
                ct += 1
                order = {
                "datetime" : row.ts_recv,
                "option_symbol" : row.symbol,
                "action" : "S",
                "order_size" : min(order_size, exposures[row.instrument_id])
                }
                exposures[row.instrument_id] += min(order_size, exposures[row.instrument_id])
                print("Theo: ", row.theo)
                print("Order:", ct, order)
                orders.append(order)
            '''
                 
        print("Total order count: ", len(orders))
        return pd.DataFrame(orders)