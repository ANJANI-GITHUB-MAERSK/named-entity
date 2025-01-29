import streamlit as st
import pandas as pd
from PIL import Image
import re
import os
import jellyfish

# Function to preprocess text by making it lowercase and removing special characters
def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

# Function to calculate Damerau-Levenshtein similarity
def damerau_levenshtein_similarity(s1: str, s2: str) -> float:
    try:
        s1 = preprocess_text(s1)
        s2 = preprocess_text(s2)
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0  # If both strings are empty, similarity is 1
        distance = jellyfish.damerau_levenshtein_distance(s1, s2)
        return 1 - (distance / max_len)  # Convert distance to similarity
    except Exception as e:
        st.error(f"Error calculating similarity: {e}")
        return 0.0

# Function to match names
def match_name_address(df: pd.DataFrame, user_name: str) -> pd.DataFrame:
    try:
        if 'name' not in df.columns:
            st.error("DataFrame must contain 'name' column")
            return pd.DataFrame()

        df['name_similarity'] = df['name'].apply(lambda name: damerau_levenshtein_similarity(name, user_name))
        filtered_df = df[df['name_similarity'] > 0.75]
        return filtered_df[['name', 'name_similarity']]
    except Exception as e:
        st.error(f"Error in matching: {e}")
        return pd.DataFrame()

# Streamlit app
def main():
    logo = Image.open("minerva_logo.jpg")  # Replace with your logo path
    st.image(logo, width=800)

    try:
        df = pd.read_csv("Entity_data.csv")
        df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return

    st.subheader("Let's verify if you are not part of sanctioned entities")
    user_name = st.text_input("Your Name for Matching:")

    if st.button("Match"):
        if user_name:
            result_df = match_name_address(df, user_name)
            if not result_df.empty:
                st.write("Ooo... You matched with one of the sanctioned entities. Further investigation required (score > 75%):")
                st.dataframe(result_df.sort_values(by=['name_similarity'], ascending=False).reset_index(drop=True))
            else:
                st.write("Congratulations! You are not part of any sanctioned list.")
        else:
            st.error("Please provide a name to match.")

if __name__ == "__main__":
    main()
