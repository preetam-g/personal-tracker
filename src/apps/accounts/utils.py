

def serialize_form_data(form_data: dict) -> dict:
    data = {}

    for key, value in form_data.items():

        if value is None:
            continue

        if hasattr(value, 'pk'):
            data[key] = value.pk
        else:
            data[key] = value

    return data