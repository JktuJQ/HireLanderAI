document.addEventListener("DOMContentLoaded", function() {
    const status = document.getElementById("status");
    const language_select = document.getElementById("languageSelect");

    const editor = ace.edit("code-editor", {
      enableBasicAutocompletion: true,
      enableLiveAutocompletion: true,
      mode: `ace/mode/${language_select.value}`
    });
    editor.setTheme("ace/theme/chrome")

    language_select.addEventListener("change", function() {
        editor.session.setMode(`ace/mode/${language_select.value}`);
    })

    socket.on("disconnect", function() {
        status.textContent = "Disconnected from server";
    });

    socket.on("connect_error", function(error) {
        console.error("Connection error:", error);
        status.textContent = "Connection error";
    });

    socket.on("coding_field_update", function(data) {
        if (data.code !== editor.value) {
            const cursorPosition = editor.selectionStart;
            const scrollPosition = editor.scrollTop;
            
            editor.value = data.code;
            
            editor.selectionStart = cursorPosition;
            editor.selectionEnd = cursorPosition;
            editor.scrollTop = scrollPosition;
        }
    });

    let timeout = null;
    editor.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            socket.emit("coding_field_update", { code: editor.value });
        }, 100);
    });

    socket.on("user_count", function(data) {
        status.textContent = `Connected users: ${data.count}`;
    });
});