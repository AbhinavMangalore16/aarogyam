def format_records(records):
    """
    Format a list of records into human-readable text.
    """
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
    """
    Format individual resources like Patient, Observation, or Condition.
    """
    resource_type = resource.get('resourceType', 'Unknown')
    if resource_type == 'Patient':
        return (f"Patient Name: {resource.get('name', [{}])[0].get('given', [''])[0]} "
                f"{resource.get('name', [{}])[0].get('family', '')}, "
                f"Gender: {resource.get('gender', 'Unknown')}, "
                f"Birth Date: {resource.get('birthDate', 'Unknown')}")
    elif resource_type == 'Observation':
        return (f"Observation: {resource.get('code', {}).get('text', 'Unknown')}, "
                f"Value: {resource.get('valueQuantity', {}).get('value', 'N/A')} "
                f"{resource.get('valueQuantity', {}).get('unit', '')}, "
                f"Effective Date: {resource.get('effectiveDateTime', 'Unknown')}")
    elif resource_type == 'Condition':
        return (f"Condition: {resource.get('code', {}).get('text', 'Unknown')}, "
                f"Status: {resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'Unknown')}, "
                f"Onset Date: {resource.get('onsetDateTime', 'Unknown')}")
    elif resource_type == 'Medication':
        return (f"Medication: {resource.get('medicationCodeableConcept', {}).get('text', 'Unknown')}, "
                f"Status: {resource.get('status', 'Unknown')}")
    elif resource_type == 'Encounter':
        return (f"Encounter Class: {resource.get('class', {}).get('code', 'Unknown')}, "
                f"Start Date: {resource.get('period', {}).get('start', 'Unknown')}, "
                f"End Date: {resource.get('period', {}).get('end', 'Unknown')}")
    else:
        return f"Unknown Resource Type: {resource_type}"
