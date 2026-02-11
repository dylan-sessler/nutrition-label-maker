import json
import os
import copy
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# --- SETUP ---
output_dir = "output_labels"
os.makedirs(output_dir, exist_ok=True)
project_path = "file://" + os.path.abspath(os.getcwd())

# --- CONFIGURATION ---
SODIUM_DV_BASE = 2300

# SALT PROFILES
# "sodium_mg": Added to the Nutrition Facts (Per Serving)
# "salt_g_per_48_servings": The actual weight of salt added to a full batch
SALT_VARIANTS = {
    "noSalt": {
        "sodium_mg": 0,
        "salt_g_per_48_servings": 0
    },
    "standardSalt": {
        "sodium_mg": 614,
        "salt_g_per_48_servings": 76
    },
    "highSalt": {
        "sodium_mg": 1228,
        "salt_g_per_48_servings": 152
    }
}

# --- LOAD DATA ---
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
        # 1. GET BASE INGREDIENTS
        base_ingredients = recipe.get('ingredients', [])

        # 2. DETERMINE SALT LEVELS
        if recipe.get('config', {}).get('has_salt_variants', False):
            active_salt_levels = ["noSalt", "standardSalt", "highSalt"]
        else:
            active_salt_levels = ["noSalt"]

        # 3. GENERATE VARIANTS
        for servings_display in [5, 24, 48]:
            for salt_type in active_salt_levels:

                # --- A. PREPARE NUTRITION DATA ---
                variant_nutrition = copy.deepcopy(recipe['nutrition'])
                variant_nutrition['servings_per_container'] = servings_display

                salt_data = SALT_VARIANTS[salt_type]

                # Update Sodium (Per Serving)
                added_sodium = salt_data['sodium_mg']
                current_sodium = variant_nutrition.get('sodium_mg', 0)
                total_sodium = current_sodium + added_sodium
                variant_nutrition['sodium_mg'] = total_sodium

                # Update DV%
                new_dv = (total_sodium / SODIUM_DV_BASE) * 100
                variant_nutrition['sodium_dv'] = round(new_dv)

                # --- B. PREPARE INGREDIENT LIST ---
                current_ingredients_list = copy.deepcopy(base_ingredients)

                # Use the hard-coded batch weight directly
                total_salt_weight_g = salt_data['salt_g_per_48_servings']

                # Add Salt to list if weight > 0
                if total_salt_weight_g > 0:
                    current_ingredients_list.append({
                        "name": "salt",
                        "weight": total_salt_weight_g
                    })

                # SORT by weight (Descending)
                # Includes the fix for 'null' weights: (x.get('weight') or 0)
                sorted_ingredients = sorted(
                    current_ingredients_list,
                    key=lambda x: (x.get('weight') or 0),
                    reverse=True
                )

                # Generate string
                final_ingredients_text = ", ".join([item['name'] for item in sorted_ingredients])

                # --- C. RENDER ---
                safe_name = r_name.replace(" ", "_").replace("(", "").replace(")", "")
                filename = f"{safe_name}_{servings_display}sv_{salt_type}.pdf"
                full_path = os.path.join(output_dir, filename)

                html_output = template.render(
                    ingredients_text=final_ingredients_text,
                    n=variant_nutrition,
                    font_path=project_path
                )

                HTML(string=html_output).write_pdf(full_path)

    except Exception as e:
        print(f"  ERROR processing {r_name}: {e}")

print(f"\nAll done! Check the '{output_dir}' folder.")
