from fastapi import FastAPI, HTTPException
import requests
import csv
from mangum import Mangum  # Required for AWS Lambda compatibility

# Initialize the FastAPI app
app = FastAPI()

PHQ9_URL = "https://docs.google.com/spreadsheets/d/1D312sgbt_nOsT668iaUrccAzQ3oByUT0peXS8LYL5wg/export?format=csv"

response_mapping = {
    "Not at all": 0,
    "Several Days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

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

@app.get("/analyze")
def analyze_phq9(client_name: str):
    try:
        response = requests.get(PHQ9_URL)
        response.raise_for_status()
        data = response.text.splitlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PHQ-9 data: {e}")

    try:
        reader = csv.reader(data)
        header = next(reader)

        for row in reader:
            name = row[-1].strip()
            if name.lower() == client_name.lower():
                responses = row[1:-2]
                total_score = sum(response_mapping.get(r.strip(), 0) for r in responses)
                interpretation = get_phq9_interpretation(total_score)

                return {
                    "client_name": client_name,
                    "total_score": total_score,
                    "interpretation": interpretation,
                }
        raise HTTPException(status_code=404, detail=f"Client '{client_name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PHQ-9 data: {e}")

handler = Mangum(app)
