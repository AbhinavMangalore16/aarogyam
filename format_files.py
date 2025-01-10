def format_records(records):
    formatted = []
    for record in records:
        resource_type = record.get('resourceType', 'Unknown')
        if resource_type == 'Bundle':
            # Handle Bundle resources by formatting each entry
            for entry in record.get('entry', []):
                resource = entry.get('resource', {})
                formatted.append(format_individual_resource(resource))
        else:
            formatted.append(format_individual_resource(record))
    return formatted

def format_individual_resource(resource):
    resource_type = resource.get('resourceType', 'Unknown')
    
    if resource_type == 'Patient':
        return (f"Patient Name: {resource.get('name', [{}])[0].get('given', [''])[0]} "
                f"{resource.get('name', [{}])[0].get('family', '')}, "
                f"Gender: {resource.get('gender', 'Unknown')}, "
                f"Birth Date: {resource.get('birthDate', 'Unknown')}")
    
    elif resource_type == 'Observation':
        observations = resource.get('code', {}).get('coding', [])
        observation_details = []
        for obs in observations:
            obs_text = obs.get('display', 'Unknown')
            obs_code = obs.get('code', 'Unknown')
            obs_system = obs.get('system', 'Unknown')
            obs_link = f"http://{obs_system}/{obs_code}" if obs_code != 'Unknown' else ''
            observation_details.append(f"{obs_text} (Code: {obs_code}, Link: {obs_link})")
        
        value_quantity = resource.get('valueQuantity', {})
        value = value_quantity.get('value', 'N/A')
        unit = value_quantity.get('unit', '')
        effective_date = resource.get('effectiveDateTime', 'Unknown')
        
        return (f"Observations: {', '.join(observation_details)}, "
                f"Value: {value} {unit}, Effective Date: {effective_date}")
    
    elif resource_type == 'Condition':
        conditions = resource.get('code', {}).get('coding', [])
        condition_details = []
        for cond in conditions:
            cond_display = cond.get('display', 'Unknown')
            cond_code = cond.get('code', 'Unknown')
            cond_system = cond.get('system', 'Unknown')
            cond_link = f"http://{cond_system}/{cond_code}" if cond_code != 'Unknown' else ''
            condition_details.append(f"{cond_display} (Code: {cond_code}, Link: {cond_link})")
        
        clinical_status = resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'Unknown')
        onset_date = resource.get('onsetDateTime', 'Unknown')
        
        return (f"Conditions: {', '.join(condition_details)}, "
                f"Status: {clinical_status}, Onset Date: {onset_date}")
    
    elif resource_type == 'Medication':
        medications = resource.get('code', {}).get('coding', [])
        medication_details = []
        for med in medications:
            med_display = med.get('display', 'Unknown')
            med_code = med.get('code', 'Unknown')
            med_system = med.get('system', 'Unknown')
            med_link = f"http://{med_system}/{med_code}" if med_code != 'Unknown' else ''
            medication_details.append(f"{med_display} (Code: {med_code}, Link: {med_link})")
        return (f"Medications: {', '.join(medication_details)}, "
                f"Status: {resource.get('status', 'Unknown')}")
    
    elif resource_type == 'Encounter':
        encounters = resource.get('class', {}).get('coding', [])
        encounter_details = []
        for enc in encounters:
            enc_code = enc.get('code', 'Unknown')
            enc_display = enc.get('display', 'Unknown')
            enc_link = f"http://terminology.hl7.org/CodeSystem/encounter-class/{enc_code}" if enc_code != 'Unknown' else ''
            encounter_details.append(f"{enc_display} (Code: {enc_code}, Link: {enc_link})")
        
        period = resource.get('period', {})
        start_date = period.get('start', 'Unknown')
        end_date = period.get('end', 'Unknown')
        
        return (f"Encounters: {', '.join(encounter_details)}, "
                f"Start Date: {start_date}, End Date: {end_date}")
    
    else:
        return f"Unknown Resource Type: {resource_type}"
