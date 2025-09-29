document.addEventListener("DOMContentLoaded", function() {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");

    chatForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        const messageText = userInput.value.trim();
        if (messageText === "") return;

        // Hiển thị tin nhắn của người dùng
        appendMessage(messageText, "user");
        userInput.value = "";

        try {
            // Gửi tin nhắn tới server
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: messageText }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            // Hiển thị câu trả lời của bot
            appendMessage(data.response, "bot");

        } catch (error) {
            console.error("Error:", error);
            appendMessage("Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.", "bot");
        }
    });

    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${sender}-message`);
        
        const p = document.createElement("p");
        p.textContent = text;
        messageDiv.appendChild(p);

        chatBox.appendChild(messageDiv);
        // Tự động cuộn xuống tin nhắn mới nhất
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
