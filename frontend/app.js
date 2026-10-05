let msalInstance;
let apiScope;

const $ = (id) => document.getElementById(id);

function showError(message) {
  $("error").textContent = message || "";
}

// --- Setup -----------------------------------------------------------------

async function init() {
  const cfg = await (await fetch("/config")).json();
  apiScope = cfg.apiScope;

  msalInstance = new msal.PublicClientApplication({
    auth: {
      clientId: cfg.webClientId,
      authority: `https://login.microsoftonline.com/${cfg.tenantId}`,
      redirectUri: window.location.origin,
      postLogoutRedirectUri: window.location.origin,
    },
    // sessionStorage: tokens are gone when the tab closes.
    cache: { cacheLocation: "sessionStorage" },
  });

  await msalInstance.initialize();

  // If we just came back from Entra, this finishes the code + PKCE exchange.
  const result = await msalInstance.handleRedirectPromise();
  if (result && result.account) {
    msalInstance.setActiveAccount(result.account);
  } else {
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) msalInstance.setActiveAccount(accounts[0]);
  }

  await render();
}

// --- Sign-in / sign-out ----------------------------------------------------

function signIn() {
  msalInstance.loginRedirect({
    scopes: [apiScope],
    // Always show "Pick an account", even if an Entra session cookie exists.
    prompt: "select_account",
  });
}

function signOut() {
  // Clears MSAL's token cache AND ends the Entra session cookie.
  msalInstance.logoutRedirect({ account: msalInstance.getActiveAccount() });
}

// --- Tokens ----------------------------------------------------------------

async function getToken(forceRefresh = false) {
  const account = msalInstance.getActiveAccount();
  try {
    // Uses the cached token, or silently renews it with the refresh token.
    const result = await msalInstance.acquireTokenSilent({
      scopes: [apiScope],
      account,
      forceRefresh,
    });
    return result.accessToken;
  } catch (err) {
    if (err instanceof msal.InteractionRequiredAuthError) {
      // Refresh token expired or revoked: the user must sign in again.
      await msalInstance.acquireTokenRedirect({ scopes: [apiScope], account });
      return null; // the page navigates away
    }
    throw err;
  }
}

// Calls our API with a bearer token. On 401, retries once with a fresh token.
async function callApi(path, options = {}) {
  for (const forceRefresh of [false, true]) {
    const token = await getToken(forceRefresh);
    if (!token) return null;

    const res = await fetch(path, {
      ...options,
      headers: { ...(options.headers || {}), Authorization: `Bearer ${token}` },
    });
    if (res.status !== 401) return res;
  }
  showError("Your session could not be renewed. Please sign out and sign in again.");
  return null;
}

// --- UI --------------------------------------------------------------------

async function render() {
  const account = msalInstance.getActiveAccount();
  $("signed-in").classList.toggle("hidden", !account);
  $("signed-out").classList.toggle("hidden", !!account);

  if (!account) {
    $("status").textContent = "Not signed in.";
    return;
  }

  $("status").textContent = "Signed in.";
  $("user-name").textContent = account.name || account.username;

  // Roles come from the SERVER's view of the validated token,
  // not from decoding the token in the browser.
  const res = await callApi("/whoami");
  if (!res) return;
  if (res.status === 403) {
    $("user-roles").textContent = "none";
    showError("You are signed in but have no AskHR role. Ask an administrator for access.");
    return;
  }
  const me = await res.json();
  $("user-roles").textContent = me.roles.join(", ");
}

function appendMessage(text, isUser) {
  const div = document.createElement("div");
  if (isUser) div.className = "msg-user";
  // textContent, never innerHTML: user and model text must not become HTML.
  div.textContent = text;
  $("log").appendChild(div);
}

async function sendMessage(event) {
  event.preventDefault();
  const message = $("chat-input").value.trim();
  if (!message) return;

  $("chat-input").value = "";
  showError("");
  appendMessage(`You: ${message}`, true);

  const res = await callApi("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res) return;

  if (!res.ok) {
    showError(`Request failed (${res.status}).`);
    return;
  }
  const data = await res.json();
  appendMessage(`AskHR: ${data.reply}`, false);
}

async function forceRenew() {
  const token = await getToken(true);
  if (token) $("status").textContent = `Token renewed at ${new Date().toLocaleTimeString()}.`;
}

// --- Wire up ---------------------------------------------------------------

$("btn-signin").addEventListener("click", signIn);
$("btn-signout").addEventListener("click", signOut);
$("btn-renew").addEventListener("click", forceRenew);
$("chat-form").addEventListener("submit", sendMessage);

init().catch((err) => {
  console.error(err);
  showError(`Startup failed: ${err.message}`);
});