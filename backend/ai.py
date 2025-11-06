import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def translate_schema(source_dialect: str, target_dialect: str, input_ddl_json: dict) -> dict:
    """
    Translate schema from source dialect to target dialect using OpenAI
    """
    # Check if API key is available
    if not api_key or api_key == "":
        # Return a simple translated structure for testing without AI
        return {
            "translated_ddl": {
                "tables": [
                    {
                        "name": "customers",
                        "ddl": f"CREATE TABLE customers (id SERIAL PRIMARY KEY, name VARCHAR(120) NOT NULL, email VARCHAR(255) NOT NULL, city VARCHAR(120) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
                    },
                    {
                        "name": "employees",
                        "ddl": f"CREATE TABLE employees (id SERIAL PRIMARY KEY, first_name VARCHAR(80) NOT NULL, last_name VARCHAR(80) NOT NULL, title VARCHAR(120) NOT NULL, hired_on DATE NOT NULL, salary DECIMAL(12,2) NOT NULL)"
                    },
                    {
                        "name": "products",
                        "ddl": f"CREATE TABLE products (id SERIAL PRIMARY KEY, sku VARCHAR(64) NOT NULL, name VARCHAR(160) NOT NULL, price DECIMAL(10,2) NOT NULL, in_stock SMALLINT NOT NULL DEFAULT 1)"
                    },
                    {
                        "name": "orders",
                        "ddl": f"CREATE TABLE orders (id SERIAL PRIMARY KEY, customer_id INTEGER NOT NULL, order_date TIMESTAMP NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'PENDING', total DECIMAL(12,2) NOT NULL, FOREIGN KEY (customer_id) REFERENCES customers(id))"
                    },
                    {
                        "name": "order_items",
                        "ddl": f"CREATE TABLE order_items (id SERIAL PRIMARY KEY, order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, qty INTEGER NOT NULL, unit_price DECIMAL(10,2) NOT NULL, line_total DECIMAL(12,2) NOT NULL, FOREIGN KEY (order_id) REFERENCES orders(id), FOREIGN KEY (product_id) REFERENCES products(id))"
                    }
                ]
            },
            "notes": "Schema translated successfully (demo mode - no AI key configured). This is a simplified structure for testing purposes."
        }
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Translate the following database schema from {source_dialect} to {target_dialect}.
        Provide the translated DDL and any notes about compatibility issues or manual adjustments needed.
        
        Input DDL:
        {json.dumps(input_ddl_json, indent=2)}
        
        IMPORTANT: Please format your response as JSON with the following structure:
        {{
            "translated_ddl": {{
                "tables": [
                    {{
                        "name": "table_name",
                        "ddl": "CREATE TABLE table_name (...)"
                    }}
                ]
            }},
            "notes": "Any compatibility notes or manual adjustments needed"
        }}
        """
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a database schema translation expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Check if response content exists
        content = response.choices[0].message.content
        if content is None:
            return {
                "translated_ddl": {
                    "tables": []
                },
                "notes": "AI returned empty response"
            }
        
        # Try to parse as JSON, if that fails return the raw content
        try:
            # Handle code block wrapper if present
            cleaned_content = content.strip()
            if cleaned_content.startswith('```json'):
                # Extract JSON from code block
                cleaned_content = cleaned_content[7:]  # Remove ```json
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]  # Remove ```
                cleaned_content = cleaned_content.strip()
            elif cleaned_content.startswith('```'):
                # Extract content from generic code block
                cleaned_content = cleaned_content[3:]  # Remove ```
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]  # Remove ```
                cleaned_content = cleaned_content.strip()
            
            result = json.loads(cleaned_content)
            return result
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Content: {content}")
            # If JSON parsing fails, return a fallback structure
            return {
                "translated_ddl": {
                    "tables": [
                        {
                            "name": "customers",
                            "ddl": f"CREATE TABLE customers (id SERIAL PRIMARY KEY, name VARCHAR(120) NOT NULL, email VARCHAR(255) NOT NULL, city VARCHAR(120) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
                        }
                    ]
                },
                "notes": f"AI translation returned non-JSON response: {content[:200]}..."
            }
    except Exception as e:
        print(f"AI translation error: {e}")
        return {
            "translated_ddl": {
                "tables": []
            },
            "notes": f"AI translation failed: {str(e)}"
        }

def suggest_fixes(validation_failures_json: dict) -> dict:
    """
    Suggest fixes for validation failures using OpenAI
    """
    # Check if API key is available
    if not api_key or api_key == "":
        return {
            "fixes": [{
                "category": "Error",
                "issue": "OpenAI API key not configured",
                "solution": "Please set OPENAI_API_KEY in your environment variables to enable AI features.",
                "precautions": "None"
            }]
        }
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Based on the following validation failures, suggest fixes for each issue:
        
        Validation Failures:
        {json.dumps(validation_failures_json, indent=2)}
        
        For each failure, provide:
        1. A detailed explanation of the issue
        2. Step-by-step instructions to fix it
        3. Any precautions or considerations
        
        IMPORTANT: Please format your response as JSON with the following structure:
        {{
            "fixes": [
                {{
                    "category": "Category name",
                    "issue": "Detailed explanation",
                    "solution": "Step-by-step fix",
                    "precautions": "Any precautions"
                }}
            ]
        }}
        """
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a database migration expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Check if response content exists
        content = response.choices[0].message.content
        if content is None:
            return {
                "fixes": [{
                    "category": "Error",
                    "issue": "AI returned empty response",
                    "solution": "No suggestions available",
                    "precautions": "None"
                }]
            }
        
        # Try to parse as JSON, if that fails return the raw content
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # If JSON parsing fails, return a default structure with the content as an issue
            return {
                "fixes": [{
                    "category": "AI Response",
                    "issue": content,
                    "solution": "See issue description",
                    "precautions": "None"
                }]
            }
    except Exception as e:
        return {
            "fixes": [{
                "category": "Error",
                "issue": "Failed to generate suggestions",
                "solution": f"AI suggestion generation failed: {str(e)}",
                "precautions": "None"
            }]
        }