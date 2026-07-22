import os
from dotenv import load_dotenv
import glob

# Import namespaces
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

default_endpoint = "https://ai.azure.com/.default"
instructions="""
You are a travel assistant that provides information on travel services available from Margie's Travel.
Answer questions about services offered by Margie's Travel using the provided travel brochures.
Search the web for general information about destinations or current travel advice.
Provides responses just in spanish.
"""

def main(): 
    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    try:
        # Get configuration settings 
        load_dotenv()
        azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        model_deployment = os.getenv("MODEL_DEPLOYMENT")

        # Initialize the OpenAI client
        token_provider = get_bearer_token_provider(DefaultAzureCredential(), default_endpoint)
        client = OpenAI(
            base_url = azure_openai_endpoint,
            api_key= token_provider
        )


        # Create vector store and upload files
        print("Creating vector store and uploading files..")
        vector_store = client.vector_stores.create(
            name="travel-brochures"
        )
        file_streams = [open(f,"rb") for f in glob.glob("brochures/*.pdf")]
        if not file_streams:
            print("No PDF files found in the brochures folder!")
            return
        
        file_batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id = vector_store.id,
            files = file_streams
        )

        tools = [
            {
                "type": "file_search",
                "vector_store_ids": [vector_store.id]
            },
            {
                "type": "web_search"
            }
        ]
        for f in file_streams:
            f.close()

        print(f"Vector store created with {file_batch.file_counts.completed} files.")
        # Track conversation state
        last_response_id = None

        # Loop until the user wants to quit
        while True:
            input_text = input('\nEnter a question (or type "quit" to exit): ')
            if input_text.lower() == "quit":
                break
            if len(input_text) == 0:
                print("Please enter a question.")
                continue

            # Get a response using tools
            response = client.responses.create(
                model = model_deployment,
                instructions = instructions,
                input = input_text,
                previous_response_id = last_response_id,
                tools = tools
            )

            answer = response.output_text
            print(f"Assistant: {answer}")
            last_response_id = response.id
            



    except Exception as ex:
        print(ex)

if __name__ == '__main__': 
    main()
