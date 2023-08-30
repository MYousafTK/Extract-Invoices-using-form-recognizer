import logging
import os
import requests
import json
import uuid
from azure.core.exceptions import ResourceNotFoundError
#from azure.ai.formrecognizer import FormRecognizerClient, FormTrainingClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import azure.functions as func
from azure.data.tables import TableServiceClient, UpdateMode
from datetime import datetime

FormRecognizer_API_KEY = os.getenv("Env_FormRecognizer_API_KEY")
FormRecognizer_ENDPOINT = os.getenv("Env_FormRecognizer_ENDPOINT")
Chatgpt_Api_key= os.getenv("Env_Chatgpt_Api_key")
CHATGPT_API_ENDPOINT = 'https://api.openai.com/v1/chat/completions'
"""Endpoint_toGetKeys = os.getenv("Env_Endpoint_toGetKeys")
AdminAPIKey_toGetFunctionKeys = os.getenv("Env_AdminAPIKey_toGetFunctionKeys")

connection_string = os.getenv('Env_connection_string')
table_service_client = TableServiceClient.from_connection_string(connection_string)"""

       

# Azure Function to handle the PDF processing and ChatGPT response
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        pdf_file = req.files.get("pdf_file")
        customer_url = req.form.get("customer_url")
        required_param = req.form.get("required_param")
        # Get the customer Function key from the request URL parameters
        customer_key_url = req.params.get("code")
        # Get the customer key from the request headers
        customer_key_header = req.headers.get("x-functions-key")
        # Choose the customer key, giving priority to the one in the URL if both are present
        customer_Function_key = customer_key_url or customer_key_header



        if pdf_file:
           pdf_content = pdf_file.read()
        else:
            return func.HttpResponse(
                status_code=400,
                body=json.dumps({"error": "No PDF file provided"}),
                mimetype="application/json"
            )

        # Process the PDF content and get text
        pdf_content_text = process_pdf_content(pdf_content)
        
        
        # Prompt
        #prompt=f'''Extract the following data: invoice_no= Invoice Number, invoice_date=Invoice date in dd.mm.yyyy format, payment_due=Invoice payment due date in dd.mm.yyyy format, total_excl_vat= Invoice total excluding VAT without currency abbreviation, vat=Invoice total VAT without currency abbreviation, total_incl_vat= Invoice total including VAT without currency abbreviation, supplier_vat=Supplier VAT number, recipient_vat=Recipient VAT number from the provided content: '{pdf_content_text}'. keep in mind that content is in Latvian language so result should be accurate e.g invoice_no will be like PAVADZIME Nr= AM230600424 2023, Rēķina datums =2023. gada 20. jünijs, Apmaksas termiņš =17.07.2023, Kopsumma bez PVN= 53.3, PVN 21%=4.4, Kopsumma ar PVN or Apmaksas summa=66.4 and Saņēmēja PVN numurs= 40203368636  but provide output in this format: {{"invoice_no": "7897349 or AM230600424","invoice_date": "30.06.2023","payment_due": "17.07.2023","total_excl_vat": 62.12,"vat": 13.05,"total_incl_vat": 75.17,"supplier_vat": "LV40203368636","recipient_vat": "LV40003132723"}}. and don't respond from sample values these are for just sample not use them in original response return only values which are in above content otherwise return null'''
        
        Envprompt=os.getenv("prompt12")
        prompt=f"From the provided content in triple quote ```{pdf_content_text}.```, {Envprompt}.{required_param}"
        logging.info(f"Prompt : {prompt}")
        # Get ChatGPT response
        chatbot_response,total_tokens_used = get_chatbot_response(prompt)

        # Send ChatGPT response to client endpoint
        send_chatgpt_response_to_client(chatbot_response, customer_url, customer_Function_key)



        # Get keys from the response
        """keys_from_response = get_azure_function_keys(Endpoint_toGetKeys, AdminAPIKey_toGetFunctionKeys)

        if keys_from_response:
            key_name = find_key_name(keys_from_response, customer_Function_key)
            if key_name:
                print(f"Customer key '{customer_Function_key}' corresponds to key name '{key_name}'.")
            else:
                print("Customer key not found in the keys list.")
        else:
            print("Failed to retrieve keys from the response.")"""





        # Query table to find a match
        """table_name = "ApiCallsTracker"
        table_client = table_service_client.get_table_client(table_name)
        # Prepare the entity to insert
        new_entity = {
        "PartitionKey": customer_Function_key,  # Use customer key as PartitionKey
        "RowKey": str(uuid.uuid4()),
        "CustomerName": key_name,  
        "TotalTokens": total_tokens_used  # Insert the total tokens used
        }

        # Insert the new entity
        table_client.upsert_entity(new_entity)"""

        


        # Prepare response data
        response_data = {
            "response": chatbot_response,
            "internal_postback_url":customer_Function_key
        }
        
        return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")

    except Exception as e:
        error_message = str(e)
        return func.HttpResponse(f'body={error_message}',status_code=500
        )







def process_pdf_content(pdf_content):
    # Create a Form Recognizer client
    #form_recognizer_client = FormRecognizerClient(FormRecognizer_ENDPOINT, AzureKeyCredential(FormRecognizer_API_KEY))
    document_analysis_client = DocumentAnalysisClient(FormRecognizer_ENDPOINT, AzureKeyCredential(FormRecognizer_API_KEY))
    #pdf_stream = io.BytesIO(pdf_content)

    poller = document_analysis_client.begin_analyze_document("prebuilt-read", pdf_content)

    #poller = form_recognizer_client.begin_recognize_content(pdf_stream)
    form_result = poller.result()

    pdf_text = ""

    for page in form_result.pages:
        for line in page.lines:
            pdf_text += line.content + " "

    return pdf_text

def get_chatbot_response(prompt):
    # Get a response from the ChatGPT API
    default_max_tokens = 4096
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {Chatgpt_Api_key}'
    }

    data = {
        'model': 'gpt-3.5-turbo',
        'temperature':0,
        'messages': [{'role': 'system', 'content': 'You are an AI assistant trained to extract invoice details accurately and format them into JSON.'},
                     {'role': 'user', 'content': prompt}]
    }

    response = requests.post(CHATGPT_API_ENDPOINT, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        #return result['choices'][0]['message']['content']
        content = result['choices'][0]['message']['content']
        total_tokens = result['usage']['total_tokens']
        
        if total_tokens >= default_max_tokens:
            return func.HttpResponse("Text length exceeded. Please provide a shorter prompt.", status_code=400)
        else:
            return content, total_tokens

    else:
        print(f"Failed to get response from ChatGPT API. Status code: {response.status_code}")
        return None

def send_chatgpt_response_to_client(chatbot_response,  customer_url, customer_Function_key):
    try:
        
        response_data = {'response': chatbot_response,
                         "internal_postback_url":customer_Function_key
                        }
        response = requests.post(customer_url, json=response_data)

        if response.status_code == 200:
            logging.info("Response successfully sent to the endpoint.")
            # Prepare response data
            response_data = {
            "response": chatbot_response,
            "internal_postback_url":customer_Function_key
            }
            return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")
        else:
            logging.error(f"Failed to send response to the endpoint. Status ccode: {response.status_code}")
            return func.HttpResponse(f"Failed to send response to the endpoint. Status ccode: {response.status_code}")
    except Exception as e:
        error_message = str(e)
        logging.error(f"An Exception error occurred sending Chatgpt response to Customer url: {error_message}")
        return func.HttpResponse(
            body=json.dumps({"An Exception error occurred sending Chatgpt response to Customer url": error_message}),
            status_code=500
        )
    
"""def get_azure_function_keys(Endpoint_toGetKeys, AdminAPIKey_toGetFunctionKeys):
    headers = {
        "Content-Type": "application/json",
        "x-functions-key": AdminAPIKey_toGetFunctionKeys
    }

    response = requests.get(Endpoint_toGetKeys, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        return response_data["keys"]
    else:
        return None

def find_key_name(keys_list, customer_key):
    for key in keys_list:
        if key["value"] == customer_key:
            return key["name"]
    return None"""