// The TxChecker API. Use localhost while testing; switch to your Lambda URL after deploying.
const API_URL = "https://j44ndfv7xkzupywgq3aycifgwq0ktknn.lambda-url.us-east-2.on.aws";

const form = document.getElementById("form");
const hashInput = document.getElementById("hash");
const message = document.getElementById("message");
const results = document.getElementById("results");

form.addEventListener("submit", async function (event) {
  event.preventDefault(); // stop the page from reloading

  message.textContent = "Checking...";
  results.innerHTML = "";

  try {
    const response = await fetch(API_URL + "/analyze/" + hashInput.value.trim());
    const data = await response.json();

    if (!response.ok) {
      message.textContent = "Error: " + data.detail;
      return;
    }

    message.textContent = "";
    showResults(data);
  } catch (error) {
    message.textContent = "Could not reach the API. Is it running?";
  }
});

function showResults(data) {
  const tx = data.transaction;

  if (data.findings.length === 0) {
    addBox("No findings. This only means none of the 3 rules matched.", "");
  }

  for (const finding of data.findings) {
    addBox(finding.severity.toUpperCase() + ": " + finding.message, finding.severity);
  }

  addBox(
    "Function: " + (data.decoded_input.function_signature || "none") + "\n" +
    "Status: " + tx.status + "\n" +
    "From: " + tx.from_address + "\n" +
    "To: " + (tx.to_address || "contract creation") + "\n" +
    "Block: " + (tx.block_number || "pending"),
    ""
  );
}

// Adds one result box. textContent keeps API text from being run as HTML.
function addBox(text, className) {
  const box = document.createElement("div");
  box.className = "box " + className;
  box.textContent = text;
  results.appendChild(box);
}
