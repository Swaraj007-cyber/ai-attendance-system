from huggingface_hub import InferenceClient
from mailjet_rest import Client

# ==========================================
# 1. API Configuration
# ==========================================
# Hugging Face Setup
HF_API_TOKEN = "YOUR_HUGGINGFACE_TOKEN_HERE" 

# Initialize the official Hugging Face client
hf_client = InferenceClient(api_key=HF_API_TOKEN)

# Mailjet Setup
MAILJET_API_KEY = "YOUR_MAILJET_API_KEY_HERE"
MAILJET_API_SECRET = "YOUR_MAILJET_API_SECRET_HERE"
SENDER_EMAIL = "swarajsandeepchondhe@gmail.com" # Must be verified in Mailjet!
SENDER_NAME = "College Attendance Office"

# Initialize the Mailjet client
mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')

# ==========================================
# 2. Updated Student Database (Using Emails)
# ==========================================
attendance_data = {
    "yash": {"Email": "yashhagare7@gmail.com", "Status": "Absent", "Previous_Absences": 10}
}

# ==========================================
# 3. AI Email Generator (Tiered Tone)
# ==========================================
def generate_ai_email_body(name, previous_absences):
    """Uses the Hugging Face conversational API to draft a custom email."""
    
    # 1. Decide the Tone and Instructions
    if previous_absences == 0:
        instructions = (
            f"You are a friendly college attendance assistant. Write an email to {name} "
            f"who was absent today for the very first time. Be warm and supportive. "
            f"Ask if they are feeling well and remind them to check the online portal for today's notes. "
            f"Write exactly 3 sentences. Do not include a subject line."
        )
    elif previous_absences <= 2:
        instructions = (
            f"You are a college academic advisor. Write a polite but firm email to {name}. "
            f"Inform them they were marked absent today. Explicitly state they have {previous_absences} previous absences. "
            f"Remind them that consistent attendance is crucial for passing the coursework. "
            f"Write exactly 3 sentences. Do not include a subject line."
        )
    else:
        instructions = (
            f"You are the Dean of Students. Write a serious, urgent, and professional email to {name}. "
            f"Start the email EXACTLY with 'Dear {name},' and do not invent any last names or use titles like Mr./Ms. "
            f"Inform them they were marked absent today. Highlight that they now have a critical total of {previous_absences} previous absences. "
            f"Instruct them to reply to this email immediately to schedule a mandatory meeting to discuss their academic standing. "
            f"Write exactly 4 sentences. Do not include a subject line."
        )
    
    # 2. Send to Hugging Face
    try:
        # Updated to Qwen 2.5 7B Instruct
        response = hf_client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[{"role": "user", "content": instructions}],
            max_tokens=120,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"\n⚠️ AI ERROR: {e}\n")
        return f"Dear {name},\n\nYou were marked absent today. You currently have {previous_absences} prior absences. Please contact the office."

# ==========================================
# 4. Mailjet Sending Function
# ==========================================
def send_mailjet_email(student_email, student_name, email_body):
    """Packages the AI text and sends it via Mailjet."""
    data = {
      'Messages': [
        {
          "From": {
            "Email": SENDER_EMAIL,
            "Name": SENDER_NAME
          },
          "To": [
            {
              "Email": student_email,
              "Name": student_name
            }
          ],
          "Subject": "Attendance Notice: Absent Today",
          "TextPart": email_body
        }
      ]
    }
    
    print(f"✉️ Sending email to {student_name} ({student_email})...")
    result = mailjet.send.create(data=data)
    
    if result.status_code == 200:
        print("✅ Email sent successfully!")
    else:
        print(f"❌ Failed to send email. Error: {result.status_code}")
        print(result.json())

# ==========================================
# 5. Main Processing Loop
# ==========================================
def process_absences():
    print("--- Starting AI Email Attendance System ---\n")
    
    for name, info in attendance_data.items():
        if info["Status"].lower() == "absent":
            print(f"Drafting AI email for {name}...")
            
            email_content = generate_ai_email_body(name, info["Previous_Absences"])
            send_mailjet_email(info["Email"], name, email_content)
            
            print("-" * 30)

if __name__ == "__main__":
    process_absences()
