1. Environment Setup
First, navigate to the project's root folder in your terminal.

1.1. Create the Virtual Environment

Execute the following command to create a virtual environment named .venv:

python -m venv .venv

1.2. Activate the Virtual Environment

You must activate the environment in your terminal session. Use the correct command for your operating system:

Windows (CMD): .\.venv\Scripts\activate

Windows (PowerShell): .\.venv\Scripts\Activate.ps1

macOS / Linux / Git Bash: source .venv/bin/activate

Once activated, you will see (.venv) at the beginning of your terminal prompt.

1.3. Install Dependencies

With the virtual environment active, install all the required packages from the requirements.txt file:

pip install -r requirements.txt

2. Running the Server
2.1. For Local Development (same machine)

To run the server and have it accessible only from your own computer (e.g., for testing with the client on the same device), use the following command. The --reload flag will automatically restart the server whenever you save a change in the code.

uvicorn main:app --reload

The API will be available at http://127.0.0.1:8000.

2.2. To Accept Connections from Other Machines (LAN)

This is the command you need if the client will run on a different computer on the same network. The --host 0.0.0.0 flag tells the server to listen for connections on all available network interfaces, not just the local one.

uvicorn main:app --host 0.0.0.0

When using this command, you will need to find the server's local IP address (e.g., 192.168.1.35) to connect from the client.

3. Running the Client
Open a new terminal, navigate to the project folder, and activate the same virtual environment as you did for the server. Then, run the client script:

python client.py

If the server is running on the same machine, you can use 127.0.0.1 when prompted for the IP address.

If the server is running on a different machine on the same network, you must input the server's local IP address (the one you found to connect to it).
