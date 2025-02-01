# https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app/
# .\tensorflowvenv\Scripts\activate
# cd PrakashSenapati\2024_12_05_Azure_Blob_Storage_OCR_and_Face_Detection
# streamlit run testapp.py
# ==================================================================
import streamlit as st
import os
import sys
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
import time
from PIL import Image, ImageDraw
import io
import base64
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.storage.blob import BlobServiceClient
# ==================================================================
st.set_page_config(page_title="OCR", page_icon="📑")
# ==================================================================
# Azure configuration

# Computer vision (OCR)
AZURE_KEY = "Azure-key"
AZURE_ENDPOINT = "https://rajcomputervision1.cognitiveservices.azure.com/"

# Face API (Face Detection)
FACE_API_KEY = "Azure-cognitiveservices-key"
FACE_API_ENDPOINT = "https://rajazurefaceapi1.cognitiveservices.azure.com/"

# Storage account-Location
AZURE_REGION = "eastus"

# Storage account-Access Keys (Container, Azure-blob-storage)
STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=rajmachinelear7916564259;AccountKey=xxxxx==;EndpointSuffix=core.windows.net"

# Azure clients
computervision_client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))
blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
face_client = FaceClient(FACE_API_ENDPOINT, CognitiveServicesCredentials(FACE_API_KEY))

# ==================================================================
# Function for OCR using Azure Computer Vision

def perform_ocr(image_data):
    try:
        response = computervision_client.read_in_stream(image_data, language="en", raw=True)
        operation_location = response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]

        # Poll for the OCR result
        while True:
            result = computervision_client.get_read_result(operation_id)
            if result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)

        if result.status == OperationStatusCodes.succeeded:
            text = []
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    text.append(line.text)
            return text
        else:
            st.error("OCR processing failed.")
            return None
    except Exception as e:
        st.error(f"Error during OCR: {e}")
        return None

# ==================================================================
# Function to convert an image to base64

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_image

# ==================================================================
# Set path to your image
background_image_path = "img.jpg"

# Convert image to base64
encoded_image = image_to_base64(background_image_path)

# Set background image using base64 encoding in CSS
st.markdown(
    f"""
    <style>
        .stApp {{
            background-image: url('data:image/jpeg;base64,{encoded_image}');
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            height: 100%;
            width: 100%;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================================================================
# Streamlit UI

st.markdown("<h1 style='text-align: center; font-size: 40px;'>OCR 📑</h1>", unsafe_allow_html=True)

# ==================================================================

col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    # File upload section
    uploaded_file = st.file_uploader("Upload an Image 🖼️", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Save image in-memory for processing and uploading
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        image_bytes.seek(0)

        # OCR Section
        if st.button("Perform OCR 📑"):
            ocr_result = perform_ocr(image_bytes)
            if ocr_result:
                st.write("Extracted Text: 🗣️")
                for line in ocr_result:
                    st.write(line)

# ==================================================================