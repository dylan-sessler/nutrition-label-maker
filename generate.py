import json
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# 1. LOAD DATA
with open('data.json', 'r') as f:
    data = json.load(f)

# 2. PROCESS INGREDIENTS (Same as before)
raw_ingredients = data['ingredients']
sorted_ingredients = sorted(raw_ingredients, key=lambda x: x['weight'], reverse=True)
ingredient_names = [item['name'] for item in sorted_ingredients]
final_string = ", ".join(ingredient_names)

# 3. RENDER HTML
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.html')

# *** UPDATE: We now pass 'n=data['nutrition']' to the template ***
html_output = template.render(
    ingredients_text=final_string,
    n=data['nutrition']
)

# 4. SAVE OUTPUT
HTML(string=html_output).write_pdf("output_label.pdf")
print("Success! Created output_label.pdf with full nutrition facts.")
