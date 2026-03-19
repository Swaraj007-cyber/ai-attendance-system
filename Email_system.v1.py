from huggingface_hub import InferenceClient
from mailjet_rest import Client
import pandas as pd
import os

# ==========================================
# 1. API Configuration
# ==========================================
HF_API_TOKEN = "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" 
hf_client = InferenceClient(api_key=HF_API_TOKEN)

MAILJET_API_KEY = "d5ae1705a799eed0828f580c67ae931a"
MAILJET_API_SECRET = "378ee2af9289e5fd17d412535b8f6821"
SENDER_EMAIL = "swarajsandeepchondhe@gmail.com" 
SENDER_NAME = "Zeal College Attendance Office"

mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')

# ==========================================
# 2. Updated Student Database (File Loading)
# ==========================================
def get_attendance_data():
    """Asks for filename and ensures Python looks in the script's folder."""
    # PERMANENT PATH FIX: 
    # This force-switches Python to the folder where this script is saved.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("--- 📂 Attendance Data Loader ---")
    print(f"Current Folder: {script_dir}") # Helps you verify where to put the Excel file
    file_path = input("Enter the filename (e.g., 19-Mar-2026.xlsx): ").strip()

    if not os.path.exists(file_path):
        print(f"❌ Error: The file '{file_path}' was not found in this folder.")
        return None

    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            # Requires: pip install openpyxl
            df = pd.read_excel(file_path)
        
        # Clean column names (removes spaces, makes them Title Case)
        df.columns = [c.strip().title() for c in df.columns]
        
        # Verification: Ensure required columns exist
        required = ['Name', 'Email', 'Status', 'Previous_Absences']
        if not all(col in df.columns for col in required):
            print(f"❌ Error: Missing columns. File must have: {required}")
            return None
            
        return df
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return None

# ==========================================
# 3. AI Email Generator (Strict Rule-Based)
# ==========================================
def generate_ai_email_body(name, previous_absences):
    """Uses Hugging Face with strict, checklist-style prompts to prevent hallucinations."""
    
    if previous_absences == 0:
        instructions = (
            f"Draft an email to {name}.\n"
            f"Rule 1: Start the text EXACTLY with 'Dear {name},'. Do not invent last names.\n"
            f"Rule 2: Write exactly 7 sentences.\n"
            f"Rule 3: State they were absent today for the first time and ask if they are well.\n"
            f"Rule 4: Remind them to check the Zeal College portal for today's notes.\n"
            f"Rule 5: End the message immediately after the 7rd sentence. Absolutely NO sign-offs, signatures, or 'Best regards'."
        )
    elif previous_absences <= 2:
        instructions = (
            f"Draft a firm academic email to {name}.\n"
            f"Rule 1: Start the text EXACTLY with 'Dear {name},'. Do not invent last names.\n"
            f"Rule 2: Write exactly 7 sentences.\n"
            f"Rule 3: Inform them they were marked absent today, bringing their total to {previous_absences} absences.\n"
            f"Rule 4: Firmly state that consistent attendance is crucial for Zeal College coursework.\n"
            f"Rule 5: End the message immediately after the 7rd sentence. Absolutely NO sign-offs, signatures, or 'Best regards'."
        )
    else:
        instructions = (
            f"Draft a severe, urgent email to {name}."
            f"Rule 1: Start the text EXACTLY with 'Dear {name},'. Do not invent last names."
            f"Rule 2: Write exactly 10 sentences."
            f"Rule 3: State they were marked absent today, reaching a critical threshold of {previous_absences} absences."
            f"Rule 4: Order them to meet their GFM, Jadhav Sir, tomorrow. State that this meeting is strictly compulsory."
            f"Rule 5: End the message immediately after the 10th sentence with a final warning. DO NOT include any sign-offs, greetings, or 'Best regards'."
            f"Rule 6: Also at the end of the email write 'Zeal Attendance Section.'"
        )
    
    try:
        response = hf_client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                # Using the 'system' role sets absolute, unbreakable rules for the AI
                {"role": "system", "content": "You are a strict automated system. Follow the user's rules exactly. Never add extra commentary."},
                {"role": "user", "content": instructions}
            ],
            max_tokens=150,
            temperature=0.3 # Lowered temperature makes the AI more robotic and less likely to get creative
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return f"Dear {name},\n\nYou were marked absent today. Total absences: {previous_absences}. You must meet Jadhav Sir tomorrow compulsory."

# ==========================================
# 4. Mailjet Sending Function
# ==========================================
def send_mailjet_email(student_email, student_name, email_body):
    data = {
      'Messages': [{
          "From": {"Email": SENDER_EMAIL, "Name": SENDER_NAME},
          "To": [{"Email": student_email, "Name": student_name}],
          "Subject": "Attendance Notice: Absent Today",
          "TextPart": email_body
      }]
    }
    result = mailjet.send.create(data=data)
    return result.status_code == 200

# ==========================================
# 5. Main Processing Loop
# ==========================================
def process_absences(df):
    if df is None: return

    print(f"\n--- 🚀 Starting System for {len(df)} records ---\n")
    sent_count = 0

    for index, row in df.iterrows():
        # Handle cases where 'Status' might be empty
        status = str(row['Status']).strip().lower()
        
        if status == "absent":
            name = row['Name']
            email = row['Email']
            prev_absences = row['Previous_Absences']
            
            print(f"🤖 Drafting AI email for {name}...")
            content = generate_ai_email_body(name, prev_absences)
            
            if send_mailjet_email(email, name, content):
                print(f"✅ Sent to {name}")
                sent_count += 1
            else:
                print(f"❌ Failed to send to {name}")
            
            print("-" * 30)

    print(f"\n📊 SUMMARY REPORT:")
    print(f"Total Processed: {len(df)}")
    print(f"Emails Sent: {sent_count}")
    print("==============================\n")

if __name__ == "__main__":
    attendance_df = get_attendance_data()
    if attendance_df is not None:
        process_absences(attendance_df)
