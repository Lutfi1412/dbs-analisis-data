import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static


def load_data():
    dataframes = {
        # "Customers": pd.read_csv("../data/customers_dataset.csv"),
        # "Geolocation": pd.read_csv("../data/geolocation_dataset.csv"),
        # "Order Items": pd.read_csv("../data/order_items_dataset.csv"),
        # "Order Payments": pd.read_csv("../data/order_payments_dataset.csv"),
        # "Order Reviews": pd.read_csv("../data/order_reviews_dataset.csv"),
        # "Orders": pd.read_csv("../data/orders_dataset.csv"),
        # "Product Category": pd.read_csv("../data/product_category_name_translation.csv"),
        # "Products": pd.read_csv("../data/products_dataset.csv"),
        # "Sellers": pd.read_csv("../data/sellers_dataset.csv"),

        "Customers": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/customers_dataset.csv"),
        "Geolocation": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/geolocation_dataset.csv"),
        "Order Items": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/order_items_dataset.csv"),
        "Order Payments": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/order_payments_dataset.csv"),
        "Order Reviews": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/order_reviews_dataset.csv"),
        "Orders": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/orders_dataset.csv"),
        "Product Category": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/product_category_name_translation.csv"),
        "Products": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/products_dataset.csv"),
        "Sellers": pd.read_csv("https://raw.githubusercontent.com/Lutfi1412/dbs-analisis-data/refs/heads/main/data/sellers_dataset.csv"),
    }
    return dataframes

def clean_data(dataframes):
    cleaned_dataframes = {}
    
    for name, df in dataframes.items():
        df = df.copy()

        
        df.drop_duplicates(inplace=True)

        
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                if df[col].dtype == "object":
                    df.dropna(subset=[col], inplace=True)  
                else:
                    df[col].fillna(df[col].mean(), inplace=True)  

        
        for col in df.select_dtypes(include=np.number).columns:
            data = df[col].dropna()  
            if len(data) > 0:
                q25, q75 = np.percentile(data, 25), np.percentile(data, 75)
                iqr = q75 - q25
                cut_off = iqr * 1.5  
                minimum, maximum = q25 - cut_off, q75 + cut_off
                df[col] = df[col].mask((df[col] < minimum) | (df[col] > maximum), maximum)  

        
        cleaned_dataframes[name] = df
        
    return cleaned_dataframes


def get_state_review_analysis(cleaned_dataframes):
    if not cleaned_dataframes:
        return None, None
    
    # Menggabungkan Customers dan Orders
    all_df = pd.merge(
        left=cleaned_dataframes["Customers"],
        right=cleaned_dataframes["Orders"],
        how="inner",
        left_on="customer_id",
        right_on="customer_id"
    )

    # Menggabungkan dengan Order Reviews
    rating_state = pd.merge(
        left=all_df,
        right=cleaned_dataframes["Order Reviews"],
        how="inner",
        left_on="order_id",
        right_on="order_id"
    )

    state_review_analysis = rating_state.groupby("customer_state")["review_score"].mean().reset_index()
    state_review_analysis = state_review_analysis.sort_values(by="review_score", ascending=False)

    return state_review_analysis, rating_state

def get_top_product_per_state(cleaned_dataframes):
    if not cleaned_dataframes:
        return None
    
    all_df = pd.merge(
        left=cleaned_dataframes["Customers"],
        right=cleaned_dataframes["Orders"],
        how="inner",
        left_on="customer_id",
        right_on="customer_id"
    )

    # Menggabungkan dengan Order Reviews
    rating_state = pd.merge(
        left=all_df,
        right=cleaned_dataframes["Order Reviews"],
        how="inner",
        left_on="order_id",
        right_on="order_id"
    )

    products_state = pd.merge(
    left=rating_state,
    right=cleaned_dataframes["Order Items"],
    how="inner",
    left_on="order_id",
    right_on="order_id"
    )

    products_state = pd.merge(
        left=products_state,
        right=cleaned_dataframes["Products"],
        how="inner",
        left_on="product_id",
        right_on="product_id"
    )

    # Analisis produk terbanyak dibeli per negara
    state_products_analysis = products_state.groupby(["customer_state", "product_category_name"]).size().reset_index(name="total_purchases")
    top_product_per_state = state_products_analysis.loc[state_products_analysis.groupby("customer_state")["total_purchases"].idxmax()]

    return top_product_per_state

def display_ratings(state_review_analysis, rating_state):
    st.sidebar.header("Filter Data")
    selected_country = st.sidebar.selectbox(
        "Pilih Negara", 
        options=state_review_analysis["customer_state"].unique(),
        index=None,
        placeholder="Pilih negara..."
    )

    if selected_country:
        country_data = rating_state[rating_state["customer_state"] == selected_country]
        rating_counts = country_data["review_score"].value_counts().sort_index()

        # Buat bar chart
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(rating_counts.index, rating_counts.values, color="skyblue")

        ax.set_xlabel("Rating")
        ax.set_ylabel("Jumlah")
        ax.set_title(f"Distribusi Rating di Negara {selected_country}")
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        st.pyplot(fig)

        # Menampilkan teks deskripsi rating
        rating_text = ", ".join([f"rating {rating} dengan jumlah {jumlah}" for rating, jumlah in rating_counts.items()])
        
        st.write(f"Pada negara {selected_country} memiliki {rating_text}.")



    else:
        # Tampilan default: rata-rata rating per negara
        st.title("Rata-rata Rating per Negara")
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.bar(
            state_review_analysis["customer_state"], 
            state_review_analysis["review_score"], 
            color='skyblue'
        )

        ax.set_xlabel("Negara")
        ax.set_ylabel("Rata-rata Review Score")
        ax.set_title("Rata-rata Review Score di Setiap Negara")
        ax.set_xticklabels(state_review_analysis["customer_state"], rotation=45)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        st.pyplot(fig)

        st.write("""
        **Rata-rata Rating per Negara:**  
        Pada halaman ini terdapat jumlah rata rata rating untuk setiap negara, terdapat fitur filtering juga
        yang dapat memfilter setiap rating dari customer untuk setiap negara
        """)


def display_top_product(top_product_per_state):
    st.sidebar.header("Filter Data")
    selected_country = st.sidebar.selectbox(
        "Pilih Negara", 
        options=top_product_per_state["customer_state"].unique(),
        index=None,
        placeholder="Pilih negara..."
    )

    if selected_country:
        # Filter data hanya untuk negara yang dipilih
        filtered_data = top_product_per_state[top_product_per_state["customer_state"] == selected_country]

        # Ambil produk dengan total penjualan tertinggi
        top_product = filtered_data.iloc[0]  # Data sudah diambil dari 'get_top_product_per_state', jadi sudah sorted
        product_name = top_product["product_category_name"]
        total_sales = top_product["total_purchases"]

        st.subheader(f"Produk Terbanyak Dibeli di {selected_country}")

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(product_name, total_sales, color="royalblue")

        ax.set_xlabel("Produk")
        ax.set_ylabel("Total Penjualan")
        ax.set_title(f"Produk Terlaris di {selected_country}")
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        st.pyplot(fig)

        # Menampilkan informasi produk terlaris
        st.write(f"""
        **Pada negara {selected_country}, produk yang paling laku terjual adalah`{product_name} dengan total penjualan sebanyak {total_sales}.**
        """)

    else:
        # Jika tidak ada negara yang dipilih, tampilkan semua negara dalam line chart
        filtered_data = top_product_per_state

        st.subheader("Produk Terbanyak Dibeli di Semua Negara")

        fig, ax = plt.subplots(figsize=(12, 6))

        sns.lineplot(
            data=filtered_data,
            x="customer_state",
            y="total_purchases",
            hue="product_category_name",
            marker="o",
            linewidth=2,
            ax=ax
        )

        ax.set_xticklabels(filtered_data["customer_state"], rotation=45)
        ax.set_xlabel("Customer State")
        ax.set_ylabel("Total Purchases")
        ax.set_title("Produk Paling Banyak Dibeli di Semua Negara")
        ax.legend(title="Product Category", bbox_to_anchor=(1, 1))
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        st.pyplot(fig)

        st.write("""
        Ini adalah semua data yang paling laris di masing-masing negara.
        """)

def geolocation(dataframes):

    st.title("Penggunaan E-Commerce di Berbagai Negara")
    geolocation_df = dataframes["Geolocation"]
    st.subheader("Analisis Lanjutan")

    # Tambahkan Selectbox untuk memilih negara (default kosong)
    selected_state = st.sidebar.selectbox(
        "Pilih Negara",
        options=geolocation_df["geolocation_state"].unique(),
        index=None,  # Default tidak memilih apapun
        placeholder="Pilih negara..."
    )

    # Filter jika negara dipilih
    if selected_state:
        geolocation_df = geolocation_df[geolocation_df["geolocation_state"] == selected_state]

    # Batasi jumlah data untuk efisiensi
    if len(geolocation_df) > 10000:
        geolocation_df = geolocation_df.sample(n=10000, random_state=42)

    # Pusat peta berdasarkan titik tengah dataset
    map_center = [geolocation_df["geolocation_lat"].mean(), geolocation_df["geolocation_lng"].mean()]
    m = folium.Map(location=map_center, zoom_start=5)

    # Tambahkan titik lokasi
    for _, row in geolocation_df.iterrows():
        folium.CircleMarker(
            location=[row["geolocation_lat"], row["geolocation_lng"]],
            radius=2,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.5
        ).add_to(m)

    # Tambahkan HeatMap
    heat_data = geolocation_df[["geolocation_lat", "geolocation_lng"]].values.tolist()
    HeatMap(heat_data, radius=10, blur=15).add_to(m)

    # Tampilkan peta
    folium_static(m)

    # Tambahkan informasi
    if selected_state:
        st.write(f"ini adalah lokasi data pengguna dari negara **{selected_state}** yang menggunakan layanan ecommerse kami.")
    else:
        st.write("Ini adalah semua lokasi data pengguna yang menggunakan layanan toko ecommerse kami")





with st.sidebar:
    menu = st.selectbox(
        "Pilih halaman",
        ("Home", "Rata-rata Rating per Negara", "Produk Terlaris setiap Negara", "Penggunaan E-Commerce di Berbagai Negara")
    )

dataframes = load_data()

if menu == "Home":
    st.write("""
        **Dashboard**  
        Pada halaman web ini user dapat melihat data:
    
             1. Rata-rata Rating per Negara.

             2. Produk Terlaris setiap Negara.

             3. Penggunaan E-Commerce di Berbagai Negara.

        tidak hanya itu saja user dapat berinteraksi dengan halaman web ini, dengan fitur filter yang telah saya sediakan.
        """)
elif menu == "Rata-rata Rating per Negara":
    cleaned_dataframes = clean_data(dataframes)
    state_review_analysis, rating_state = get_state_review_analysis(cleaned_dataframes)
    display_ratings(state_review_analysis, rating_state)
elif menu == "Produk Terlaris setiap Negara":
    cleaned_dataframes = clean_data(dataframes)
    state_top_analis = get_top_product_per_state(cleaned_dataframes)
    display_top_product(state_top_analis)
elif menu == "Penggunaan E-Commerce di Berbagai Negara":
    geolocation(dataframes)