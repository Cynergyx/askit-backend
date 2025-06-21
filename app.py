import os
from src.main import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the environment from the .env file, default to 'development'
env = os.getenv('FLASK_ENV', 'development')
config_name = f"config.{env.capitalize()}Config"

app = create_app(config_name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 8080)))