import json
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# --- SECTION 1: LOAD DATA ---
# We open the JSON file and load it into a Python dictionary.
with open('data.json', 'r') as f:
    data = json.load(f)

# --- SECTION 2: PROCESS DATA ---
# This is the "logic" layer.
# 1. We grab the list of ingredients.
raw_ingredients = data['ingredients']

# 2. We SORT them by weight (descending), as required by food law.
#    'lambda x: x['weight']' tells Python to sort based on the number in the 'weight' key.
sorted_ingredients = sorted(raw_ingredients, key=lambda x: x['weight'], reverse=True)

# 3. We extract just the names into a clean list.
ingredient_names = [item['name'] for item in sorted_ingredients]

# 4. We join them into a single string separated by commas.
#    Example: "Rolled oats, carrot, potato..."
final_string = ", ".join(ingredient_names)

# --- SECTION 3: RENDER HTML ---
# We set up Jinja2 to look for templates in the current folder ('.').
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.html')

# We 'render' the template, passing our 'final_string' into the
# 'ingredients_text' placeholder we defined in the HTML file.
html_output = template.render(ingredients_text=final_string)

# --- SECTION 4: SAVE OUTPUT ---
# WeasyPrint takes the rendered HTML and saves it as a PDF.
HTML(string=html_output).write_pdf("output_label.pdf")

print("Success! Created output_label.pdf")
