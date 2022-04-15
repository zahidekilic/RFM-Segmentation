###############################################################
# 1. Understanding Data
###############################################################

import datetime as dt
import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.float_format", lambda x: '%.3f' % x)

df = pd.read_excel("online_retail_I.xlsx")
df.head()

# When we look at the data from here, we see that there is multiplexing in Invoice. Because each invoice contains more than one product.
# Quantity shows how many of the product is bought, Price value shows the unit price of the product. In this case, we have to do Quantity * Price to find out how much was paid for the product in total.
# Similarly, to find out the amount of each invoice, we need to group by invoice and add up the prices we just found.

df.shape
df.isnull().sum()
# We will delete the missing values here, because if I don't know the customer's number, I can't do marketing work for her/him, so it is better to delete it.

df["Description"].nunique()

df["Description"].value_counts().head()

# Most ordered product
df.groupby("Description").agg({"Quantity": "sum"}).head() #negative values are on the output, there is a problem...
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head()

# Unique invoice count
df["Invoice"].nunique()

df["TotalPrice"] = df["Quantity"] * df["Price"]
df.groupby("Invoice").agg({"TotalPrice": "sum"}).head()

#################################################
# 2. Data Preparation
#################################################
df.shape
df.dropna(inplace= True) # delete nan values
df.shape

# Aborted operation if it starts with C. Delete all of them
df = df[~df["Invoice"].str.contains("C", na=False)] 
df.describe().T # check the dataframe


###############################################################
# 3. Calculating RFM Metrics
###############################################################
# Recency : Analyzing date - The date of the customer's last purchase
# Frequency : Total purchases made by the customer
# Monetary : The total monetary value left by the customer as a result of the total purchases made

df.head()

# we will define the day of analysis, however, it would not be correct to give today's date since we performed this analysis in years after the years in the dataset (2009-2010).
# so we will determine the analysis date according to the last purchasing made
df["InvoiceDate"].max() #For example, the last shopping date was 2010-01-18. We determine our analysis date by putting 2 days on top of this date.
today_date = dt.datetime(2010,1,18)
type(today_date)

rfm = df.groupby("Customer ID").agg({"InvoiceDate": lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
                                     "Invoice": lambda Invoice: Invoice.nunique(),
                                     "TotalPrice": lambda TotalPrice: TotalPrice.sum()})
rfm.head()
rfm.columns = ["recency", "frequency", "monetary"]

rfm.describe().T #it is seen that some monetary values are 0. We will delete those records as these will not be of use to us.
rfm = rfm[rfm["monetary"]> 0]
rfm.describe().T

###############################################################
# 4. Calculating RFM Scores
###############################################################

rfm["recency_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1])
rfm["monetary_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5])
rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm.head()

rfm["RFM_SCORE"] = rfm["recency_score"].astype(str) + rfm["frequency_score"].astype(str)

rfm.describe().T

# champions...
rfm[rfm["RFM_SCORE"] == "55"]
# hibernatings...
rfm[rfm["RFM_SCORE"] == "11"]

###############################################################
# 5. Creating & Analysing RFM Segments
###############################################################


# Regex for RFM Segments
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
#creating segments
rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)

rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])

#list of customers that are in "need_attention" segment
rfm[rfm["segment"] == "need_attention"].head()
rfm[rfm["segment"] == "need_attention"].index

new_df = pd.DataFrame()
new_df["new_customer_id"] = rfm[rfm["segment"] == "new_customers"].index


new_df["new_customer_id"] = new_df["new_customer_id"].astype(int)

# export to CSV
new_df.to_csv("new_customers.csv")


