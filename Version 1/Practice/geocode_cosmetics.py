import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep

# Manually add companies (or load from your CSV later)
companies = [
    "New Avon LLC", "J. Strickland & Co.", "CHANEL, INC",
    "Revlon Consumer Product Corporation", "Dermalogica"
]

geolocator = Nominatim(user_agent="cosmetic_mapper")
results = []

for company in companies:
    try:
        location = geolocator.geocode(company)
        if location:
            results.append({
                "Company": company,
                "Latitude": location.latitude,
                "Longitude": location.longitude,
                "Address": location.address
            })
        else:
            results.append({
                "Company": company,
                "Latitude": None,
                "Longitude": None,
                "Address": "Not found"
            })
        sleep(1)
    except Exception as e:
        print(f"Error geocoding {company}: {e}")

df = pd.DataFrame(results)
df.to_csv("geocoded_companies.csv", index=False)
print("Saved geocoded data to 'geocoded_companies.csv'")
