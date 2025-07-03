import streamlit as st
from tqdm import tqdm  # For progress bar
from openai import OpenAI
import pandas as pd
import time
from dotenv import load_dotenv
import os


load_dotenv()  
# Initialize OpenAI client

client = OpenAI(
  api_key= os.getenv("OPEN_AI_API_KEY"),
)
st.title("Insurance Appeal Letter Generator")

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

def process_data(df):
    letters = []
    status_container = st.empty()
    # Display a progress bar 
    progress_bar = st.progress(0)
    progress_text = st.empty()
    start_time = time.time()
    status_container.write("Processing data... This may take a moment.")

    # Iterate through each row and generate a letter
    
    for index, row in df.iterrows():
        progress = (index + 1) / len(df)
        progress_bar.progress(progress) 
        elapsed = time.time() - start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        if progress > 0:
            estimated_total_time = elapsed / progress
            remaining = estimated_total_time - elapsed
        else:
            remaining = 0
        remaining_str = time.strftime("%H:%M:%S", time.gmtime(remaining))

        progress_text.text(
        f"{int(progress * 100)}% complete — Time elapsed: {elapsed_str} — Estimated time remaining: {remaining_str}"
    )
        tqdm.pandas(desc="Generating letters")

        prompt = f"""Using the information below, draft a personalized appeal letter on behalf of the patient’s provider.

        Patient Name: {row['patient_name']}
        Insurance Company: {row['insurance_company']}
        Denial Reason: {row['denial_reason']}
        Service/Procedure: {row['procedure']}
        Provider Name: {row['provider_name']}
        Clinical Notes / Context: {row['notes']}
        Appeal Deadline (if applicable): {row['appeal_deadline']}

        Instructions:
        - Use clear, formal language.
        - Include the reason the procedure was medically necessary.
        - Reference the denial reason and respectfully refute it using the context provided.
        - Mention supporting documentation if hinted at in the notes.
        - Keep the tone respectful, professional, and factual.

        Write the letter as if it's being submitted directly to the insurance company on the provider’s behalf.
        Do not make up facts or dates.
        Do not include a real signature or PHI outside the details provided.

        Format:

        [Letter Body]

        Sincerely,  
        {row['provider_name']}
        Now generate the appeal letter."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a medical office assistant..."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )

        letters.append(response.choices[0].message.content)
    status_container.empty()  # Clear the status message
    progress_bar.empty()  # Clear the progress bar
    progress_text.empty()  # Clear the progress text
    st.success("All letters generated successfully!")
    st.balloons()  # Celebrate completion
    return letters

# Check if file uploaded and not yet processed
if uploaded_file is not None and 'df' not in st.session_state:
    df = pd.read_csv(uploaded_file)
    letters = process_data(df)
    df['generated_letter'] = letters
    st.session_state.df = df  # Store in session so it's not re-run

# Once cached, retrieve from session
if 'df' in st.session_state:
    df = st.session_state.df

    @st.cache_data
    def get_cached_dataframe(df):
        return df.to_csv(index=False).encode('utf-8')

    formatted_csv = get_cached_dataframe(df)

    st.download_button(
        label="Download CSV with Letters",
        data=formatted_csv,
        file_name='insurance_appeals_with_letters.csv',
        mime='text/csv'
    )

    st.write("✅ Letters generated:")
    st.dataframe(df[["patient_name", "generated_letter"]])