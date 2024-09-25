import streamlit as st
import pandas as pd
from PIL import Image
import re
from concurrent.futures import ThreadPoolExecutor
import requests
import json
import base64
from pyjarowinkler import distance  # Ensure you have installed pyjarowinkler
from io import StringIO  # Import StringIO for in-memory file handling
import os

# GitHub details
# GITHUB_TOKEN = '--'  # Replace with your personal access token
# GITHUB_REPO = '--'  # Replace with the name of your repo
# GITHUB_FILE_PATH = '--'  # Desired file path in the repo

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

# Function to match name using multithreading
def match_single_name(name: str, user_name: str) -> tuple:
    similarity = jaro_winkler_similarity(name, user_name)
    return name, similarity

# Function to match name with the dataframe
def match_name_address(df: pd.DataFrame, user_name: str) -> pd.DataFrame:
    try:
        if 'name' not in df.columns:
            st.error("DataFrame must contain 'name' column")
            return pd.DataFrame()

        # Multithreading for faster similarity calculation
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda name: match_single_name(name, user_name), df['name']))

        # Assign results back to the DataFrame
        df['name_similarity'] = [similarity for _, similarity in results]

        # Filter records with a similarity score > 85%
        filtered_df = df[df['name_similarity'] > 0.85]

        return filtered_df[['name', 'name_similarity']]

    except Exception as e:
        st.error(f"Error in matching: {e}")
        return pd.DataFrame()

# # Function to upload CSV to GitHub
# def upload_file_to_github(content, commit_message):
#     url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
#     headers = {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json"
#     }

    # Check if the file already exists
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
    else:
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
        }

    result = requests.put(url, headers=headers, data=json.dumps(data))
    if result.status_code == 201 or result.status_code == 200:
        st.success("File uploaded successfully to GitHub!")
    else:
        st.error(f"Failed to upload file: {result.content}")

# Function to save the updated DataFrame to GitHub
def save_csv_to_github(df, commit_message="Update CSV via Streamlit App"):
    csv_content = df.to_csv(index=False)
    #upload_file_to_github(csv_content, commit_message)

# def create_download_link(df, filename):
#     # Create a CSV string from the DataFrame
#     csv = df.to_csv(index=False)
#     # Create a download button
#     st.download_button(
#         label="Download data as CSV",
#         data=csv,
#         file_name=filename,
#         mime="text/csv"
#     )
# Function to check if the user is already registered
def is_user_registered(df: pd.DataFrame, name: str, apmid: str) -> bool:
    if 'name' not in df.columns or 'apmid' not in df.columns:
        return False

    df['name'] = df['name'].str.lower()
    df['apmid'] = df['apmid'].astype(str).str.lower()
    
    name = name.lower()
    apmid = apmid.lower()
    
    return not df[(df['name'] == name) & (df['apmid'] == apmid)].empty

# Function to append new user data to registered_users2.csv
def append_to_registered_users(name: str, apmid: str):
    # Create the DataFrame with the new entry
    new_row = pd.DataFrame({"name": [name], "apmid": [apmid]})
    
    # Check if the file exists
    file_path = "registered_users.csv"
    
    if os.path.isfile(file_path):
        # Append to existing CSV without the header
        new_row.to_csv(file_path, mode='a', header=False, index=False)
    else:
        # Create a new CSV file with header
        new_row.to_csv(file_path, mode='w', header=True, index=False)

    # Optional: Create a download link for the CSV file
    create_download_link(file_path)

# Function to create a download link
def create_download_link(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()  # Convert to base64
    href = f'<a href="data:file/csv;base64,{b64}" download="{file_path}">Download {file_path}</a>'
    st.markdown(href, unsafe_allow_html=True)

# Streamlit app
def main():
    logo = Image.open("minerva_logo.jpg")  # Replace with your logo path
    st.image(logo, width=800)

    # Load entity data
    try:
        df = pd.read_csv("Entity_data.csv")
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return

    # Use session state to manage the name after save
    if 'saved_name' not in st.session_state:
        st.session_state.saved_name = ""

    st.subheader("Please Register Yourself!")

    # Input fields for name and APMID
    name_input = st.text_input("Enter Your Name:")
    apmid_input = st.text_input("Enter Your APMID:")

    # Save button to register the name and APMID
    if st.button("Save"):
        if name_input and apmid_input:
            if is_user_registered(df, name_input, apmid_input):
                st.warning(f"User '{name_input}' with APMID '{apmid_input}' is already registered!")
            else:
                new_row = pd.DataFrame({"name": [name_input], "apmid": [apmid_input]})
                #df = pd.concat([df, new_row], ignore_index=True)

                # Save updated CSV to GitHub
                save_csv_to_github(df, commit_message="New user registered via Streamlit app")
                st.success(f"Name '{name_input}' and APMID '{apmid_input}' saved!")
                st.session_state.saved_name = name_input

                 # Append to registered_users2.csv
                append_to_registered_users(name_input, apmid_input)
        else:
            st.error("Please fill both Name and APMID fields.")

    st.subheader("Let's verify if you are not part of sanctioned entities")

    # Use the saved name to populate the "Enter Your Name" field
    user_name = st.text_input("Your Name for Matching:", value=st.session_state.saved_name)

    if st.button("Match"):
        if user_name:
            result_df = match_name_address(df, user_name)
            if not result_df.empty:
                st.write("Ooo... You matched with one of the sanctioned entities. Further investigation required (score > 85%):")
                st.dataframe(result_df[['name', 'name_similarity']].sort_values(by=['name_similarity'], ascending=False).reset_index(drop=True))
            else:
                st.write("Congratulations! You are not part of any sanctioned list.")

            # Reset the "Enter Your Name" field for next input
            st.session_state.saved_name = ""
        else:
            st.error("Please provide a name to match.")

if __name__ == "__main__":
    main()
