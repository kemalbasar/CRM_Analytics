import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter
from lifetimes.plotting import plot_period_transactions

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
pd.set_option('display.float_format', lambda x: '%.9f' % x)


df = pd.read_excel(r"C:\Users\kbbudak\Desktop\Data Scıence Bootcamp\crm_analytics\datasets\online_retail_II.xlsx",
                   sheet_name="Year 2010-2011")


def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    # dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit


percentiles = [0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]

df.describe(percentiles=percentiles)

df.isna().sum()
df.dropna(inplace=True)

df = df[~df["Invoice"].str.contains("C", na=False)]
df = df[df["Quantity"] > 0]
df = df[df["Price"] > 0]
df.describe()


replace_with_thresholds(df, "Price")
replace_with_thresholds(df, "Quantity")


df["TotalPrice"] = df["Quantity"] * df["Price"]



#########################################################################
#########################################################################
#########################################################################



today_date = dt.datetime(2011, 12, 11)

cltv_df = df.groupby("Customer ID").agg({"InvoiceDate": [lambda x: (x.max() - x.min()).days,
                                                         lambda x: (today_date - x.min()).days],
                                         "Invoice": lambda x: x.nunique(),
                                         "TotalPrice": lambda x: x.sum()})

cltv_df.columns.droplevel(0)
# cltv_df.reset_index(inplace = True)

cltv_df.columns = ["recency","T","frequency","monetary"]
cltv_df["monetary"] = cltv_df["monetary"] / cltv_df["frequency"]



cltv_df = cltv_df[cltv_df["frequency"] > 1]
cltv_df["T"] = cltv_df["T"] / 7
cltv_df["recency"] = cltv_df["recency"] / 7

cltv_df.describe().T



#########################################################################
#########################################################################
#########################################################################



bgf = BetaGeoFitter(penalizer_coef = 0.001)
bgf.fit(cltv_df['frequency'],
        cltv_df['recency'],
        cltv_df['T'])
bgf.conditional_expected_number_of_purchases_up_to_time(1,
                                                        cltv_df['frequency'],
                                                        cltv_df['recency'],
                                                        cltv_df['T'])

cltv_df["expected_purc_1_week"].sort_values(ascending = False).head(10)
plot_period_transactions(bgf)
plt.show()



#########################################################################
#########################################################################
#########################################################################


ggf = GammaGammaFitter(penalizer_coef=0.01)
ggf.fit(cltv_df['frequency'],cltv_df['monetary'])
cltv_df["expected_avarage_profit"] = ggf.conditional_expected_average_profit(cltv_df['frequency'],
                                                                         cltv_df['monetary'])

list_of_expected = [col for col in cltv_df.columns if "expected" in col]
cltv_df[list_of_expected].agg("sum")



ggf.customer_lifetime_value(bgf,cltv_df['frequency'],
                                cltv_df['recency'],
                                cltv_df['T'],
                                cltv_df['monetary'],
                                time = 3,
                                freq='W',
                                discount_rate = 0.01)
