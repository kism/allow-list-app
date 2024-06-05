function printSuccess(message) {
  document.getElementById("CONNECTION_TEST").innerHTML = message;
  document.getElementById("CONNECTION_TEST").style.color = "#00FF00";
  document.getElementById("REDIRECT").style.display = "initial";
}

function printFailure(message) {
  document.getElementById("CONNECTION_TEST").innerHTML = message;
  document.getElementById("CONNECTION_TEST").style.color = "#FFCCCC";
}

function checkAuthentication() {
  fetch("checkauth", {
    method: "GET",
  }).then((response) => {
    if (response.ok) {
      printSuccess(`Already authenticated!`);
    }
  });
}

document.getElementById("AUTH_FORM").onsubmit = async function (event) {
  event.preventDefault(); // Prevent the default form submission

  // Collect form data
  const formData = new FormData(this);

  try {
    // Send form data using Fetch API
    const response = await fetch("authenticate", {
      method: "POST",
      body: formData,
    });

    // Check if the request was successful
    if (response.ok) {
      printSuccess(`Authenticated!`);
    } else {
      printFailure(`Authentication Failure`);
    }

    // // Process the response ∏(e.g., display a success message)
    // const result = await response.text();
    // document.getElementById('CONNECTION_TEST').innerText = result;
  } catch (error) {
    // Handle errors (e.g., display an error message)
    printFailure("Form submission failed: " + error.message);
  }
};

checkAuthentication();
