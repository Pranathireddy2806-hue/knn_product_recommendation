import html
import random
import re

import requests
import streamlit as st

from train_model import load_products, build_model, recommend_products

st.set_page_config(page_title="Smart Product Finder", page_icon="🛍️", layout="wide")

# Colours used for the card banners (they cycle through the list)
COLORS = ["#7c4dff", "#ff6b6b", "#00b8a9", "#ff9f1c", "#3a86ff", "#e84393"]

# ---------------------------------------------------------
# STYLE (colours only - no logic here)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 5% 0%, #e0d4ff 0, transparent 35%),
            radial-gradient(circle at 95% 10%, #ffe0cc 0, transparent 30%),
            radial-gradient(circle at 50% 100%, #d4f5ee 0, transparent 35%),
            #faf9ff;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ede4ff 0%, #ffeede 100%);
    }
    .hero {
        padding: 2rem; border-radius: 24px; color: white; margin-bottom: 1.2rem;
        background: linear-gradient(120deg, #6c3fd1, #e84393, #ff9f1c);
        background-size: 200% 200%;
        animation: shift 8s ease infinite;
        box-shadow: 0 14px 35px rgba(108, 63, 209, 0.3);
    }
    @keyframes shift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .hero h1 {margin: 0; font-size: 2.5rem;}
    .hero p {margin: .4rem 0 0; font-size: 1.1rem; opacity: .95;}
    .badge {
        display: inline-block; padding: 3px 12px; border-radius: 999px;
        color: white; font-size: .8rem; font-weight: 700; margin: 0 6px 6px 0;
    }
    .price {font-size: 1.6rem; font-weight: 800; color: #512da8;}
    .old-price {color: #999; text-decoration: line-through; margin-left: 8px;}
    [data-testid="stMetric"] {
        background: white; padding: 1rem; border-radius: 16px;
        border-left: 6px solid #7c4dff; box-shadow: 0 4px 14px rgba(0,0,0,.06);
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px; background: rgba(255,255,255,.92);
        transition: transform .2s, box-shadow .2s;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px); box-shadow: 0 12px 28px rgba(108,63,209,.2);
    }
    .stTabs [data-baseweb="tab"] {font-weight: 700; font-size: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🛍️ Smart Product Finder</h1>
        <p>Pick a product, tweak the filters, and discover similar finds you'll love.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# LOAD DATA + MODEL (cached so it only runs once)
# ---------------------------------------------------------
@st.cache_resource
def get_recommender():
    products = load_products()
    product_categories = (
        products["category"].str.split("|", regex=False).str[0].str.strip()
    )
    top_categories = product_categories.value_counts().head(5).index
    products = products.loc[
        product_categories.isin(top_categories)
    ].reset_index(drop=True)
    model, features = build_model(products)
    return products, model, features


try:
    products, model, features = get_recommender()
except Exception as error:
    st.error(f"Could not load the dataset or build the model: {error}")
    st.info("Check that data/amazon.csv exists and the requirements are installed.")
    st.stop()

# Favourites are remembered while the app is open
if "favs" not in st.session_state:
    st.session_state.favs = set()


# ---------------------------------------------------------
# SMALL HELPER FUNCTIONS
# ---------------------------------------------------------
def short(text, length):
    text = str(text)
    return text if len(text) <= length else text[:length] + "..."


def badge(text, color):
    return f'<span class="badge" style="background:{color}">{html.escape(text)}</span>'


def similarity_color(score):
    if score >= 60:
        return "#00b894"   # green = very similar
    if score >= 30:
        return "#ff9f1c"   # orange = somewhat similar
    return "#e84393"       # pink = loosely similar


def toggle_favourite(product_id, name):
    if product_id in st.session_state.favs:
        st.session_state.favs.remove(product_id)
        st.toast(f"Removed: {short(name, 40)}", icon="💔")
    else:
        st.session_state.favs.add(product_id)
        st.toast(f"Saved: {short(name, 40)}", icon="❤️")


def pick_random(options):
    st.session_state.chosen = random.choice(options)


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_product_image(image_url):
    """Fetch and cache an image so the browser does not request Amazon directly."""
    if not image_url.startswith(("http://", "https://")):
        return None, "invalid image URL"

    image_match = re.match(
        r"^(https?://m\.media-amazon\.com)/"
        r"(?:images/W/WEBP_[^/]+/)?images/I/([^./]+)",
        image_url,
        flags=re.IGNORECASE,
    )
    image_urls = [image_url]
    if image_match:
        image_base = f"{image_match.group(1)}/images/I/{image_match.group(2)}"
        image_urls = [
            f"{image_base}._SX300_SY300_QL70_.jpg",
            f"{image_base}._SY445_.jpg",
            f"{image_base}.jpg",
            image_url,
        ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/130.0 Safari/537.36"
        ),
        "Referer": "https://www.amazon.in/",
    }
    last_error = "image host could not be reached"

    for candidate_url in dict.fromkeys(image_urls):
        try:
            response = requests.get(candidate_url, headers=headers, timeout=5)
            response.raise_for_status()
        except requests.HTTPError as error:
            if error.response is None:
                last_error = "image host rejected the request"
            else:
                last_error = f"HTTP {error.response.status_code}"
            continue
        except requests.RequestException:
            continue

        if not response.headers.get("Content-Type", "").startswith("image/"):
            last_error = "image host returned an unsupported response"
            continue
        if len(response.content) > 5_000_000:
            last_error = "image is too large to display"
            continue
        return response.content, None

    return None, last_error


def show_product_image(image_url):
    image_data, unavailable_reason = fetch_product_image(str(image_url).strip())
    if image_data:
        st.image(image_data, width="stretch")
    else:
        st.markdown(
            """
            <div style="
                min-height: 150px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 14px;
                background: linear-gradient(135deg, #f1eaff, #fff0e7);
                color: #745a9e;
                font-weight: 600;
            ">🖼️ Product image unavailable</div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(unavailable_reason)


def show_card(product, label, color, key_prefix):
    """Draw one colourful product card."""
    with st.container(border=True):
        st.markdown(badge(label, color), unsafe_allow_html=True)

        show_product_image(product["image_link"])

        st.markdown(f"**{short(product['product_name'], 75)}**")

        last_category = str(product["category"]).split("|")[-1]
        stars = "⭐" * int(round(product["rating"]))
        st.markdown(
            badge(last_category, "#3a86ff")
            + badge(f"{product['discount']:.0f}% OFF", "#ff6b6b")
            + badge(f"{stars} {product['rating']:.1f}", "#ff9f1c"),
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<span class="price">₹{product["price"]:,.0f}</span>'
            f'<span class="old-price">₹{product["actual_price"]:,.0f}</span>',
            unsafe_allow_html=True,
        )

        with st.expander("Read description"):
            st.write(short(product["description"], 600))

        if "similarity" in product:
            score = float(product["similarity"])
            st.markdown(
                f'<div style="color:{similarity_color(score)};font-weight:700">'
                f"Similarity: {score:.1f}%</div>",
                unsafe_allow_html=True,
            )
            st.progress(int(score))

        col1, col2 = st.columns(2)
        url = str(product["product_link"])
        if url.startswith(("http://", "https://")):
            col1.link_button("🛒 View", url, width="stretch")

        saved = product["product_id"] in st.session_state.favs
        col2.button(
            "💔 Remove" if saved else "🤍 Save",
            key=f"{key_prefix}_{product['product_id']}",
            on_click=toggle_favourite,
            args=(product["product_id"], product["product_name"]),
            width="stretch",
        )


def show_grid(df, per_row, label_fn, key_prefix):
    """Show products in rows of cards."""
    rows = list(df.iterrows())
    for start in range(0, len(rows), per_row):
        columns = st.columns(per_row)
        for offset, (column, (_, product)) in enumerate(zip(columns, rows[start:start + per_row])):
            rank = start + offset
            with column:
                show_card(product, label_fn(rank), COLORS[rank % len(COLORS)], key_prefix)


# ---------------------------------------------------------
# SIDEBAR: all the controls
# ---------------------------------------------------------
st.sidebar.header("🎨 Find your match")

# 1) Pick the product
search_query = st.sidebar.text_input("🔎 Search products", placeholder="e.g. cable, mixer, headphones")

product_categories = (
    products["category"].str.split("|", regex=False).str[0].str.strip()
)
categories = ["All categories"] + product_categories.value_counts().index.tolist()
selected_category = st.sidebar.selectbox(
    "📂 Category",
    categories,
    format_func=lambda category: category.replace("&", " & "),
)

matching = products
if selected_category != "All categories":
    matching = products.loc[product_categories == selected_category]
if search_query.strip():
    text = matching["product_name"] + " " + matching["category"] + " " + matching["description"]
    matching = matching[text.str.contains(search_query.strip(), case=False, regex=False)]

if matching.empty:
    st.info("No products match those filters. Try another category or search.")
    st.stop()

options = matching.index.tolist()

st.sidebar.selectbox(
    "🛒 Choose a product",
    options,
    key="chosen",
    format_func=lambda i: short(products.loc[i, "product_name"], 70),
)
st.sidebar.button("🎲 Surprise me!", on_click=pick_random, args=(options,), width="stretch")
st.sidebar.caption(f"{len(matching):,} products match your filters")

# 2) Tune the recommendations
st.sidebar.divider()
st.sidebar.subheader("🎛️ Tune results")

how_many = st.sidebar.slider("How many recommendations?", 1, 12, 6)

min_price, max_price = int(products["price"].min()), int(products["price"].max())
price_range = st.sidebar.slider("💰 Price range (₹)", min_price, max_price, (min_price, max_price))

min_rating = st.sidebar.slider("⭐ Minimum rating", 0.0, 5.0, 0.0, step=0.1)

sort_by = st.sidebar.selectbox(
    "↕️ Sort by",
    ["Most similar", "Top rated", "Price: low to high", "Price: high to low", "Biggest discount"],
)

per_row = st.sidebar.select_slider("🧱 Cards per row", options=[2, 3, 4], value=3)

selected_index = st.session_state.chosen
selected_product = products.loc[selected_index]


# ---------------------------------------------------------
# GET RECOMMENDATIONS
# ---------------------------------------------------------
# Ask for many neighbours first, then apply the price/rating filters
candidates = recommend_products(selected_index, products, model, features, n=100)
candidates = candidates[
    candidates["price"].between(price_range[0], price_range[1])
    & (candidates["rating"] >= min_rating)
]
recommendations = candidates.head(how_many)

if sort_by == "Top rated":
    recommendations = recommendations.sort_values("rating", ascending=False)
elif sort_by == "Price: low to high":
    recommendations = recommendations.sort_values("price")
elif sort_by == "Price: high to low":
    recommendations = recommendations.sort_values("price", ascending=False)
elif sort_by == "Biggest discount":
    recommendations = recommendations.sort_values("discount", ascending=False)


# ---------------------------------------------------------
# MAIN PAGE: tabs
# ---------------------------------------------------------
tab_recs, tab_compare, tab_favs, tab_info = st.tabs([
    "💜 Recommendations",
    "📊 Compare",
    f"❤️ Favourites ({len(st.session_state.favs)})",
    "💡 How it works",
])

# ----- Tab 1: selected product + recommendations -----
with tab_recs:
    st.subheader("✨ Your selected product")

    left, right = st.columns([1, 3])
    with left:
        show_product_image(selected_product["image_link"])

    with right:
        st.markdown(f"### {selected_product['product_name']}")
        st.caption(str(selected_product["category"]).replace("|", " › "))

        m1, m2, m3 = st.columns(3)
        m1.metric("Price", f"₹{selected_product['price']:,.0f}")
        m2.metric("Rating", f"{selected_product['rating']:.1f} / 5")
        m3.metric("Discount", f"{selected_product['discount']:.0f}%")

        with st.expander("Read description"):
            st.write(short(selected_product["description"], 1200))

    st.divider()
    st.subheader("🌈 Picks you may like")

    if recommendations.empty:
        st.warning("No recommendations match your price/rating filters. Try loosening them.")
    else:
        st.caption(f"Showing {len(recommendations)} products, sorted by: {sort_by.lower()}")
        show_grid(recommendations, per_row, lambda r: f"#{r + 1}", "rec")

# ----- Tab 2: charts and table -----
with tab_compare:
    if recommendations.empty:
        st.info("Nothing to compare yet - loosen your filters.")
    else:
        chart_data = recommendations.copy()
        chart_data["name"] = chart_data["product_name"].apply(lambda t: short(t, 25))
        chart_data = chart_data.set_index("name")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🎯 Similarity (%)")
            st.bar_chart(chart_data["similarity"], color="#7c4dff")
        with c2:
            st.markdown("#### 💰 Price (₹)")
            st.bar_chart(chart_data["price"], color="#ff6b6b")

        st.markdown("#### 📋 Full table")
        table = recommendations[["product_name", "price", "rating", "discount", "similarity"]]
        st.dataframe(table, hide_index=True, width="stretch")

        st.download_button(
            "⬇️ Download these recommendations (CSV)",
            table.to_csv(index=False),
            file_name="recommendations.csv",
            mime="text/csv",
        )

# ----- Tab 3: saved products -----
with tab_favs:
    saved_products = products[products["product_id"].isin(st.session_state.favs)]
    if saved_products.empty:
        st.info("You haven't saved anything yet. Click 🤍 Save on any card!")
    else:
        show_grid(saved_products, per_row, lambda r: "❤️ Saved", "fav")

# ----- Tab 4: explanation -----
with tab_info:
    st.markdown(
        """
        1. **Clean the data** - remove symbols like ₹ , % and turn text into numbers.
        2. **TF-IDF** - turns each product's name, category and description into numbers.
        3. **KNN** - finds the products whose numbers are closest (cosine distance).
        4. **Filters** - your price and rating choices are applied to those neighbours.

        **Note:** similarity is a score of how alike two product *descriptions* are.
        It is not a prediction that you will buy the product.
        """
    )

st.caption("Built with Python, Pandas, scikit-learn and Streamlit · Dataset: Amazon Sales (Kaggle)")