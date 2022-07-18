import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt


seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potentioal_loyalist',
    r'5[4-5]': 'champions',
}


df = pd.read_csv(r'C:\Users\kbbudak\PycharmProjects\Charting\cltv\data\flo_data_20k.csv')

df.describe()

df["order_num_total"] = df['order_num_total_ever_offline'] + df['order_num_total_ever_online']

df['customer_total_value'] = df['customer_value_total_ever_offline'] + df['customer_value_total_ever_online']

df.groupby("order_channel").agg({"customer_total_value": "sum",
                                 "order_num_total": "sum"})

df["last_order_date"].max()

today = dt.date(2021, 6, 1)

df.loc[:, df.columns.str.contains("date")] = df.loc[:, df.columns.str.contains("date")].apply(
    lambda x: pd.to_datetime(x).dt.date)

df.sort_values(by="customer_total_value")

rfm = df.groupby(["master_id","interested_in_categories_12"]).agg({"last_order_date": lambda x: (today - x.max()).days,
                                   "order_num_total": lambda x: x.sum(),
                                   "customer_total_value": lambda x: x.sum()})

rfm.columns = ["recency", "frequency", "monetary"]

rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm["m_score"] = pd.qcut(rfm["monetary"], 5, labels=[5, 4, 3, 2, 1])
rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1])

rfm["frequency"].hist()

rfm["f_score"].value_counts()

rfm["segment"] = ''

rfm.reset_index(inplace = True)

# for row in rfm.index:
#     if 1 <= rfm["f_score"][row] <= 2 and 1 <= rfm["r_score"][row] <= 2:
#
#         rfm["segment"][row] = seg_map["[1-2][1-2]"]
#
#     elif 1 <= rfm["f_score"][row] <= 2 and 3 <= rfm["r_score"][row] <= 4:
#
#         rfm["segment"][row] = seg_map["[1-2][3-4]"]
#
#     elif 1 <= rfm["f_score"][row] <= 2 and 1 <= rfm["r_score"][row] == 5:
#
#         rfm["segment"][row] = seg_map["[1-2]5"]
#
#     elif rfm["f_score"][row] == 3 and 1 <= rfm["r_score"][row] <= 2:
#
#         rfm["segment"][row] = seg_map["3[1-2]"]
#
#     elif rfm["f_score"][row] == 3 and rfm["f_score"][row] == 3:
#
#         rfm["segment"][row] = seg_map["33"]
#
#     elif 3 <= rfm["f_score"][row] <= 4 and 4 <= rfm["f_score"][row] <= 5:
#
#         rfm["segment"][row] = seg_map["[3-4][4-5]"]
#
#     elif rfm["f_score"][row] == 4 and rfm["f_score"][row] == 1:
#
#         rfm["segment"][row] = seg_map["41"]
#
#     elif rfm["f_score"][row] == 5 and rfm["f_score"][row] == 1:
#
#         rfm["segment"][row] = seg_map["51"]
#
#     elif 4 <= rfm["f_score"][row] <= 5 and 2 <= rfm["f_score"][row] <= 3:
#
#         rfm["segment"][row] = seg_map["[4-5][2-3]"]
#
#     else:
#
#         rfm["segment"][row] = seg_map['5[4-5]']


seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potentioal_loyalist',
    r'5[4-5]': 'champions',
}


rfm_loyals = rfm.loc[((rfm["segment"] == 'champions')  |  (rfm["segment"] =='loyal_customers'))]

target_customers = pd.DataFrame([rfm_loyals["master_id"][row] for row in rfm_loyals.index if "KADIN" in rfm_loyals["interested_in_categories_12"][row]])

target_customers.to_csv(r'C:\Users\kbbudak\PycharmProjects\Charting\cltv\xlsheets\royal_women.csv')