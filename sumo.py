from flask import Flask, request, jsonify, send_file
import pdfplumber
from groq import Groq
from docx import Document
from fpdf import FPDF
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)

# Initialize Groq client with your API key
API_KEY = "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"
client = Groq(api_key=API_KEY)


# Function to split text into chunks of a maximum token length
def chunk_text(text, max_tokens=1024):
    words = text.split()
    chunks = []
    chunk = []

    for word in words:
        chunk.append(word)
        if len(" ".join(chunk)) > max_tokens:
            chunks.append(" ".join(chunk[:-1]))
            chunk = [chunk[-1]]

    if chunk:
        chunks.append(" ".join(chunk))

    return chunks


@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    try:
        # Check if file is in the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        uploaded_file = request.files['file']
        if not uploaded_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400

        # Extract text from the PDF
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = "".join([page.extract_text() for page in pdf.pages])

        if not full_text.strip():
            return jsonify({'error': 'No text extracted from the PDF'}), 400

        # Generate quiz questions using Groq API
        text_chunks = chunk_text(full_text, max_tokens=1024)
        final_quiz = ""

        for chunk in text_chunks:
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{
                    "role": "user",
                    "content": f"Just Generate subjective questions and its answers in brief that assess thorough understanding of the following text:\n{chunk}"
                }],
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )

            quiz_text = ""
            for response_chunk in completion:
                quiz_text += response_chunk.choices[0].delta.content or ""

            final_quiz += quiz_text.strip() + "\n\n"

        # Return the quiz as plain text
        return jsonify({'quiz': final_quiz.strip()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
