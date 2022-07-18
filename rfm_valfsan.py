import datetime as dt
import pandas as pd
from currency_converter import CurrencyConverter

c = CurrencyConverter(fallback_on_missing_rate=True)

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

df = pd.read_excel(r"C:\Users\kbbudak\PycharmProjects\cltv\data\VALFSAN_YURTDIŞI.xlsx")

# Dataframe i yedekliyoruz.
df_backup = df.copy()
# İhtiyacımız olmayan kolonu drop ettik.
df.drop("Durum", axis=1, inplace=True)

# Şirket ismi VALFSAN olanlar satış değil bu yüzden o verilerden kurtuluyoruz.
df = df[~(df["İsim-1"] == "VALFSAN DIS TIC. LTD.")]
# Kayıt tipi alış iade olan verilerdende kurtulalım.
df = df[~(df["Kayıt Tipi"] == "Alış İade")]

# İptal edilmiş faturaları veri setinden çıkartıyoruz.
df = df[df["İptal"] == 0]

# Betimsel istatistik özeti
df.isna().sum()
percentiles = [0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
df.describe(percentiles=percentiles)

# Müşteri isimlerini ayrı bir dataframe de tutalım.
df_names = df.groupby(["Müşteri", "İsim-1"]).agg({"İsim-1": 'count'})
df_names.columns = ["adet"]
df_names.reset_index(inplace=True)
df_names = df_names.groupby("Müşteri").agg({"İsim-1": "first"})

#
# # np_names = np.array(df_names["Müşteri"])
#
# #bunu soracağız (isimleri tekilleştirmeye  çalışıyorum)
# names = [df_names[df_names["Müşteri"] == df.iloc[row]["Müşteri"]][["İsim-1"]].values for row in range(len(df))]


# Currency Converter kütüphanesini kullanarak tutarların hepsini USD ye çevireceğiz, bunun için para birimi 'TL' olanları , kütüphanede kullanılan kod
# olan 'TRY' olarak düzenleyelim.
df['Bel. Pr. Br.'] = df['Bel. Pr. Br.'].apply(lambda x: 'TRY' if x == 'TL' else x)
# çıkarılan verilerden sonra indexin bozulan ardışıklığını düzeltelim.
df.index = range(7889)
# currency convert işini doğru yapmış mı kontrol etmek için yedek alıyoruz.
df_backup = df.copy()

# Kütüphane de Temmuz ayı currency verileri  bulunamadığı için , verileri kontrol ediyoruz, if else yapısında manuel convert edeceğiz.
df[df['Bel. Tarihi'] > '2022-06-27']['Bel. Pr. Br.'].value_counts()

# currency_converter kütüphanesini kullanarak tek satırda gerekli dönüşümleri yapıyoruz.
for row in range(len(df)):
    if df['Bel. Tarihi'][row] < dt.date(2022, 6, 27):
        df["Bel. Toplamı"][row] = c.convert(df["Bel. Toplamı"][row], df['Bel. Pr. Br.'][row], 'EUR',
                                            date=df['Bel. Tarihi'][row])
    else:
        if df['Bel. Pr. Br.'][row] == 'GBP':
            df["Bel. Toplamı"][row] = df["Bel. Toplamı"][row] * 0.84
        elif df['Bel. Pr. Br.'][row] == 'USD':
            df["Bel. Toplamı"][row] = df["Bel. Toplamı"][row] * 1.01

# currency converter işini doğru yapmış mı kontrol etmek için para birimi TRY olanların çıktılarını kontrol edelim.
df_backup[df_backup['Bel. Pr. Br.'] == 'TRY']
df[df['Bel. Pr. Br.'] == 'TRY']

# RFM analizi yapmaya başlayabiliriz recency,frekans  ve monetary metriklerini  her bir müşteri için bulalım.

df['Bel. Tarihi'].max()
today = dt.date(2022, 7, 9)

rfm_valfsan = df.groupby("Müşteri").agg({'Bel. Tarihi': lambda x: (today - x.max().to_pydatetime().date()).days,
                                         'E-Belge No': "count",
                                         'Bel. Toplamı': "sum",
                                         })

rfm_valfsan.columns = ["recency", "frequency", "monetary"]

rfm_valfsan["frequency_score"] = pd.qcut(rfm_valfsan['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm_valfsan["recency_score"] = pd.qcut(rfm_valfsan['recency'], 5, labels=[5, 4, 3, 2, 1])
rfm_valfsan["monetary_score"] = pd.qcut(rfm_valfsan['monetary'], 5, labels=[1, 2, 3, 4, 5])

rfm_valfsan["RF_SCORE"] = (rfm_valfsan['recency_score'].astype(str) + rfm_valfsan['frequency_score'].astype(str))

rfm_valfsan["RFM_SCORE"] = (
            rfm_valfsan['recency_score'].astype(str) + rfm_valfsan['frequency_score'].astype(str) + rfm_valfsan[
        'monetary_score'].astype(str))

seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

rfm_valfsan['segment'] = rfm_valfsan['RF_SCORE'].replace(seg_map, regex=True)

rfm_valfsan.head()

rfm_valfsan = pd.merge(rfm_valfsan, df_names, how='left', on='Müşteri')

# Şampiyonları ve kaybetmek üzere olduğumu müşterilere bakalım.
rfm_valfsan[rfm_valfsan["segment"] == "champions"]
rfm_valfsan[rfm_valfsan["segment"] == "about_to_sleep"]
rfm_valfsan[rfm_valfsan["segment"] == "potential_loyalists"]

# Segmentlere göre genel özete bakalım.
rfm_valfsan.groupby("segment").agg({"monetary": "mean",
                                    "frequency": "mean",
                                    "recency": "mean"})
