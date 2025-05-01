import streamlit as st
import pandas as pd
import boto3
import json
import re
import pyodbc
from nova_client import NovaClient

#st.set_page_config(layout="wide")

# Custom CSS to reduce space above the title
st.markdown("""
<style>
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
</style>
""", unsafe_allow_html=True)

def get_secret():
    # Initialize a session using Amazon Secrets Manager
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    
    # Get the secret value
    secret_name = "mssql_secrets"
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# Function to connect to the database
def connect_to_db():
    # Fetch the secret values
    secret_values = get_secret()
    host=secret_values['host']
    user=secret_values['username']
    password=secret_values['password']
    port=secret_values['port']
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host};UID={user};PWD={password}'
    
    try:
        # Connect to the MySQL server (without specifying a database)
        conn = pyodbc.connect(connection_string, autocommit=True)
        cursor = conn.cursor()

        if cursor:
            return conn
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Function for schedma generation 
def get_schema_context(db_name, db_view_name):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(f"USE {db_name}")
    query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{db_view_name}'"
    cursor.execute(query)
    schema = cursor.fetchall()
    print("Schema:", schema)
    return '\n'.join([f"- {row[0]}: {row[1]}" for row in schema])


# Funcution for query generation from amazon Nova
def interact_with_llm(query, db_name, db_view_name):
    from sql_generator import generate_sql_query
    try:
        # Get schema context and generate SQL query
        schema_context = get_schema_context(db_name,db_view_name)
        print("Schema Context:", schema_context)
        print("User Query:", query)
        sql_query = generate_sql_query(query, schema_context, db_name, db_view_name)
        
        # Create a placeholder for displaying results
        response_placeholder = st.empty()
        
        # Display the generated SQL query
        response_placeholder.markdown(f"""
        Generated SQL Query:
        ```sql: 
        {sql_query}
        ```
        """)
        print("Generated SQL Query:", sql_query)
        return sql_query
    except Exception as e:
        st.error(f"Error generating SQL query: {str(e)}")
        return None

# Function for Amazon Nova to generate human like response after processing data from database
def interact_with_nova(user_input, llm_query, query_response, model="nova"):
    session = boto3.session.Session()
    region = session.region_name
    
    nova_client = NovaClient(region_name=region)
    
    final_prompt = f"""Human: You are a expert chatbot who is happy to assist the users. User questions in given in <Question> tag and results in <query_response> tag. Understand the question and use information from <query_response> to generate an answer. If there are more than one entry, give a numbered list. Never retrun <question> and <query_response> in your response.
    for example : question - 'How many mouse were sold?'
                  llm response : 
                                " There were 3 mouse sold in total. 
                                - 1 mouse sold to Mia Perez on October 2nd, 2023. 
                                - 2 mouse sold to Jack Hernandez on October 1st 2023."
    <Question>
    {user_input}
    </Question>
    <query_response>
    {query_response}
    </query_response>"""
    
    try:
        
            response = nova_client.invoke_model(
                model_id='amazon.nova-lite-v1:0',
                prompt=final_prompt,
                max_tokens=4096,
                temperature=0.7
            )
            
            content = response['output']['message']['content']
            text = content[0]['text']
            return text
            
            return "Sorry, I couldn't process your request."
    
    except Exception as e:
        print(f"Error in LLM interaction: {str(e)}")
        return "Sorry, an error occurred while processing your request."
     
def main():
    
    custom_html = """
        <style>
            .banner {
                width: 200px;
                height: 500px;
                margin:auto;
                text-align:center; /*centers horizontally*/
                line-height:190px; /*same as height and for centering vertically*/
                
            }
            .banner img {
                width: 80%;
                object-fit: cover;
                
                
            }
        </style>
        """

# CSS for the chat interface and responses
    st.markdown('''
        <style>
        .chat-message {padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex}
        .chat-message.user {background-color:rgb(255, 237, 251)}
        .chat-message.bot {background-color:#0c0c0c}
        .chat-message .avatar {width: 20%}
        .chat-message .avatar img {max-width: 78px; max-height: 78px; border-radius: 50%; object-fit: cover}
        .chat-message .message {width:90%; color: #0c0c0c}
        .response, .url {background-color: #f0f0f0; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;}
        </style>
    ''', unsafe_allow_html=True)

    user_template = '''
        <div class="chat-message user">
            <div class="message">{{MSG}}</div>
        </div>
    '''

    # Display the custom HTML
    st.components.v1.html(custom_html)
    st.title("Welcome to Sales-bot Powered by Amazon Bedrock")

    # process starts here!
    secret_values = get_secret()
    db_name=secret_values['dbname']
    db_view_name = 'vw_BookingSummary_h' ## option - you can make this dynamic by adding a new field in secrets manager as view_name and retrieve it in the code by using db_view_name=secret_values['view_name']
    
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(f"USE {db_name}")
    st.success("Connected!")
     
    css = '''
        <style>
            .element-container:has(>.stTextArea), .stTextArea {
                width: 400px !important;
            }
            .stTextArea textarea {
                height: 200px;
            }
        </style>
        '''
    # Display the view
    try:
            query = f"SELECT top 1 * FROM {db_view_name};"
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            columns = pd.DataFrame(np.matrix(cursor.description))[0]
            
    except Exception as e:
            st.error(f"Error fetching view data: {e}")


    # LLM Interaction
    user_query = st.text_input("Enter your question:")

    if st.button("Run Query"):
            
            st.cache_data.clear()
            st.cache_resource.clear()
            
            llm_response = interact_with_llm(user_query,db_name, db_view_name)

            # Convert multiline llm_response to single line
            print(f"LLM Response: {llm_response}")
            
            # Extract SQL command from LLM response
            sql_command_match = llm_response 
            if sql_command_match:
                sql_command = sql_command_match
                try:
                    cursor.execute(sql_command)
                    result = cursor.fetchall()
                    print(result)
                    # Send the Dabase Query response to Amazon Nova
                    final_result=interact_with_nova(user_query,llm_response,result)
                    st.markdown(user_template.replace("{{MSG}}", final_result), unsafe_allow_html=True)
                    
                    
                except Exception as e:
                    st.error(f"Error executing SQL command: {e}")
            else:
                st.warning("No SQL command found in LLM response.")

    conn.close()

if __name__ == "__main__":
    main()

