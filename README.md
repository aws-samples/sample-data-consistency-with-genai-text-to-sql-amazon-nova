# Data Consistency with GenAI: The Case for Text-to-SQL Solution Using Amazon Nova

This repository contains the code and resources for implementing a Text-to-SQL solution using Amazon Nova LLMs as described in the AWS Blog post of the same name.

## Overview

This solution enables non-technical users to query organizational data using natural language. It leverages Amazon Bedrock with Amazon Nova Lite and Pro LLMs to translate natural language queries into SQL, execute them against your database, and return formatted, human-readable responses.

## Architecture 

![alt text](/images/architecture.png)


## Key Features

- **Dynamic Schema Context**: Retrieves database schema dynamically for precise query generation
- **SQL Query Generation**: Converts natural language into SQL queries using Amazon Nova Pro LLM
- **Query Execution**: Runs queries on organizational databases and retrieves results
- **Formatted Responses**: Processes raw query results into user-friendly formats using Amazon Nova Lite LLM

## Prerequisites
Before getting started, make sure you have the following:

- **AWS Account** 
- **AWS CLI**: Make sure AWS CLI is installed and configured with valid credentials.
   - **AWS CLI Installation** - Follow AWS [documentation](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) to install AWS Command Line Interface (AWS CLI) and check the version with following command.
      ```shell
      aws --version
      ```
   - **AWS CLI configure** - Follow AWS [documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) to configure basic settings that the AWS Command Line Interface (AWS CLI) uses to interact with AWS.
- **Amazon Bedrock Access**: Make sure Amazon Bedrock is [enabled](https://docs.aws.amazon.com/bedrock/latest/userguide/setting-up.html) in your AWS account
- **Model access**: Obtain [access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) to Amazon Nova Lite and Pro LLMs
- **Database System**: Sample code uses [Microsoft SQL Server](https://www.microsoft.com/en-us/sql-server/sql-server-downloads) (version 2016 or later) On-Premises, but this solution also supports:
   - [Amazon RDS](https://aws.amazon.com/rds/) (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server) 
   - [Amazon Aurora](https://aws.amazon.com/rds/aurora/) (MySQL and PostgreSQL compatible)
   - On-Premises Databases
   Note: You will need to modify the database connection code and SQL syntax when adapting this sample to database engines other than SQL Server.
- **Python Development Setup**: Python 3.9 or later installed on your local machine (or on virtual machine),
   - Python 24.0 or later.If missing, install from [here](https://www.python.org/downloads/)
    ```shell
    python --version
    ```
   - Pip 24.3.1 or later. If missing, install from [here](https://pip.pypa.io/en/stable/installation/)
   ```shell
    pip --version
    ```
   - To update pip, run: 
    ```shell
    python.exe -m pip install --upgrade pip
    ```

## Setup Instructions
1. **MS SQL Server Database**: set up the MS SQL database with credentials to connect to the database.
  - Create a secret in [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) for DB credentials and name it "mssql_secrets"
  - Follow [AWS Secrets Manager Guide](https://docs.aws.amazon.com/dms/latest/sbs/schema-conversion-oracle-postgresql-step-4.html) and select "Credentials for other database" under the "Choose Secret Type" section

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sample-data-consistency-with-genai-text-to-sql-amazon-nova
   ```

1. **Set Up the Development Environment**
- Run below command to install required libraries -
   - Streamlit version 1.23.0 or later
   - Boto3
   - botocore verions 1.34.107 or later
   - pandas
   - mysql-connector-python
   - pyodbc

   ```bash
   python -m pip install -r requirements.txt --upgrade
   ```

2. **Load Sample Dataset in Database**
   - Make sure you have created a secret in AWS Secrets Manager named "mssql_secrets" as per the prerequisites
   - If name of your secrets manager is different than "mssql_secrets", update the code under folder sample-data-consistency-with-genai-text-to-sql-amazon-nova in:
     - app.py (line 37)
     - load_data.py (line 22)
   - Run the following command from the code folder:
     ```bash
     python load_data.py
     ```
   This creates a database named Sales with tables Products, Customers, and Orders and loads sample data. This script also creates a database view - vw_sales which is used in the application code.

3. **Run the Application**
   ```bash
   streamlit run app.py
   ```

## Example Queries

### Example 1: Find Customers Who Bought Smartphones
- **User Query**: "Who are the customers who bought smartphones?"
- **Generated SQL**: 
  ```sql
  SELECT DISTINCT CustomerName, ProductName, SUM(Quantity) AS TotalSoldQuantity 
  FROM vw_sales 
  WHERE ProductName LIKE '%smartphone%' 
  GROUP BY CustomerName, ProductName, OrderDate;
  ```
- **Formatted Response**:
  - Alice Johnson, who bought 1 smartphone on October 14th, 2023
  - Ivy Martinez, who bought 2 smartphones on October 15th, 2023

### Example 2: Check Available Smartphones in Stock
- **User Query**: "How many smartphones are in stock?"
- **Generated SQL**:
  ```sql
  SELECT DISTINCT ProductName, StockQuantity AS AvailableQuantity 
  FROM vw_sales 
  WHERE ProductName LIKE '%smartphone%';
  ```
- **Formatted Response**: "There are 100 smartphones currently in stock."

## Clean Up

To avoid incurring future costs:

1. **Database cleanup**:
   - Delete the Amazon RDS instance or EC2 instance hosting the database
   - Remove associated storage volumes

2. **Security cleanup**:
   - Delete database credentials from AWS Secrets Manager
   - Remove Bedrock model access for Amazon Nova Pro and Lite LLM

3. **Frontend cleanup** (optional - If hosting Streamlit app on Amazon EC2):
   - Terminate the EC2 instance hosting the Streamlit application
   - Delete associated storage volumes

4. **Additional resources** (if applicable):
   - Remove Elastic Load Balancers
   - Delete VPC configurations

5. **Final verification**:
   - Check AWS Management Console to confirm all resources have been deleted

## Additional Resources

For a more comprehensive example of a Text-to-SQL solution built on Amazon Bedrock, explore the [Bedrock Agent GitHub](https://github.com/aws-samples/bedrock-agent-txt2sql). This open-source project demonstrates how to use Amazon Bedrock and Amazon Nova LLM to build a robust text-to-SQL agent that can generate complex queries, self-correct, and query diverse data sources.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.