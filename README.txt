To run the program locally, it is recommended to create a virtual environment in the same folder where the code is. You can do that by executing the next command on your terminal:

`python -m venv .venv`

Then, activate it with the correct command for your terminal:

- **Bash / Git Bash:** `source .venv/bin/activate`
- **PowerShell:** `.venv\Scripts\Activate.ps1`

Once you are inside the virtual environment, use the following command to install all the required packages:

`pip install -r requirements.txt`

To run the server, execute:

`uvicorn main:app --reload` or `python -m uvicorn main:app --reload`

The API will be available at `http://127.0.0.1:8000`.