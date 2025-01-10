import requests

url = "http://127.0.0.1:5000/add_health_rec"

# Sample FHIR health record data
data = {
    "user_id": "user1113",  # Replace with actual user ID
    "record_data": {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "fullUrl": "urn:uuid:12345678-1234-5678-1234-567812345678",
                "resource": {
                    "resourceType": "Patient",
                    "id": "12345678-1234-5678-1234-567812345678",
                    "identifier": [
                        {
                            "use": "usual",
                            "system": "http://hospital.example.org/mrn",
                            "value": "MRN12345"
                        }
                    ],
                    "name": [
                        {
                            "use": "official",
                            "family": "Doe",
                            "given": ["John"]
                        }
                    ],
                    "gender": "male",
                    "birthDate": "1985-06-15",
                    "address": [
                        {
                            "use": "home",
                            "line": ["123 Main Street"],
                            "city": "Metropolis",
                            "state": "CA",
                            "postalCode": "90210",
                            "country": "USA"
                        }
                    ]
                }
            },
            {
                "fullUrl": "urn:uuid:abcd1234-abcd-1234-abcd-1234abcd5678",
                "resource": {
                    "resourceType": "Observation",
                    "id": "abcd1234-abcd-1234-abcd-1234abcd5678",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "laboratory",
                                    "display": "Laboratory"
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "718-7",
                                "display": "Hemoglobin [Mass/volume] in Blood"
                            }
                        ],
                        "text": "Hemoglobin test"
                    },
                    "subject": {
                        "reference": "urn:uuid:12345678-1234-5678-1234-567812345678"
                    },
                    "effectiveDateTime": "2025-01-01T12:00:00Z",
                    "valueQuantity": {
                        "value": 13.5,
                        "unit": "g/dL",
                        "system": "http://unitsofmeasure.org",
                        "code": "g/dL"
                    }
                }
            },
            {
                "fullUrl": "urn:uuid:efgh5678-efgh-5678-efgh-5678efgh9012",
                "resource": {
                    "resourceType": "Condition",
                    "id": "efgh5678-efgh-5678-efgh-5678efgh9012",
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active"
                            }
                        ]
                    },
                    "verificationStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                "code": "confirmed"
                            }
                        ]
                    },
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                    "code": "problem-list-item",
                                    "display": "Problem List Item"
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "44054006",
                                "display": "Diabetes mellitus type 2"
                            }
                        ],
                        "text": "Type 2 Diabetes"
                    },
                    "subject": {
                        "reference": "urn:uuid:12345678-1234-5678-1234-567812345678"
                    },
                    "onsetDateTime": "2020-01-01"
                }
            }
        ]
    }
}

# Headers
headers = {
    "Content-Type": "application/json",
}

# Send POST request
response = requests.post(url, json=data, headers=headers)

# Print the response
print(response.status_code)
print(response.json())