from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.chains import ConversationChain 
from langchain.memory import ConversationBufferMemory
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit

from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.utilities.gitlab import GitLabAPIWrapper

from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

#import openai
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from context_manager import MCPContextManager
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load env var
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#Init openAI api
OpenAI.api_key = OPENAI_API_KEY

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API KEY not found!")

#Github
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_APP_PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")

'''if not all([GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_REPOSITORY]):
    raise ValueError("GitHub credentials not found.")'''

#GitLab
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
GITLAB_REPOSITORY = os.getenv("GITLAB_REPOSITORY")
GITLAB_BRANCH = os.getenv("GITLAB_BRANCH", "bot-branch")
GITLAB_BASE_BRANCH = os.getenv("GITLAB_BASE_BRANCH", "main")
'''if not all([GITLAB_URL, GITLAB_PERSONAL_ACCESS_TOKEN, GITLAB_REPOSITORY]):
    raise ValueError("GitLab credentials not found.")'''

#db
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
'''if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB]):
    raise ValueError("PostgreSQL credentials not found.")'''


class MCP:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=500
        )
        #init memoru to store cnv history
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        #init 
        self.context_manager = MCPContextManager()
        #init tools
        self.tools = self._initialize_tools()

        #init agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )

    def _initialize_tools(self):
        """Initialize and combine all available tools"""
        tools = []
        
        #init GitHub toolkit if credentials are available
        """if all([GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_REPOSITORY]):
            try:
                logger.info("Initializing GitHub toolkit")
                # Validate repository format
                if '/' not in GITHUB_REPOSITORY:
                    raise ValueError(f"GITHUB_REPOSITORY must be in format 'owner/repo', got: {GITHUB_REPOSITORY}")
                
                # Split repository into owner and repo
                repo_parts = GITHUB_REPOSITORY.split('/')
                if len(repo_parts) != 2:
                    raise ValueError(f"GITHUB_REPOSITORY must have exactly one '/', got: {GITHUB_REPOSITORY}")


                github = GitHubAPIWrapper(
                    github_app_id=GITHUB_APP_ID,
                    github_app_private_key=GITHUB_APP_PRIVATE_KEY,
                    github_repository=GITHUB_REPOSITORY
                )
                github_toolkit = GitHubToolkit.from_github_api_wrapper(github)
                tools.extend(github_toolkit.get_tools())
                logger.info("GitHub toolkit initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub toolkit: {str(e)}")
                logger.error(f"Check your GitHub configuration:")
                logger.error(f"  GITHUB_APP_ID: {'Set' if GITHUB_APP_ID else 'Not set'}")
                logger.error(f"  GITHUB_APP_PRIVATE_KEY: {'Set' if GITHUB_APP_PRIVATE_KEY else 'Not set'}")
                logger.error(f"  GITHUB_REPOSITORY: {GITHUB_REPOSITORY}")

        
        #init GitLab toolkit if credentials are available
        if all([GITLAB_URL, GITLAB_PERSONAL_ACCESS_TOKEN, GITLAB_REPOSITORY]):
            try:
                logger.info("Initializing GitLab toolkit")
                gitlab = GitLabAPIWrapper(
                    gitlab_url=GITLAB_URL,
                    gitlab_personal_access_token=GITLAB_PERSONAL_ACCESS_TOKEN,
                    gitlab_repository=GITLAB_REPOSITORY,
                    gitlab_branch=GITLAB_BRANCH,
                    gitlab_base_branch=GITLAB_BASE_BRANCH
                )
                gitlab_toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
                tools.extend(gitlab_toolkit.get_tools())
                logger.info("GitLab toolkit initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GitLab toolkit: {str(e)}") """#"""
        
        #init SQL toolkit if credentials are available
        if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB]):
            try:
                logger.info("Initializing SQL toolkit")
                db_uri = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
                db = SQLDatabase.from_uri(db_uri)
                sql_toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)
                tools.extend(sql_toolkit.get_tools())
                logger.info("SQL toolkit initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SQL toolkit: {str(e)}")
        
        return tools
    
    def interact(self, user_input):
        """Process user input and return AI response."""
        try:
            if user_input.lower() == "debug_sql":
            # Direct tool testing
                for tool in self.tools:
                    if tool.name == "sql_db_list_tables":
                        print(f"Testing {tool.name} directly...")
                        result = tool.run("")
                        print(f"Direct result: '{result}'")
                        return f"Direct tool result: {result}"
                        
            if not user_input.strip():
                return "Error: Empty input. Please provide a valid query."
            
            # Run the agent with the user input
            response = self.agent.invoke(user_input, chat_history=[])
            
            # Extract the actual response text from the dictionary
            if isinstance(response, dict):
                # Based on the response "AI: Hello! How can I assist you today?"
                # it seems the response is in the 'output' key
                response_text = response.get('output', '')
                
                # If 'output' isn't available, try other possible keys
                if not response_text and 'response' in response:
                    response_text = response['response']
                elif not response_text and 'content' in response:
                    response_text = response['content']
                elif not response_text and 'result' in response:
                    response_text = response['result']
                # Fallback: convert the whole response to string
                elif not response_text:
                    response_text = str(response)
            else:
                response_text = str(response)
            
            # Store interaction in custom context manager
            self.context_manager.add_context(user_input, response_text)
            
            return response_text
        except Exception as e:
            logger.error(f"Error during interaction: {str(e)}")
            return f"Error: {str(e)}"
        
    
    def save_context(self, filename="context.json"):
        try:
            memory_data = {
                "chat_history": [{"role": msg.type, "content": msg.content} for msg in self.memory.chat_memory.messages]
            }
            
            with open(filename, "w") as f:
                json.dump(memory_data, f, indent=2)
            
            logger.info(f"Context saved to {filename}")
            return f"Context saved to {filename}"
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
            return f"Error saving context: {str(e)}"

    def load_context(self, filename="context.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)

            self.memory.clear()
            from langchain.schema import HumanMessage, AIMessage
            for msg in data.get("chat_history", []):
                if msg["role"] == "human":
                    self.memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
                elif msg["role"] == "ai":
                    self.memory.chat_memory.add_message(AIMessage(content=msg["content"]))
            logger.info(f"Context loaded from {filename}")
            return f"Context loaded from {filename}"
        except FileNotFoundError:
            logger.warning("No saved context found")
            return "No saved context found!"
        except Exception as e:
            logger.error(f"Error loading context: {str(e)}")
            return f"Error loading context: {str(e)}"
        
    
    def get_available_tools(self):
        """Return a list of available tools for the user."""
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append({
                "name": tool.name,
                "description": tool.description
            })
        return tool_descriptions

    def test_database_connection(self):

        """Test database connection and show basic info"""
        try:
            # Test the connection
            db_uri = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
            print(f"Testing connection to: postgresql://{POSTGRES_USER}:***@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
            
            from langchain_community.utilities.sql_database import SQLDatabase
            db = SQLDatabase.from_uri(db_uri)
            
            # Try to get table info
            tables = db.get_usable_table_names()
            print(f"Connected successfully!")
            print(f"Found {len(tables)} tables: {tables}")
            
            # Try a simple query
            if tables:
                result = db.run("SELECT current_database(), current_user;")
                print(f"Database info: {result}")
            else:
                print("No tables found - database might be empty")
                
            return True
            
        except Exception as e:
            print(f"Database connection failed: {str(e)}")
            return False
        
   
if __name__ == "__main__":
    mcp = MCP()
    print("Welcome to MCP (Model Context Protocol)")
    print("Available commands: exit, quit, clear, save, load, tools")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break
        elif user_input.lower() == "clear":
            mcp.memory.clear()
            mcp.context_manager.clear_context()           
            print("Context cleared.")
            continue
        elif user_input.lower() == "save":
            result = mcp.save_context()
            print(result)
            continue
        elif user_input.lower() == "load":
            result = mcp.load_context()
            print(result)
            continue
        elif user_input.lower() == "tools":
            tools = mcp.get_available_tools()
            print("\nAvailable tools:")
            for tool in tools:
                print(f"- {tool['name']}: {tool['description']}")
            print()
            continue
        elif user_input.lower() == "test_db":
            result = mcp.test_database_connection()
            continue

        response = mcp.interact(user_input)
        print(f"MCP: {response}\n")
