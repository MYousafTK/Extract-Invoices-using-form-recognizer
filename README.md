# Invoice extraction using Microsoft 365/Azure and Open AI 

This project facilitates seamless document data extraction via HTTP requests sent from customers to MS Solutions. Utilizing Power Automate's cloud connector, documents in PDF format are processed to extract specified data elements such as invoice numbers, dates, and financial details. Leveraging Azure Form Recognizer and OpenAI's API, extracted text is analyzed and returned to customers, ensuring efficient data retrieval with optimal cost-effectiveness and readability.

![image](https://github.com/MYousafTK/Invoice-extraction-using-Microsoft-365-Azure-and-Open-AI-/assets/128382787/29cab7b2-f531-46ff-b608-bdd5e8bbcdbb)

# Skills Learned and Used 

- Performed all steps in Power Automate as well but then shift to Azure Function 
- Created local Http Trigger Azure Function in VS code and deployed to Azure portal 
- Python script to receive pdf_file, customer_url, required_param 
- Pass pdf to Form Recognizer API and get pdf content 
- Pass pdf_content to Chatgpt API with prompt to extract invoice data mentioned above 
- Send back Chatbot_response to customer provided endpoint url 
- Testing with Postman & Using Power Automate HTTP action 
