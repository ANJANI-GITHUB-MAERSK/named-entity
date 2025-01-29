import streamlit as st
import pandas as pd
from pyjarowinkler import distance  # Using pyjarowinkler for Jaro-Winkler similarity
import os

# Function to preprocess text by making it lowercase and removing special characters
def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

# Function to calculate Jaro-Winkler similarity
def jaro_winkler_similarity(s1: str, s2: str) -> float:
    try:
        s1 = preprocess_text(s1)
        s2 = preprocess_text(s2)
        return distance.get_jaro_distance(s1, s2, winkler=True)
    except Exception as e:
        st.error(f"Error calculating similarity: {e}")
        return 0.0

# Function to match name with the dataframe
def match_name_address(df: pd.DataFrame, user_name: str) -> pd.DataFrame:
    try:
        # Check if 'name' column exists in the DataFrame
        if 'name' not in df.columns:
            st.error("DataFrame must contain 'name' column")
            return pd.DataFrame()

        # Initialize an empty list to store similarity scores
        similarity_scores = []

        # Iterate through the 'name' column and calculate similarity for each row
        for name in df['name']:
            score = jaro_winkler_similarity(name, user_name)
            similarity_scores.append(score)

        # Add the similarity scores to the DataFrame as a new column
        df['name_similarity'] = similarity_scores

        # Filter records with a similarity score greater than 75%
        filtered_df = df[df['name_similarity'] > 0.75]

        # Return relevant columns
        return filtered_df[['name', 'name_similarity']]

    except Exception as e:
        st.error(f"Error in matching: {e}")
        return pd.DataFrame()

# Function to check if the user is already registered
def is_user_registered(df: pd.DataFrame, name: str, apmid: str) -> bool:
    if 'name' not in df.columns or 'apmid' not in df.columns:
        return False

    df['name'] = df['name'].str.lower()
    df['apmid'] = df['apmid'].astype(str).str.lower()
    
    name = name.lower()
    apmid = apmid.lower()
    
    return not df[(df['name'] == name) & (df['apmid'] == apmid)].empty

# Function to append new user data to registered_users.csv
def append_to_registered_users(name: str, apmid: str):
    new_row = pd.DataFrame({"name": [name], "apmid": [apmid]})
    file_path = "registered_users.csv"
    
    if os.path.isfile(file_path):
        new_row.to_csv(file_path, mode='a', header=False, index=False)
    else:
        new_row.to_csv(file_path, mode='w', header=True, index=False)

    create_download_link(file_path)

def create_download_link(file_path):
    try:
        # Open the file and read its content
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Check if data is empty or None
        if not data:
            st.error("The file is empty or could not be read properly.")
            return
        
        # Encode the data to base64
        b64 = base64.b64encode(data).decode()  # Convert to base64
        href = f'<a href="data:file/csv;base64,{b64}" download="{file_path}">Download {file_path}</a>'
        st.markdown(href, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error creating download link: {e}")


# Streamlit app
def main():
    # Load entity data
    try:
        df = pd.read_csv("Entity_data.csv")
        df.columns = df.columns.str.strip()  # Strip whitespace from column names
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

    st.subheader("Verify Your Name with Sanctioned Entities")
    user_name = st.text_input("Your Name for Matching:")

    if st.button("Match"):
        if user_name:
            result_df = match_name_address(df, user_name)
            if not result_df.empty:
                st.write("You matched with a sanctioned entity (score > 75%):")
                st.dataframe(result_df)
            else:
                st.write("You're not part of any sanctioned list.")
        else:
            st.error("Please provide a name to match.")

if __name__ == "__main__":
    main()
