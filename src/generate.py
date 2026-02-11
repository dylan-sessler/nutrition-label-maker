import json
import os
import copy
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# --- SETUP ---
output_dir = "output_labels"
os.makedirs(output_dir, exist_ok=True)

# Get current path for fonts
project_path = "file://" + os.path.abspath(os.getcwd())

# --- CONFIGURATION ---
SALT_VARIANTS = {
    "noSalt": 0,
    "standardSalt": 614,
    "highSalt": 1228
}
SODIUM_DV_BASE = 2300

# --- LOAD DATA ---
# Note: We now expect a LIST of recipes, not just one object
with open('src/data.json', 'r') as f:
    recipes_list = json.load(f)

# --- TEMPLATE SETUP ---
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('src/template.html')

# --- MAIN LOOP ---
for recipe in recipes_list:
    r_name = recipe.get('recipe_name', 'Unknown')
    print(f"--- Processing: {r_name} ---")

    try:
        # 1. PROCESS INGREDIENTS
        raw_ingredients = recipe['ingredients']
        # Sort by weight descending
        sorted_ingredients = sorted(raw_ingredients, key=lambda x: x.get('weight', 0), reverse=True)
        ingredient_names = [item['name'] for item in sorted_ingredients]
        final_ingredients_text = ", ".join(ingredient_names)

        # 2. DETERMINE VARIANTS
        # Check the boolean flag in the recipe config
        if recipe.get('config', {}).get('has_salt_variants', False):
            active_salt_levels = ["noSalt", "standardSalt", "highSalt"]
        else:
            active_salt_levels = ["noSalt"]

        # 3. GENERATE LABEL MATRIX
        for servings in [5, 24, 48]:
            for salt_type in active_salt_levels:

                # Copy nutrition data to avoid modifying the original
                variant_nutrition = copy.deepcopy(recipe['nutrition'])

                # A. Update Servings
                variant_nutrition['servings_per_container'] = servings

                # B. Update Sodium (if salt is added)
                # We only add sodium if it's NOT 'noSalt'
                if salt_type != "noSalt":
                    added_sodium = SALT_VARIANTS[salt_type]
                    total_sodium = variant_nutrition.get('sodium_mg', 0) + added_sodium
                    variant_nutrition['sodium_mg'] = total_sodium

                    # Recalc DV%
                    new_dv = (total_sodium / SODIUM_DV_BASE) * 100
                    variant_nutrition['sodium_dv'] = round(new_dv)

                # C. Render
                safe_name = r_name.replace(" ", "_")
                filename = f"{safe_name}_{servings}sv_{salt_type}.pdf"
                full_path = os.path.join(output_dir, filename)

                html_output = template.render(
                    ingredients_text=final_ingredients_text,
                    n=variant_nutrition,
                    font_path=project_path
                )

                HTML(string=html_output).write_pdf(full_path)
                print(f"  -> Created {filename}")

    except Exception as e:
        print(f"  ERROR processing {r_name}: {e}")

print(f"\nAll done! Check the '{output_dir}' folder.")
