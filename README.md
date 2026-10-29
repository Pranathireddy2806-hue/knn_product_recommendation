
# Smart Product Finder — KNN Product Recommendation System

A machine-learning project that recommends similar Amazon products using TF-IDF, numerical features, K-Nearest Neighbors (KNN), and a Streamlit web interface.

## Project Overview

The application lets a user select a product and discover similar products from the dataset. It displays product names, categories, descriptions, prices, ratings, discounts, images, and product links when available.

## Dataset

Source: Amazon Sales Dataset on Kaggle

https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset

The supplied dataset has 1,465 rows and 16 original columns.

The project uses these columns:
- product_id
- product_name
- category
- discounted_price
- actual_price
- discount_percentage
- rating
- about_product
- img_link
- product_link

Other columns are available in the original dataset but are not needed for this version of the recommender.

## Technologies Used

- Python
- Pandas
- Scikit-learn
- SciPy
- TF-IDF
- K-Nearest Neighbors
- Cosine distance
- Streamlit

## Project Structure

```text
knn_product_recommendation/
├── app.py
├── train_model.py
├── requirements.txt
├── README.md
├── .gitignore
└── data/
    └── amazon.csv
```

## Features

- Select a product from the dataset.
- Recommend similar products using KNN.
- Display product descriptions, prices, ratings, and discounts.
- Show product images when their URLs are accessible.
- Open product pages when links are available.
- Choose how many recommendations to display.
- Explain the model methodology inside the application.

## How the Model Works

### 1. Data Cleaning

Pandas loads the CSV, converts prices and discounts to numeric values, handles missing values, removes unusable records, and removes duplicate product IDs.

### 2. Text Feature Extraction

TF-IDF converts product names, categories, and descriptions into numerical vectors. These vectors represent the words and phrases associated with each product.

### 3. Numerical Feature Processing

The model uses discounted price, rating, and discount percentage. Price is log-transformed, and numerical features are standardized before being combined with text features.

### 4. KNN Recommendation

Scikit-learn's NearestNeighbors finds products with the smallest cosine distances from the selected product.

### 5. User Interface

Streamlit displays the selected product and the resulting recommendations in a browser.

## Installation on Windows

### Step 1: Open the project

Extract the project ZIP and open the `knn_product_recommendation` folder in VS Code.

### Step 2: Create a virtual environment

```powershell
python -m venv .venv
```

### Step 3: Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### Step 4: Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 5: Test the model

```powershell
python train_model.py
```

The terminal should show the number of valid products and a sample of recommendations.

### Step 6: Run the web application

```powershell
python -m streamlit run app.py
```

Open the local URL printed in the terminal, usually:

http://localhost:8501

Keep the terminal running while using the application.

## Limitations

- This is a content-based recommender, not a personalized recommendation engine.
- The model does not predict purchases or customer satisfaction.
- The similarity score is not a purchase probability.
- Recommendations depend on the dataset and selected features.
- Product images and links may become unavailable.
- The project is intended as a learning and demonstration project.

## Future Improvements

- Add search and category filters.
- Add a price-range filter.
- Compare multiple recommendation algorithms.
- Evaluate recommendation quality using a defined evaluation method.
- Add user preferences and interaction history.
- Deploy the application online.

## GitHub Publishing

Check the Kaggle dataset license and terms before redistributing the CSV. If redistribution is not permitted, do not commit the dataset file; instead, explain how to download it from Kaggle.

Never commit passwords, access tokens, or other secrets.

## Skills Demonstrated

Python, data cleaning, Pandas, TF-IDF, feature scaling, sparse matrices, cosine distance, KNN, recommendation systems, Streamlit, and project documentation.
