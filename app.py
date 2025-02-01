import streamlit as st
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.storage.blob import BlobServiceClient
import time
from PIL import Image
import io
import base64

# Set the title of the browser tab
st.set_page_config(page_title="Azure AI - OCR & Face Detection", page_icon="🧑‍💻")

# Azure configuration

# Computer vision (OCR)
AZURE_KEY = "Azure-Key"
AZURE_ENDPOINT = "https://rajcomputervision1.cognitiveservices.azure.com/"

# Face API (Face Detection)
FACE_API_KEY = "Azure-cognitiveservices-key"
FACE_API_ENDPOINT = "https://rajazurefaceapi1.cognitiveservices.azure.com/"

# Storage account-Location
AZURE_REGION = "eastus"

# Storage account-Access Keys (Container, Azure-blob-storage)
STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=rajmachinelear7916564259;AccountKey=xxxxxx==;EndpointSuffix=core.windows.net"

# Azure clients
computervision_client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))
blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
face_client = FaceClient(FACE_API_ENDPOINT, CognitiveServicesCredentials(FACE_API_KEY))

# Function to fetch all containers
def fetch_containers():
    try:
        return [container.name for container in blob_service_client.list_containers()]
    except Exception as e:
        st.error(f"Error fetching containers: {e}")
        return []

# Function to create a new container
def create_new_container(container_name):
    try:
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
            return True
        else:
            st.warning(f"Container '{container_name}' already exists.")
            return False
    except Exception as e:
        st.error(f"Error creating new container: {e}")
        return False

# Function to upload file to blob
def upload_to_blob(container_name, blob_name, image_data):
    try:
        container_client = blob_service_client.get_container_client(container_name)
        container_client.upload_blob(blob_name, image_data)
        return True
    except Exception as e:
        st.error(f"Error uploading blob: {e}")
        return False

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

# Function for face detection using Azure Face API
def detect_faces(image_data):
    try:
        detected_faces = face_client.face.detect_with_stream(
            image=image_data,
            return_face_id=False,
            return_face_landmarks=False,
            return_face_attributes=None
        )

        if not detected_faces:
            st.warning("No faces detected in the image. 😞")
            return None

        image = Image.open(image_data)
        faces = []

        for face in detected_faces:
            rect = face.face_rectangle
            left, top, width, height = rect.left, rect.top, rect.width, rect.height
            box = (left, top, left + width, top + height)

            # Crop face from the image
            face_image = image.crop(box)
            faces.append(face_image)

        return faces
    except Exception as e:
        st.error(f"Error during face detection: {e}")
        return None

import base64

# Function to convert an image to base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_image

# Set path to your image
background_image_path = "img.jpg"  # Replace with your image path

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

# Streamlit UI
st.markdown("<h1 style='text-align: center; font-size: 40px;'>Azure Blob Storage, OCR, and Face Detection 🧑‍💻📸</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    # Section for selecting an existing container
    st.markdown("Select an Existing Container 📦")
    existing_containers = fetch_containers()

    if existing_containers:
        selected_container = st.selectbox("Choose an existing container:", existing_containers)
        st.write(f"Selected container: {selected_container}")
    else:
        st.warning("No containers available. Please create one.")

    # Section for container creation
    st.header("Create a New Container 📦")
    new_container_name = st.text_input("Enter new container name:")
    if st.button("Create Container"):
        if new_container_name:
            if create_new_container(new_container_name):
                st.success(f"Container '{new_container_name}' created successfully! 🎉")
        else:
            st.error("Please provide a container name. 🚫")

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
        if st.button("Perform OCR 📝"):
            ocr_result = perform_ocr(image_bytes)
            if ocr_result:
                st.write("Extracted Text: 🗣️")
                for line in ocr_result:
                    st.write(line)

        # Face Detection Section
        if st.button("Detect Faces 👤"):
            faces = detect_faces(image_bytes)
            if faces:
                st.write("Detected Faces: 😍")
                for idx, face in enumerate(faces):
                    st.image(face, caption=f"Face {idx + 1}", use_column_width=True)

        # Upload to Azure Blob Storage Section
        if st.button("Upload to Azure Blob Storage ☁️"):
            if selected_container:  # Use selected_container for uploading to the chosen container
                # Check if the image already exists in the selected container
                blob_exists = False
                try:
                    # Check if the blob exists by getting its properties
                    blob_service_client.get_container_client(selected_container).get_blob_client(uploaded_file.name).get_blob_properties()
                    blob_exists = True
                except Exception as e:
                    if "404 Client Error" not in str(e):
                        st.error(f"Error checking blob existence: {e}")
                
                if blob_exists:
                    st.warning(f"Image '{uploaded_file.name}' already exists in container '{selected_container}'. 🚫")
                else:
                    # Upload the image if it doesn't exist
                    if upload_to_blob(selected_container, uploaded_file.name, image_bytes.getvalue()):
                        st.success(f"Image '{uploaded_file.name}' uploaded to container '{selected_container}'. 📤")
                        
            elif new_container_name:  # If the user creates a new container, upload there
                # Check if the image already exists in the new container
                blob_exists = False
                try:
                    # Check if the blob exists by getting its properties
                    blob_service_client.get_container_client(new_container_name).get_blob_client(uploaded_file.name).get_blob_properties()
                    blob_exists = True
                except Exception as e:
                    if "404 Client Error" not in str(e):
                        st.error(f"Error checking blob existence: {e}")
                
                if blob_exists:
                    st.warning(f"Image '{uploaded_file.name}' already exists in new container '{new_container_name}'. 🚫")
                else:
                    # Upload the image if it doesn't exist
                    if upload_to_blob(new_container_name, uploaded_file.name, image_bytes.getvalue()):
                        st.success(f"Image '{uploaded_file.name}' uploaded to new container '{new_container_name}'. 📤")
                        
            else:
                st.error("Please select or create a container before uploading. 🚫")



    # Show updated container contents
    if st.button("Show Container Contents 📂"):
        try:
            container_client = blob_service_client.get_container_client(selected_container)
            blobs = [blob.name for blob in container_client.list_blobs()]
            if blobs:
                st.write("Container Contents: 📋")
                for blob in blobs:
                    st.write(blob)
            else:
                st.write("No files in container. 🚫")
        except Exception as e:
            st.error(f"Error listing container contents: {e}")
