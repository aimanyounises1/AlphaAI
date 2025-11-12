# file: file_handlers/doc_handler.py
import os
import docx
import chainlit as cl

async def process_doc(file: cl.File, input_dir: str):
    try:
        # Ensure the input directory exists
        os.makedirs(input_dir, exist_ok=True)

        # Read the DOC file
        doc = docx.Document(file.path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        # Save the extracted text
        text_filename = os.path.splitext(file.name)[0] + ".txt"
        text_path = os.path.join(input_dir, text_filename)
        with open(text_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)

        await cl.Message(f"Successfully processed DOC file: {file.name}").send()
    except Exception as e:
        await cl.Message(f"Error processing DOC file {file.name}: {str(e)}").send()