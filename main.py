from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
import requests
import csv
import json
import random
from mangum import Mangum  # Required for AWS Lambda compatibility

# Initialize the FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (use specific origins in production for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all HTTP headers
)

PHQ9_URL = "https://docs.google.com/spreadsheets/d/1D312sgbt_nOsT668iaUrccAzQ3oByUT0peXS8LYL5wg/export?format=csv"

response_mapping = {
    "Not at all": 0,
    "Several Days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

# Load phrases for PHQ-9 impressions
with open("phrases_phq9.json", "r") as f:
    phrases = json.load(f)

def get_random_phrase(condition, used_phrases):
    available_phrases = [p for p in phrases[condition] if p not in used_phrases]
    if available_phrases:
        phrase = random.choice(available_phrases)
        used_phrases.add(phrase)
        return phrase
    else:
        return "No more unique phrases available."

def get_phq9_interpretation(score):
    if score <= 4:
        return "Minimal or none (0-4)"
    elif score <= 9:
        return "Mild (5-9)"
    elif score <= 14:
        return "Moderate (10-14)"
    elif score <= 19:
        return "Moderately severe (15-19)"
    else:
        return "Severe (20-27)"

@app.get("/")
def root():
    return {"message": "PHQ-9 Tool API is running."}

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok", "message": "PHQ-9 Tool API is running and accessible."}

@app.get("/analyze")
def analyze_phq9(first_name: str, last_name: str, middle_name: str = "", suffix: str = ""):
    try:
        response = requests.get(PHQ9_URL)
        response.raise_for_status()
        data = response.text.splitlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PHQ-9 data: {e}")

    # Construct full name using the logic from your accessor
    client_full_name = f"{first_name} {middle_name} {last_name}".strip() + (f", {suffix}" if suffix else "")

    try:
        reader = csv.reader(data)
        header = next(reader)
        used_phrases = set()

        for row in reader:
            name = row[-1].strip()  # Assuming the name is in the last column
            if name.lower() == client_full_name.lower():
                responses = row[1:-2]
                total_score = sum(response_mapping.get(r.strip(), 0) for r in responses)
                interpretation = get_phq9_interpretation(total_score)

                primary_impression = (
                    f"Based on the results, it seems that {client_full_name} is experiencing {interpretation.lower()}. "
                    "This suggests that their current mental health state is within this range."
                    if interpretation in ["Minimal or none (0-4)", "Mild (5-9)"]
                    else f"The results indicate that {client_full_name} may be dealing with {interpretation.lower()}. This might require further attention or professional consultation."
                )

                additional_impressions = []

                if interpretation not in ["Minimal or none (0-4)", "Mild (5-9)"]:
                    additional_impressions = [
                        get_random_phrase("Depression", used_phrases),
                        get_random_phrase("Physical Symptoms", used_phrases),
                        get_random_phrase("Well-Being", used_phrases),
                    ]

                return {
                    "client_full_name": client_full_name,
                    "total_score": total_score,
                    "interpretation": interpretation,
                    "primary_impression": primary_impression,
                    "additional_impressions": additional_impressions,
                }

        raise HTTPException(status_code=404, detail=f"Client '{client_full_name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PHQ-9 data: {e}")


handler = Mangum(app)
