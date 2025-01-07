from fastapi import FastAPI, HTTPException
import requests
import csv
import json
from mangum import Mangum  # Required for AWS Lambda compatibility

# Initialize the FastAPI app
app = FastAPI()

# URL for PHQ-9 Google Sheet (exported as CSV)
PHQ9_URL = "https://docs.google.com/spreadsheets/d/1D312sgbt_nOsT668iaUrccAzQ3oByUT0peXS8LYL5wg/export?format=csv"

# Mapping for PHQ-9 responses
response_mapping = {
    "Not at all": 0,
    "Several Days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

# Interpretations for PHQ-9 scores
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

# Endpoint to check if the API is running
@app.get("/")
def root():
    return {"message": "PHQ-9 Tool API is running."}

# Endpoint for analyzing PHQ-9 data
@app.get("/analyze")
def analyze_phq9(client_name: str):
    try:
        # Fetch data from Google Sheets
        response = requests.get(PHQ9_URL)
        response.raise_for_status()
        data = response.text.splitlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PHQ-9 data: {e}")

    try:
        # Parse CSV data
        reader = csv.reader(data)
        header = next(reader)  # Skip header row

        for row in reader:
            name = row[-1].strip()  # Name is in the last column
            if name.lower() == client_name.lower():
                responses = row[1:-2]  # Extract responses (adjust indexes as needed)
                total_score = sum(response_mapping.get(r.strip(), 0) for r in responses)
                interpretation = get_phq9_interpretation(total_score)

                # Primary Impression
                primary_impression = (
                    "The client may have mild or no mental health concerns."
                    if interpretation in ["Minimal or none (0-4)", "Mild (5-9)"]
                    else "The client might be experiencing more significant mental health concerns."
                )

                # Additional Impressions and Suggested Tools
                additional_impressions = []
                suggested_tools = []

                if interpretation not in ["Minimal or none (0-4)", "Mild (5-9)"]:
                    additional_impressions = [
                        "The client might be experiencing Depression.",
                        "Physical symptoms could be affecting the client.",
                        "The client's overall well-being might need attention."
                    ]
                    suggested_tools = [
                        "Tools for Depression",
                        "Tools for Physical Symptoms",
                        "Tools for Well-Being"
                    ]

                # Return the analysis result
                return {
                    "client_name": client_name,
                    "total_score": total_score,
                    "interpretation": interpretation,
                    "primary_impression": primary_impression,
                    "additional_impressions": additional_impressions,
                    "suggested_tools": suggested_tools,
                }

        # Client not found
        raise HTTPException(status_code=404, detail=f"Client '{client_name}' not found.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PHQ-9 data: {e}")

# Define the handler for Vercel
handler = Mangum(app)
