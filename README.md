# AskHR: a role-aware HR/IT assistant on Azure

AskHR is an internal assistant that answers HR and IT policy questions from company documents. What it can read and do depends on who you are: your role (HR, Employee or IT) comes from your Microsoft Entra ID sign-in, and nothing typed in the chat can change it. An HR user asking for salary bands gets the answer; an employee asking the same question gets a polite refusal, because the search only ever returns documents their role is allowed to see. Actions work the same way: only IT users can open IT tickets, and profile lookups through Microsoft Graph are made on behalf of the signed-in user, so they only ever return that user's own data.

The app runs on Azure Container Apps with a managed identity, keeps its secrets in Key Vault, and is deployed from GitHub Actions using OpenID Connect, so no cloud password is stored anywhere.

## Tech stack

- **Backend:** Python, FastAPI, Uvicorn
- **Agent:** LangGraph, LangChain, OpenRouter (LLM), MCP (FastMCP) for tools
- **Identity:** Microsoft Entra ID, MSAL.js, MSAL for Python (On-Behalf-Of), PyJWT
- **Azure:** AI Search, Key Vault, Container Apps, managed identity
- **Observability:** Langfuse
- **Delivery:** Docker, GitHub Container Registry, GitHub Actions

## How to run

You'll need Python 3.12 or newer, the Azure CLI, an Azure account with your own Entra tenant, and an OpenRouter API key.

1. **Set up Entra ID.** Register an app `askhr-api` with the scope `access_as_user`, the app roles `HR`, `Employee` and `IT`, a client secret, and the delegated Graph permission `User.Read`. Register a second app `askhr-web` as a single-page application with the redirect URI `http://localhost:8000` and permission to `askhr-api`. Assign your test users to roles.

2. **Create the search service** and give yourself data access:

   ```powershell
   az login --tenant <tenant-id>
   az search service create --name <search-name> --resource-group <resource-group> --location <region> --sku free
   ```

   Assign yourself the *Search Service Contributor*, *Search Index Data Contributor* and *Search Index Data Reader* roles on the service.

3. **Install and configure:**

   ```powershell
   git clone https://github.com/AbhishekSahukar/role_based_agent.git
   cd role_based_agent
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   copy .env.example .env
   ```

   Fill in `.env` with your tenant ID, both client IDs, the `askhr-api` client secret, your OpenRouter key and model, and the search endpoint.

4. **Load the documents and start the app:**

   ```powershell
   python scripts\setup_index.py
   cd backend
   uvicorn app.main:app --reload
   ```

5. Open http://localhost:8000, sign in as a test user and ask a question.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.