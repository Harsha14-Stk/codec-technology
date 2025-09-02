from flask import Flask, render_template, request
from transformers import pipeline

# Initialize Flask app
app = Flask(__name__)

# Load a pre-trained sentiment analysis model
# 'sentiment-analysis' is a task, and 'distilbert-base-uncased-finetuned-sst-2-english'
# is a specific model good for this task.
sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')

@app.route('/', methods=['GET', 'POST'])
def index():
    sentiment_result = None
    input_text = ""

    if request.method == 'POST':
        input_text = request.form['text_to_analyze']
        if input_text:
            # Perform sentiment analysis
            result = sentiment_analyzer(input_text)
            # The result is a list of dictionaries, e.g.,
            # [{'label': 'POSITIVE', 'score': 0.999}]
            sentiment_result = result[0]
            # Format for display
            sentiment_result['label'] = sentiment_result['label'].capitalize()
            sentiment_result['score'] = f"{sentiment_result['score']:.2f}"

    return render_template('index.html', sentiment=sentiment_result, input_text=input_text)

if __name__ == '__main__':
    # Run the Flask app
    # debug=True allows for auto-reloading on code changes and provides a debugger
    app.run(debug=True)