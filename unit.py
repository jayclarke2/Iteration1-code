#Deliverable: iteration 2
# Version 2.0
#Date: 14/11/2025

#Code source: Code is aided from ChatGPT 4o see Appendix A in report Iteration 1
import re

def unit_price(product):

    name = product.get("name", "").lower()
    price = float(product.get("price", 0))
    product["unit_price"] = None
    product["unit_type"] = None

    # Check for weight in grams or kilograms
    match_kg = re.search(r'(\d+(?:\.\d+)?)\s*kg', name)
    match_g = re.search(r'(\d+(?:\.\d+)?)\s*g(?![a-z])', name)

    # Check for volume in litres or millilitres
    match_l = re.search(r'(\d+(?:\.\d+)?)\s*(?:l|litres?)', name)
    match_cl = re.search(r'(\d+(?:\.\d+)?)\s*cl', name)
    match_ml = re.search(r'(\d+(?:\.\d+)?)\s*ml', name)

    if match_kg:
        weight = float(match_kg.group(1))
        if weight > 0:
            product["unit_price"] = round(price / weight, 2)
            product["unit_type"] = "kg"

    if match_g:
        weight = float(match_g.group(1)) / 1000  # Convert g to kg
        if weight > 0:
            product["unit_price"] = round(price / weight, 2)
            product["unit_type"] = "kg"

    if match_l:
        volume = float(match_l.group(1))
        if volume > 0:
            product["unit_price"] = round(price / volume, 2)
            product["unit_type"] = "L"

    if match_ml:
        volume = float(match_ml.group(1)) / 1000  # Convert ml to L
        if volume > 0:
            product["unit_price"] = round(price / volume, 2)
            product["unit_type"] = "L"

    if match_cl:
        volume = float(match_cl.group(1)) / 100  # convert cl → L
        if volume > 0:
            product["unit_price"] = round(price / volume, 2)
            product["unit_type"] = "L"

    return product

#end of code block for iteration 2 deliverable
