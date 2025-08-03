// Defining a data model.
class DietaryPrefEvalResult {
  dietary_preference string
  reasoning string
  result bool @description(#"Whether the chatbot followed the user's dietary preferences."#)
}

// Create a function to extract the resume from a string.
function EvalDietaryPrefs(query: string, preference: string, response: string) -> DietaryPrefEvalResult {
  client "openai/gpt-4.1"
  prompt #"
    You are a quality control analyst helping review conversations between a user and a recipe chatbot.

    Your job is to identify whether or not the chatbot follows the user's dietary preferences.

    Dietrary preferences are defined as follows:
    - Vegan: No animal products (meat, dairy, eggs, honey, etc.)
    - Vegetarian: No meat or fish, but dairy and eggs are allowed
    - Gluten-free: No wheat, barley, rye, or other gluten-containing grains
    - Dairy-free: No milk, cheese, butter, yogurt, or other dairy products
    - Keto: Very low carb (typically <20g net carbs), high fat, moderate protein
    - Paleo: No grains, legumes, dairy, refined sugar, or processed foods
    - Pescatarian: No meat except fish and seafood
    - Kosher: Follows Jewish dietary laws (no pork, shellfish, mixing meat/dairy)
    - Halal: Follows Islamic dietary laws (no pork, alcohol, proper slaughter)
    - Nut-free: No tree nuts or peanuts
    - Low-carb: Significantly reduced carbohydrates (typically <50g per day)
    - Sugar-free: No added sugars or high-sugar ingredients
    - Raw vegan: Vegan foods not heated above 118°F (48°C)
    - Whole30: No grains, dairy, legumes, sugar, alcohol, or processed foods
    - Diabetic-friendly: Low glycemic index, controlled carbohydrates
    - Low-sodium: Reduced sodium content for heart health

    You will be given a query, a preference, and a response.

    The query is the user's request for a recipe.
    The preference is the user's dietary preference.
    The response is the chatbot's response to the user's request.
    <Query>
    {{ query }}
    </Query>
    <Preference>
    {{ preference }}
    </Preference>
    <Response>
    {{ response }}
    </Response>  
   {{ ctx.output_format }}
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test eval_dietary_prefs {
  functions [EvalDietaryPrefs]
  args {
    query #"
      I'm vegan but I really want to make something with honey - is there a good substitute? i am craving a yogurt breakfast.
    "#
    preference #"
      Vegan
    "#
    response #"
      Certainly! For a vegan yogurt breakfast that mimics the sweetness and texture honey provides, I recommend using agave syrup or maple syrup as a natural, plant-based substitute. Both will add a lovely sweetness without compromising your vegan diet.

      Here's a delicious Vegan Coconut & Berry Yogurt Parfait for 2 people:

      ### Ingredients:
      - 2 cups vegan coconut or almond yogurt
      - 1 cup mixed fresh berries (blueberries, strawberries, or raspberries)
      - 1/4 cup granola (preferably vegan and gluten-free if needed)
      - 2 tablespoons agave syrup or pure maple syrup
      - 1 teaspoon vanilla extract (optional)
      - A few fresh mint leaves for garnish (optional)

      ### Instructions:

      1. **Prepare the Sweetened Yogurt:**
        - In a small bowl, combine the vegan yogurt with 1 tablespoon of agave syrup or maple syrup.
        - Add the vanilla extract if using and stir well until the syrup is fully incorporated.
        - Taste and adjust sweetness if needed—add a little more syrup if you prefer it sweeter.

      2. **Assemble the Parfaits:**
        - Take two glasses or jars and start by spooning a layer of the sweetened yogurt into the bottom of each.
        - Add a layer of mixed berries on top of the yogurt layer.
        - Sprinkle a layer of granola over the berries.
        - Repeat the layers until the glasses are filled, finishing with berries and a sprinkle of granola on top.

      3. **Garnish and Serve:**
        - Add a mint leaf on top for a fresh touch.
        - Serve immediately for the crunchiest granola, or cover and refrigerate for up to an hour if you prefer it chilled.

      Enjoy your vibrant, sweet, and nutritious vegan yogurt parfait!
    "#
  }
}
