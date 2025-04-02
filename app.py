from flask import Flask, request, jsonify
import pandas as pd
import openai
import json
# Load product data
products_df = pd.read_csv("products.csv")

# Load order data
orders_df = pd.read_csv("orders.csv")

# Load FAQs
with open("faq.json", "r") as f:
    faq_data = json.load(f)
app = Flask(__name__)
openai.api_key = "yourapi key"
def chatbot_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful e-commerce assistant."},
                  {"role": "user", "content": user_input}]
    )
    return response["choices"][0]["message"]["content"]
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "").lower()
    
    # Check if query is about order status
    if "order" in user_input or "status" in user_input:
        order_id = "".join(filter(str.isdigit, user_input))  # Extract order ID from message
        order_info = orders_df[orders_df["OrderID"] == int(order_id)]
        if not order_info.empty:
            return jsonify({"response": f"Your order {order_id} is {order_info.iloc[0]['Status']}. Expected delivery: {order_info.iloc[0]['DeliveryDate']}."})
        else:
            return jsonify({"response": "Order not found. Please check your Order ID."})

    # Check if query is about product availability
    for product in products_df["Name"]:
        if product.lower() in user_input:
            product_info = products_df[products_df["Name"].str.lower() == product.lower()]
            return jsonify({"response": f"{product} is {product_info.iloc[0]['Stock']}. Price: ${product_info.iloc[0]['Price']} with {product_info.iloc[0]['Discount']} discount."})
    
    # Check predefined FAQs
    for key, value in faq_data.items():
        if key in user_input:
            return jsonify({"response": value})
    
    # If no match, use OpenAI for response
    ai_response = chatbot_response(user_input)
    
    # If AI response is uncertain, escalate to human
    if "I am not sure" in ai_response or "I don't know" in ai_response:
        return jsonify({"response": "I couldn't find an answer. Let me connect you to a human agent."})
    
    return jsonify({"response": ai_response})
if __name__ == "__main__":
    app.run(debug=True)
