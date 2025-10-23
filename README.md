PDF Chatbot
===============

This is a minimal Flask web app that answers questions about a PDF placed at `data/document.pdf`.

Setup
------

1. Create a `data` folder next to `app.py` and put your PDF there as `document.pdf`:

   - `c:\Users\anshu\OneDrive\Desktop\Kg_chatbot\data\document.pdf`

2. Install dependencies (prefer a virtual environment):

   pip install -r requirements.txt

Run
----

python app.py

Open http://127.0.0.1:5000/ and ask questions.

Behavior
--------

- If the question is unrelated to the PDF, the app returns "Out of context question" based on a similarity threshold.
- Uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings

Notes
-----

- Models will be downloaded by the first run; ensure you have an internet connection.
- Adjust `SIMILARITY_THRESHOLD` in `app.py` to be more or less strict.
