import json
import os
import copy  # Needed to duplicate the nutrition data for each variant
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# --- SETUP ---
# Create an output folder so we don't clutter the main directory
output_dir = "output_labels"
os.makedirs(output_dir, exist_ok=True)

# Get current path for fonts
project_path = "file://" + os.path.abspath(os.getcwd())

# --- CONFIGURATION ---
# The Sodium variants (in mg)
SALT_VARIANTS = {
    "noSalt": 0,
    "standardSalt": 614,
    "highSalt": 1228
}

# The Standard Daily Value for Sodium (used for % calc)
# FDA Standard is 2300mg
SODIUM_DV_BASE = 2300

# --- LOAD DATA ---
with open('src/data.json', 'r') as f:
    data = json.load(f)

# --- PROCESS INGREDIENTS ---
# This is constant for all labels
raw_ingredients = data['ingredients']
sorted_ingredients = sorted(raw_ingredients, key=lambda x: x['weight'], reverse=True)
ingredient_names = [item['name'] for item in sorted_ingredients]
final_ingredients_text = ", ".join(ingredient_names)

# --- TEMPLATE SETUP ---
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('src/template.html')

# --- GENERATION LOOP ---
# 1. Determine which salt levels to generate
if data['config']['has_salt_variants']:
    active_salt_levels = ["noSalt", "standardSalt", "highSalt"]
else:
    active_salt_levels = ["noSalt"] # Default if no variants

# 2. Loop through Servings (5, 24, 48)
for servings in [5, 24, 48]:

    # 3. Loop through Salt Levels
    for salt_type in active_salt_levels:

        # Create a fresh copy of the base nutrition so we don't mess up the original
        # 'copy.deepcopy' ensures nested objects are also safe
        variant_nutrition = copy.deepcopy(data['nutrition'])

        # --- APPLY VARIANTS ---

        # A. Update Servings
        variant_nutrition['servings_per_container'] = servings

        # B. Update Sodium (Base + Added)
        added_sodium = SALT_VARIANTS[salt_type]
        total_sodium = variant_nutrition['sodium_mg'] + added_sodium

        variant_nutrition['sodium_mg'] = total_sodium

        # C. Recalculate Sodium % Daily Value
        # Formula: (Total / 2300) * 100
        new_dv = (total_sodium / SODIUM_DV_BASE) * 100
        variant_nutrition['sodium_dv'] = round(new_dv)

        # --- RENDER & SAVE ---

        # Create a clean filename: "Low_FODMAP_Mush_24_standardSalt.pdf"
        safe_name = data['recipe_name'].replace(" ", "_")
        filename = f"{safe_name}_{servings}sv_{salt_type}.pdf"
        full_path = os.path.join(output_dir, filename)

        html_output = template.render(
            ingredients_text=final_ingredients_text,
            n=variant_nutrition,
            font_path=project_path
        )

        HTML(string=html_output).write_pdf(full_path)
        print(f"Generated: {filename} (Sodium: {total_sodium}mg / {variant_nutrition['sodium_dv']}%)")

print(f"\nAll done! Check the '{output_dir}' folder.")
