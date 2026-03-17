import requests
from mailjet_rest import Client

# ==========================================
# 1. API Configuration
# ==========================================
# Hugging Face Setup
HF_API_TOKEN = "YOUR_HUGGING_FACE_TOKEN_HERE" 
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

# Mailjet Setup
MAILJET_API_KEY = "YOUR_MAILJET_API_KEY_HERE"
MAILJET_API_SECRET = "YOUR_MAILJET_SECRET_KEY_HERE"
SENDER_EMAIL = "swarajsandeepchondhe@gmail.com" # Must be verified in Mailjet!
SENDER_NAME = "College Attendance Office"

# Initialize the Mailjet client
mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')

# ==========================================
# 2. Updated Student Database (Using Emails)
# ==========================================
attendance_data = {
    "Indrajeet Sunil Hagare": {"Email": "yashhagare7@gmail.com", "Status": "Absent", "Previous_Absences": 10},
    "Diksha": {"Email": "shetediksha10@gmail.com", "Status": "Absent", "Previous_Absences": 2},
    "Swaraj": {"Email": "swarajsandeepchondhe@gmail.com", "Status": "Absent", "Previous_Absences": 5}
}

# ==========================================
# 3. AI Email Generator
# ==========================================
def generate_ai_email_body(name, previous_absences):
    """Uses Hugging Face to draft a professional email about the absence."""
    prompt = (
        f"[INST] You are an automated college attendance system. Write a short, professional email "
        f"to a student named {name}. Inform them they were marked absent today. "
        f"Mention they have {previous_absences} previous absences on record. "
        f"Ask them to contact their professor if they need to catch up. Do not include a subject line. [/INST]"
    )
    
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 80, "temperature": 0.7, "return_full_text": False}
    }
    
    try:
        response = requests.post(HF_API_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            return response.json()[0]['generated_text'].strip()
        else:
            return f"Dear {name},\n\nYou were marked absent today. You currently have {previous_absences} prior absences. Please ensure you catch up on any missed work.\n\nBest,\nAttendance Office"
    except Exception:
        return f"Dear {name},\n\nYou were marked absent today. You have {previous_absences} prior absences."

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
            
            # 1. Generate the text using Hugging Face
            email_content = generate_ai_email_body(name, info["Previous_Absences"])
            
            # 2. Send the text using Mailjet
            send_mailjet_email(info["Email"], name, email_content)
            print("-" * 30)

if __name__ == "__main__":
    process_absences()