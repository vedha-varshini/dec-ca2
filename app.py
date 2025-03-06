import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# APILayer Spoonacular API setup
API_KEY = "MO8WCqkoWYxeO0Us32eOWPAQFqFkTo8a"
BASE_URL = "https://api.apilayer.com/spoonacular"
HEADERS = {
    "Content-Type": "application/json",
    "apikey": API_KEY
}


# Home route
@app.route('/')
def home():
    return render_template('index.html')


# Find recipes by ingredients
@app.route('/recipes/by-ingredients', methods=['POST'])
def recipes_by_ingredients():
    ingredients = request.json.get('ingredients') if request.is_json else request.form.get('ingredients')
    if not ingredients:
        return jsonify({"error": "Ingredients required"}), 400

    url = f"{BASE_URL}/recipes/complexSearch"
    # Start with minimal parameters to ensure functionality
    params = {
        "includeIngredients": ingredients,
        "number": 5  # Basic pagination
    }
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get('results'):
            return jsonify({"error": f"No recipes found for ingredients: {ingredients}"}), 404

        formatted_results = []
        for recipe in data.get('results', []):
            formatted_recipe = {
                "Title": recipe.get('title', 'Unknown Recipe'),
                "Image": recipe.get('image', 'No image available'),
                "Used Ingredients": [
                    f"{ing['name']} ({ing['amount']} {ing['unit']})"
                    for ing in recipe.get('usedIngredients', [])
                ] if 'usedIngredients' in recipe else ["Data unavailable"],
                "Missed Ingredients": [
                    f"{ing['name']} ({ing['amount']} {ing['unit']})"
                    for ing in recipe.get('missedIngredients', [])
                ] if 'missedIngredients' in recipe else ["Data unavailable"],
                "ID": recipe.get('id', 'N/A')
            }
            formatted_results.append(formatted_recipe)

        formatted_output = {
            "Total Recipes Found": data.get('totalResults', 0),
            "Recipes": formatted_results
        }
        return jsonify(formatted_output)
    except requests.exceptions.HTTPError as e:
        return jsonify({
            "error": f"Server error: {str(e)}. Check your API quota in the APILayer dashboard or contact support. URL: {response.url}"
        }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}. Verify your internet connection or API key."}), 500


# Find recipes by nutritional requirements (Disabled due to 500 errors)
@app.route('/recipes/by-nutrients', methods=['POST'])
def recipes_by_nutrients():
    return jsonify({
        "error": "Nutritional filtering is currently unavailable due to server errors. Check your Free Plan limits or contact APILayer support."
    }), 503


# Extract recipe from webpage
@app.route('/recipes/extract', methods=['POST'])
def extract_recipe():
    url_input = request.json.get('url') if request.is_json else request.form.get('url')
    if not url_input:
        return jsonify({"error": "URL required"}), 400

    url = f"{BASE_URL}/recipes/extract"
    params = {"url": url_input}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        formatted_output = {
            "Title": data.get('title', 'Unknown Recipe'),
            "Source URL": data.get('sourceUrl', url_input),
            "Ingredients": [ing.get('original', 'N/A') for ing in data.get('extendedIngredients', [])],
            "Instructions": [step.get('step', 'N/A') for step in
                             data.get('analyzedInstructions', [{}])[0].get('steps', [])],
            "Image": data.get('image', 'No image available')
        }
        return jsonify(formatted_output)
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Server error: {str(e)}. This feature may be limited in your Free Plan."}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500


# Generate a meal plan (Disabled due to 404 error)
@app.route('/meal-plan', methods=['POST'])
def generate_meal_plan():
    return jsonify({
        "error": "Meal planning is not available in your Free Plan. Verify the endpoint in your APILayer dashboard or upgrade."
    }), 503


# Generate a shopping list
@app.route('/shopping-list', methods=['POST'])
def generate_shopping_list():
    ingredients = request.json.get('ingredients') if request.is_json else request.form.get('ingredients')
    if not ingredients:
        return jsonify({"error": "Ingredients required"}), 400

    url = f"{BASE_URL}/recipes/parseIngredients"
    params = {
        "ingredientList": ingredients,
        "servings": 1
    }
    try:
        response = requests.post(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        formatted_items = []
        for item in data:
            formatted_item = {
                "Name": item.get('name', 'Unknown Ingredient'),
                "Amount": f"{item.get('amount', 'N/A')} {item.get('unit', '')}",
                "Aisle": item.get('aisle', 'N/A')
            }
            formatted_items.append(formatted_item)

        formatted_output = {
            "Servings": 1,
            "Shopping List": formatted_items
        }
        return jsonify(formatted_output)
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Server error: {str(e)}. This feature may be limited in your Free Plan."}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500


# Classify recipe type or cuisine
@app.route('/recipes/classify', methods=['POST'])
def classify_recipe():
    data = request.json if request.is_json else request.form
    recipe_id = data.get('recipe_id')
    if not recipe_id:
        return jsonify({"error": "Recipe ID required"}), 400

    url = f"{BASE_URL}/recipes/{recipe_id}/information"
    params = {"includeNutrition": False}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        cuisines = data.get('cuisines', [])
        dish_types = data.get('dishTypes', [])

        formatted_output = {
            "Recipe Title": data.get('title', 'Unknown Recipe'),
            "Cuisine": cuisines[0] if cuisines else 'N/A',
            "Dish Type": dish_types[0] if dish_types else 'N/A',
            "ID": data.get('id', 'N/A')
        }
        return jsonify(formatted_output)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
