import streamlit as st
import pandas as pd
from PIL import Image
import re
import os
import base64
import jellyfish

# Function to preprocess text
def preprocess_text(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).strip()

# Function to calculate Jaro-Winkler similarity
def jaro_winkler_similarity(s1: str, s2: str) -> float:
    try:
        s1, s2 = preprocess_text(s1), preprocess_text(s2)
        return jellyfish.jaro_winkler_similarity(s1, s2)
    except Exception as e:
        st.error(f"Error calculating similarity: {e}")
        return 0.0

# Function to match names
def match_name_address(df: pd.DataFrame, user_name: str) -> pd.DataFrame:
    if 'name' not in df.columns:
        st.error("DataFrame must contain 'name' column")
        return pd.DataFrame()

    df['name_similarity'] = df['name'].apply(lambda name: jaro_winkler_similarity(name, user_name))
    return df[df['name_similarity'] > 0.75][['name', 'name_similarity']]

# Function to check if the user is already registered
def is_user_registered(df: pd.DataFrame, name: str, apmid: str) -> bool:
    if {'name', 'apmid'}.issubset(df.columns):
        return not df[(df['name'].str.lower() == name.lower()) & (df['apmid'].astype(str).str.lower() == apmid.lower())].empty
    return False

# Function to append new user data to CSV
def append_to_registered_users(name: str, apmid: str, file_path="registered_users.csv"):
    new_row = pd.DataFrame({"name": [name], "apmid": [apmid]})
    new_row.to_csv(file_path, mode='a', header=not os.path.isfile(file_path), index=False)

# Streamlit app
def main():
    st.image("minerva_logo.jpg", width=800)
    
    try:
        df = pd.read_csv("Entity_data.csv").applymap(lambda x: x.strip() if isinstance(x, str) else x)
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return
    
    st.subheader("Please Register Yourself!")
    name_input = st.text_input("Enter Your Name:")
    apmid_input = st.text_input("Enter Your APMID:")

    if st.button("Save"):
        if name_input and apmid_input:
            if is_user_registered(df, name_input, apmid_input):
                st.warning(f"User '{name_input}' with APMID '{apmid_input}' is already registered!")
            else:
                append_to_registered_users(name_input, apmid_input)
                st.success(f"Name '{name_input}' and APMID '{apmid_input}' saved!")
        else:
            st.error("Please fill both Name and APMID fields.")
    
    st.subheader("Let's verify if you are not part of sanctioned entities")
    user_name = st.text_input("Your Name for Matching:")

    if st.button("Match"):
        if user_name:
            result_df = match_name_address(df, user_name)
            if not result_df.empty:
                st.write("Ooo... You matched with one of the sanctioned entities. Further investigation required:")
                st.dataframe(result_df.sort_values(by=['name_similarity'], ascending=False).reset_index(drop=True))
            else:
                st.write("Congratulations! You are not part of any sanctioned list.")
        else:
            st.error("Please provide a name to match.")

if __name__ == "__main__":
    main()
