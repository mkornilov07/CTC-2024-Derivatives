import random
import pandas as pd
from datetime import datetime, timedelta

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
        print("vincent v0.0.93")
    
        # chosen_id = None
        seen_exps = set()
        most_recent = None
        ct = 0
        for row in self.options.itertuples():
            #if not chosen_id:
            #    chosen_id = row.instrument_id
            #if row.instrument_id != chosen_id:
            #    continue
        
            #action = "B"

            date = lambda dateStr: datetime.strptime(dateStr, "%Y-%m-%d")

            if self.parse_symbol(row.symbol)["expiration"] > date("2024-03-30"):
                # option expires past the end date
                continue
            seen_exps.add(self.parse_symbol(row.symbol)["expiration"])
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
            this_day = date(row.day)
            this_time =  datetime.strptime(row.ts_recv[:-4], "%Y-%m-%dT%H:%M:%S.%f")
            if this_day not in seen_exps and most_recent is not None and this_time - timedelta(minutes=60) < most_recent:
                continue
            ct += 1
            if this_day in seen_exps and this_time - timedelta(seconds=15) < most_recent:
                continue
            most_recent = this_time
            #seen_exps.add(row.expiration)

            #if action == "B":
                #order_size = 1 # random.randint(1, int(row.ask_sz_00))
            #else:
                #order_size = 1 # random.randint(1, int(row.bid_sz_00))

            order_size = min(int(row.ask_sz_00), int(2500/row.ask_px_00)) # don't spend more than 250k on one transaction
            if order_size == 0:
                continue
            print(int(row.ask_sz_00), int(row.bid_sz_00), order_size)
            
            order = {
                "datetime" : row.ts_recv,
                "option_symbol" : row.symbol,
                "action" : "B",
                "order_size" : order_size
            }
            orders.append(order)
            #print("  Row:", row)
            print("Order:", order)
        
        return pd.DataFrame(orders)