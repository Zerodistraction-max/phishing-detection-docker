from flask import Flask, request, render_template, redirect, url_for
import numpy as np
import pickle
import warnings
import joblib

# --- Import your existing modules ---
# These files were copied from the source path
from feature import FeatureExtraction
from convert import convertion as original_convertion
# -----------------------------------

warnings.filterwarnings('ignore')

# 1. Load the ML model
MODEL_FILE = "newmodel.pkl"
try:
    with open(MODEL_FILE, "rb") as file:
        gbc = joblib.load(file)
    print(f"Model loaded successfully from {MODEL_FILE}.")
except FileNotFoundError:
    print(f"Error: {MODEL_FILE} not found. Please ensure it is in the same directory.")
    gbc = None
except Exception as e:
    print(f"Error loading model {MODEL_FILE}: {e}")
    gbc = None

app = Flask(__name__)

# --- Custom Conversion Logic (based on your convert.py, adapted for CSS classes) ---
def custom_convertion(url, prediction):
    """
    Returns formatted results for the front end based on the model's prediction,
    incorporating the shortlink check from your original convert.py.

    :param url: The URL the user entered.
    :param prediction: The model's prediction (-1 for unsafe, 1 for safe).
    :return: (url, prediction_text, button_text, button_css_class)
    """
    # The original convert.py logic returns [url, "Not Safe", "Still want to Continue"] if shortlink is found.
    # We check the shortlink status using your provided helper function:
    # Note: We rely on the internal logic of original_convertion to check for shortlinks
    # We define the default outputs based on the two required paths:
    safe_output = [url, "Website is Safe to use", "Continue Browsing", "btn-safe"]
    unsafe_output = [url, "Website is NOT Safe to use", "Continue Anyway", "btn-unsafe"]

    # First, check for the explicit UNSAFE flags: model prediction -1 OR shortlink check (from your convert.py)
    is_shortlink_unsafe = original_convertion(url, prediction)[1] == "Not Safe"

    if prediction == -1 or is_shortlink_unsafe:
        return unsafe_output
    elif prediction == 1:
        return safe_output
    else:
        # Fallback to unsafe for any unexpected prediction value (e.g., 0)
        return unsafe_output

# --- Routing and Views ---
@app.route("/")
def home():
    """Renders the home page with the URL input form."""
    return render_template("index.html")

@app.route('/about')
def about():
    """Renders the About page with team information."""
    return render_template('about.html',
                           team_member="Suryansh Sapehia",
                           project_name="Epics Project")

@app.route('/usecases')
def usecases():
    """Renders the Phishing Education page."""
    return render_template('usecases.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handles the URL submission, feature extraction, prediction, and result display."""
    if not gbc:
        return render_template("index.html",
                               error_text="Model not available. Check server logs.",
                               url_input="")

    url = request.form.get("url_input", "").strip()
    if not url:
        return render_template("index.html",
                               error_text="Please enter a URL to analyze.",
                               url_input="")

    # Ensure URL has a scheme for correct navigation later
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'http://' + url

    try:
        # 2. Feature Extraction (Uses your implemented logic in feature.py)
        obj = FeatureExtraction(url)
        features = obj.getFeaturesList()
        
        if len(features) != 30:
            raise ValueError(f"Expected 30 features, but got {len(features)}. Check feature.py errors for URL: {url}")
        
        x = np.array(features).reshape(1, -1)

        # 3. Prediction
        y_pred = gbc.predict(x)[0]

        # 4. Result Formatting using custom logic
        result_url, result_text, button_text, button_class = custom_convertion(url, int(y_pred))

        # Render the result on the main page
        return render_template("index.html",
                               prediction_url=result_url,
                               prediction_text=result_text,
                               button_text=button_text,
                               button_class=button_class,
                               url_input=url)

    except Exception as e:
        print(f"Prediction Error for {url}: {e}")
        return render_template("index.html",
                               error_text=f"An error occurred during analysis (Is the URL valid? Check server logs for details): {e}",
                               url_input=url)

if __name__ == "__main__":
    app.run(debug=True)