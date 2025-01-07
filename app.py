from fastapi import FastAPI
import requests
import csv
import json

app = FastAPI()

PHQ9_URL = "https://docs.google.com/spreadsheets/d/1D312sgbt_nOsT668iaUrccAzQ3oByUT0peXS8LYL5wg/export?format=csv"

response_mapping = {
    "Not at all": 0,
    "Several Days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

def get_random_phrase(condition):
    with open("phrases_phq9.json", "r") as f:
        phrases = json.load(f)
    return random.choice(phrases[condition])

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

@app.get("/analyze")
def analyze_phq9(client_name: str):
    response = requests.get(PHQ9_URL)
    response.raise_for_status()
    data = response.text.splitlines()

    reader = csv.reader(data)
    header = next(reader)  # Skip header row

    for row in reader:
        name = row[-1].strip()
        if name.lower() == client_name.lower():
            responses = row[1:-2]
            total_score = sum(response_mapping.get(r.strip(), 0) for r in responses)
            interpretation = get_phq9_interpretation(total_score)

            primary_impression = (
                "The client may have mild or no mental health concerns."
                if interpretation in ["Minimal or none (0-4)", "Mild (5-9)"]
                else "The client might be experiencing more significant mental health concerns."
            )

            additional_impressions = []
            suggested_tools = []

            if interpretation not in ["Minimal or none (0-4)", "Mild (5-9)"]:
                additional_impressions = [
                    get_random_phrase("Depression"),
                    get_random_phrase("Physical Symptoms"),
                    get_random_phrase("Well-Being"),
                ]
                suggested_tools = [
                    "Tools for Depression",
                    "Tools for Physical Symptoms",
                    "Tools for Well-Being",
                ]

            return {
                "client_name": client_name,
                "total_score": total_score,
                "interpretation": interpretation,
                "primary_impression": primary_impression,
                "additional_impressions": additional_impressions,
                "suggested_tools": suggested_tools,
            }

    return {"error": f"Client '{client_name}' not found."}
