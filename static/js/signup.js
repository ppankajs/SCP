document.addEventListener("DOMContentLoaded", function () { 
    console.log("Signup script loaded!");  // ✅ Check if script loads

    document.querySelector("#signup-form").addEventListener("submit", async function(event) {
        event.preventDefault(); // ✅ Stop form from submitting as GET
        console.log("Form submitted, preventing default...");

        const name = document.querySelector("input[name='name']").value.trim();
        const email = document.querySelector("input[name='email']").value.trim();
        const password = document.querySelector("input[name='password']").value.trim();

        if (!name || !email || !password) {
            alert("All fields are required!");
            return;
        }

        console.log("Sending POST request...");
        try {
            const response = await fetch("http://127.0.0.1:5000/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });

            const data = await response.json();
            console.log("Response received:", data);

            if (response.ok) {
                alert("Signup successful!");
                window.location.href = "/login";
            } else {
                alert("Error: " + data.message);
            }
        } catch (error) {
            console.error("Signup error:", error);
            alert("Something went wrong. Please try again.");
        }
    });
});
