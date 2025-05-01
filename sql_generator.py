import boto3
import re
from nova_client import NovaClient


def generate_sql_query(question: str, schema_context: str, db_name: str, db_view_name: str = None) -> str:
    
    nova_client = NovaClient()
       
    # Base prompt with SQL generation rules
    base_prompt = """
    MS SQL DB {db_name} has one view names '{db_view_name}'. 
    Always use '{db_view_name}' as table name to generate your query.
    Create a MS SQL query by carefully understanding the question and generate the query between tags <begin sql> and </end sql>.
    The MS SQL query should selects all columns from a view named '{db_view_name}'
    In your SQL query always use like condition in where clasue.
    if a question is asked about product stock then always use 'distinct' in your SQL query and refer to StockQuantity column.
    Never Generate an SQL query which gives error upon execution.

      
    
    Question: {question}
    
    Database Schema : {schema_context}
    
    Generate SQL query:
    """
    
    # Format the prompt with the question and schema context
    formatted_prompt = base_prompt.format(
        question=question,
        db_name=db_name,
        db_view_name=db_view_name if db_view_name else "No view name provided",
        schema_context=schema_context if schema_context else "No additional context provided"
    )
        
    # Invoke Nova model
    response = nova_client.invoke_model(
        model_id='amazon.nova-pro-v1:0',
        prompt=formatted_prompt,
        temperature=0.1  # Lower temperature for more deterministic SQL generation
    )
    
    # Extract SQL query from response using regex
    sql_match = extract_sql_from_nova_response(response)
    if sql_match:
        return sql_match
    else:
        raise ValueError("No SQL query found in the response")
    

def extract_sql_from_nova_response(response):
    try:
        # Navigate the nested dictionary structure
        content = response['output']['message']['content']
        # Get the text from the first content item
        text = content[0]['text']
        
        # Find the positions of begin and end tags
        begin_tag = "<begin sql>"
        end_tag = "</end sql>"
        start_pos = text.find(begin_tag)
        end_pos = text.find(end_tag)
        
        # If both tags are found, extract the SQL between them
        if start_pos != -1 and end_pos != -1:
            # Add length of begin tag to start position to skip the tag itself
            sql_query = text[start_pos + len(begin_tag):end_pos].strip()
            return sql_query
            
        return None
        
    except (KeyError, IndexError):
        # Return None if the expected structure is not found
        return None