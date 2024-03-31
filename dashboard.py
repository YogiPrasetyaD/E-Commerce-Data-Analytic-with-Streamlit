import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import calendar
sns.set(style='dark')

#Membuat Helper Function
def create_category_df(df):
    by_category_df = df.groupby(by=["product_category_name", "customer_city"]).agg({
        "order_id" : "nunique",
        "order_item_id" : "sum",
        "price" : "sum",
    }).sort_values(by="order_item_id", ascending=False)

    by_category_df.rename(columns={
        "order_id" : "Order Count",
        "order_item_id" : "Item",
        "price" : "Total Price",
    },inplace=True)
    
    return by_category_df

def create_customer_df(df):
    by_customer_df = df.groupby(by=["customer_city"]).agg({
        "order_id" : "nunique",
        "order_item_id" : "sum",
        "price" : "sum",
    }).sort_values(by="order_item_id", ascending=False)

    by_customer_df.rename(columns={
        "order_id" : "Order Count",
        "order_item_id" : "Item",
        "price" : "Total Price",
    },inplace=True)
    
    return by_customer_df

def all_order(df):
    all_order_df= df.groupby(by="product_category_name").order_item_id.sum().sort_values(ascending=False).reset_index()
    
    return all_order_df;

def order_month_year(df):
    # Ekstrak tahun dari kolom order_purchase_timestamp
    df['Year'] = df['order_purchase_timestamp'].dt.year
    df['Month'] = df['order_purchase_timestamp'].dt.month

    # Pengelompokkan data berdasarkan tahun dan bulan dan hitung total order item untuk setiap bulan dan tahun
    monthly_order_items = df.groupby(['Year','Month'])['order_item_id'].sum().reset_index()
    
    return monthly_order_items

def revenue_month_year(df):
    # Ekstrak tahun dan bulan dari kolom order_purchase_timestamp
    df['Year'] = df['order_purchase_timestamp'].dt.year
    df['Month'] = df['order_purchase_timestamp'].dt.month

    # Pengelompokkan data berdasarkan bulan dan tahun dan hitung total pendapatan penjualan untuk setiap bulan dan tahun
    monthly_revenue = df.groupby(['Year', 'Month'])['price'].sum().reset_index()
    
    return monthly_revenue

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp" : "max",
        "order_id" : "nunique",
        "price" : "sum"
    })

    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date-x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df

all_df = pd.read_csv("all_data.csv")

datetime_columns = ["order_purchase_timestamp"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image("logo.png")
    
    start_date,end_date = st.date_input(
        label = "Rentang Waktu",
        max_value = max_date, min_value = min_date, value=[min_date,max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"]>= str(start_date))&
                 (all_df["order_purchase_timestamp"]<= str(end_date))]

category_df = create_category_df(main_df)
customer_df = create_customer_df(main_df)
order_df= all_order(main_df)
month_df = order_month_year(main_df)
revenue_df = revenue_month_year(main_df)
rfm_df = create_rfm_df(main_df)

st.header("Public City E-Commerce")

st.subheader('Monthly Orders')
 
col1, col2 = st.columns(2)
monthly_order_items = month_df
 
with col1:
    total_orders = monthly_order_items['order_item_id'].sum()
    st.metric("Total orders", value=total_orders)
 
monthly_revenue = revenue_df
with col2:
    total_revenue = format_currency(monthly_revenue['price'].sum(), "USD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)
 
fig = plt.figure(figsize=(12, 6))
sns.lineplot(data=monthly_order_items, x='Month', y='order_item_id', hue='Year', marker='o')
plt.title('Tren Penjualan Barang')
plt.xlabel('Bulan')
plt.ylabel('Jumlah Order Item')
plt.xticks(range(1, 13), calendar.month_name[1:13], rotation=45)
plt.legend(title='Year')
plt.grid(True)
plt.tight_layout()
plt.show()

st.pyplot(fig)


st.subheader('Total Revenue')

fig=plt.figure(figsize=(12, 6))
sns.lineplot(data=monthly_revenue, x='Month', y='price', hue='Year', marker='o')
plt.title('Tren Pendapatan Bulanan')
plt.xlabel('Bulan')
plt.ylabel('Revenue')
plt.xticks(range(1, 13), calendar.month_name[1:13], rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()

st.pyplot(fig)

st.subheader("Best & Worst Performing Product")
col1, col2 = st.columns(2)
all_order_df = order_df
 
with col1:
    best_product = all_order_df.head(1)
    best_product_name = best_product.iloc[0]["product_category_name"]
    st.metric("Best Product", value=best_product_name)

with col2:
    worst_product = all_order_df.tail(1)
    worst_product_name = worst_product.iloc[0]["product_category_name"]
    st.metric("Worst Product", value=worst_product_name)
 
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

fig,ax = plt.subplots(nrows = 1, ncols=2, figsize=(24,6))
sns.barplot(x="order_item_id", y="product_category_name", data=order_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel("")
ax[0].set_xlabel("")
ax[0].set_title("Best Performing Product", loc="center", fontsize=24)
ax[0].tick_params(axis ='y', labelsize=12)

sns.barplot(x="order_item_id", y="product_category_name", data=order_df.sort_values(by="order_item_id",ascending=True).head(5),palette=colors, ax=ax[1])
ax[1].set_ylabel("")
ax[1].set_xlabel("")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=24)
ax[1].tick_params(axis ='y', labelsize=12)
st.pyplot(fig)

st.subheader("Most Product Sold in A City")
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(24, 10))

color = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]

# Menambahkan informasi kota ke dalam label sumbu-y
sns.barplot(x="Item", y="product_category_name", hue="customer_city", data=category_df.head(5), palette=color, dodge=False)
ax.set_ylabel("Product Category - Customer City", fontsize=12)  # Mengubah label sumbu-y
ax.set_xlabel("Number of Items", fontsize=12)
ax.set_title("Best Product Category Sold by City", loc="center", fontsize=15)
ax.tick_params(axis='y', labelsize=12)
ax.legend(title="City", loc="upper right", bbox_to_anchor=(1.1, 1))  # Menambahkan legenda
plt.tight_layout()  # Memastikan tata letak plot yang baik
plt.show()

st.pyplot(fig)

st.subheader("Most Order Item By City")
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(24, 12))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
# Menampilkan 5 kota dengan jumlah item terbanyak
sns.barplot(x="Item", y="customer_city", data=customer_df.head(5), palette=colors)
ax.set_ylabel("Customer City", fontsize=12)  # Mengubah label sumbu-y
ax.set_xlabel("Number of Items", fontsize=12)
ax.set_title("Most Order in a City", loc="center", fontsize=15)
ax.tick_params(axis='y', labelsize=12)
plt.tight_layout()  # Memastikan tata letak plot yang baik
plt.show()

st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=False).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Customer ID", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=25, rotation=45)  # Rotasi label sumbu x

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Customer ID", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=25, rotation=45)  # Rotasi label sumbu x

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("Customer ID", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=25, rotation=45)  # Rotasi label sumbu x

st.pyplot(fig)