import os

# Set before main_api / agent imports so UnderwritingAgent.__init__ doesn't sys.exit
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key")
