# file: file_handlers/pdf_handler.py
import os
import PyPDF2
import chainlit as cl


async def process_pdf(file: cl.File, input_dir: str):
    try:
        # Ensure the input directory exists
        os.makedirs(input_dir, exist_ok=True)

        # Read the PDF file
        pdf_reader = PyPDF2.PdfReader(file.path)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Save the extracted text
        text_filename = os.path.splitext(file.name)[0] + ".txt"
        text_path = os.path.join(input_dir, text_filename)
        with open(text_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)

        await cl.Message(f"Successfully processed PDF file: {file.name}").send()
    except Exception as e:
        await cl.Message(f"Error processing PDF file {file.name}: {str(e)}").send()
