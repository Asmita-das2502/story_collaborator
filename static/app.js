let currentUser = null;
let currentRoom = null;
let allUsers = {};

function showLoading(text = "Thinking...") {
  document.getElementById("loading-text").textContent = text;
  document.getElementById("loading-overlay").classList.remove("hidden");
}

function hideLoading() {
  document.getElementById("loading-overlay").classList.add("hidden");
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4000);
}

async function api(method, path, body = null) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const res = await fetch(path, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// SETUP
document.getElementById("enter-btn").addEventListener("click", async () => {
  const userName = document.getElementById("user-name-input").value.trim();
  const roomName = document.getElementById("room-name-input").value.trim();
  if (!userName || !roomName) {
    showError("setup-error", "Please enter both your name and a room name.");
    return;
  }
  showLoading("Setting up your story room...");
  try {
    let user;
    try {
      user = await api("POST", "/api/users", { name: userName });
    } catch (e) {
      const users = await api("GET", "/api/users");
      user = users.find((u) => u.name === userName);
      if (!user) throw new Error("Could not find or create user.");
    }
    currentUser = user;
    const rooms = await api("GET", "/api/rooms");
    let room = rooms.find((r) => r.name === roomName);
    if (!room) room = await api("POST", "/api/rooms", { name: roomName });
    currentRoom = room;
    const allUsersArr = await api("GET", "/api/users");
    allUsersArr.forEach((u) => {
      allUsers[u.id] = u.name;
    });
    document.getElementById("room-title").textContent = roomName;
    document.getElementById("user-badge").textContent = `👤 ${userName}`;
    document.getElementById("setup-screen").classList.add("hidden");
    document.getElementById("app-screen").classList.remove("hidden");
    await loadMessages();
  } catch (err) {
    showError("setup-error", err.message);
  } finally {
    hideLoading();
  }
});

document.getElementById("room-name-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") document.getElementById("enter-btn").click();
});

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".nav-btn")
      .forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => {
      p.classList.remove("active");
      p.classList.add("hidden");
    });
    btn.classList.add("active");
    const panel = document.getElementById("panel-" + btn.dataset.panel);
    panel.classList.remove("hidden");
    panel.classList.add("active");
  });
});

async function loadMessages() {
  try {
    const messages = await api("GET", `/api/rooms/${currentRoom.id}/messages`);
    renderMessages(messages);
  } catch (err) {
    console.error("Failed to load messages:", err);
  }
}

function renderMessages(messages) {
  const list = document.getElementById("messages-list");
  if (messages.length === 0) {
    list.innerHTML = '<div class="empty-state">No messages yet!</div>';
    return;
  }
  list.innerHTML = messages
    .map((msg) => {
      const isMe = msg.sender_id === currentUser.id;
      const senderName = allUsers[msg.sender_id] || "Unknown";
      const cogneeTag = msg.fed_to_cognee
        ? '<div class="message-cognee">✓ remembered</div>'
        : "";
      return `<div class="message-bubble ${isMe ? "mine" : "theirs"}"><div class="message-sender">${senderName}</div><div>${msg.content}</div>${cogneeTag}</div>`;
    })
    .join("");
  list.scrollTop = list.scrollHeight;
}

document.getElementById("send-btn").addEventListener("click", sendMessage);
document.getElementById("message-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

async function sendMessage() {
  const input = document.getElementById("message-input");
  const content = input.value.trim();
  if (!content) return;
  input.value = "";
  showLoading("Sending and remembering...");
  try {
    await api("POST", "/api/messages", {
      room_id: currentRoom.id,
      sender_id: currentUser.id,
      content,
    });
    await loadMessages();
  } catch (err) {
    console.error("Send failed:", err);
    input.value = content;
  } finally {
    hideLoading();
  }
}

document
  .getElementById("refresh-summary-btn")
  .addEventListener("click", async () => {
    showLoading("Reading your story memory...");
    try {
      const data = await api("GET", `/api/rooms/${currentRoom.id}/summary`);
      const el = document.getElementById("summary-content");
      el.textContent = data.summary;
      el.classList.remove("hidden");
    } catch (err) {
      console.error("Summary failed:", err);
    } finally {
      hideLoading();
    }
  });

document.getElementById("draft-chapter-btn").addEventListener("click", () => {
  document.getElementById("draft-form").classList.toggle("hidden");
});
document.getElementById("cancel-draft-btn").addEventListener("click", () => {
  document.getElementById("draft-form").classList.add("hidden");
});

document
  .getElementById("generate-chapter-btn")
  .addEventListener("click", async () => {
    const chapterNumber = parseInt(
      document.getElementById("chapter-number-input").value,
    );
    const title =
      document.getElementById("chapter-title-input").value.trim() || null;
    if (!chapterNumber || chapterNumber < 1) {
      alert("Please enter a valid chapter number.");
      return;
    }
    showLoading("Pulling story memory and drafting chapter...");
    try {
      await api("POST", `/api/rooms/${currentRoom.id}/draft-chapter`, {
        room_id: currentRoom.id,
        chapter_number: chapterNumber,
        title,
      });
      document.getElementById("draft-form").classList.add("hidden");
      await loadChapters();
    } catch (err) {
      console.error("Chapter draft failed:", err);
      alert("Failed to draft chapter: " + err.message);
    } finally {
      hideLoading();
    }
  });

async function loadChapters() {
  try {
    const chapters = await api("GET", `/api/rooms/${currentRoom.id}/chapters`);
    renderChapters(chapters);
  } catch (err) {
    console.error("Failed to load chapters:", err);
  }
}

function renderChapters(chapters) {
  const list = document.getElementById("chapters-list");
  if (chapters.length === 0) {
    list.innerHTML = '<div class="empty-state">No chapters yet!</div>';
    return;
  }
  list.innerHTML = chapters
    .map(
      (ch) => `
    <div class="chapter-card">
      <div class="chapter-card-header">
        <div class="chapter-card-title">Chapter ${ch.chapter_number}${ch.title ? ": " + ch.title : ""}</div>
        ${ch.is_draft ? '<span class="chapter-draft-badge">Draft</span>' : '<span class="chapter-draft-badge" style="background:#34d399">Final</span>'}
      </div>
      <div class="chapter-preview">${ch.content}</div>
    </div>`,
    )
    .join("");
}

document
  .querySelector('[data-panel="chapters"]')
  .addEventListener("click", loadChapters);

document.getElementById("recall-btn").addEventListener("click", askMemory);
document.getElementById("recall-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") askMemory();
});

async function askMemory() {
  const query = document.getElementById("recall-input").value.trim();
  if (!query) return;
  showLoading("Searching story memory...");
  try {
    const data = await api("POST", `/api/rooms/${currentRoom.id}/recall`, {
      query,
    });
    const el = document.getElementById("recall-answer");
    el.textContent = data.answer;
    el.classList.remove("hidden");
  } catch (err) {
    console.error("Recall failed:", err);
  } finally {
    hideLoading();
  }
}

let activeSuggestionType = "plot";

document.querySelectorAll(".suggestion-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".suggestion-btn")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeSuggestionType = btn.dataset.type;
  });
});

document
  .getElementById("get-suggestions-btn")
  .addEventListener("click", async () => {
    showLoading("Thinking about your story...");
    try {
      const data = await api(
        "GET",
        `/api/rooms/${currentRoom.id}/suggestions?suggestion_type=${activeSuggestionType}`,
      );
      const el = document.getElementById("suggestions-content");
      if (!el) {
        alert("suggestions-content element not found!");
        return;
      }
      el.textContent = data.suggestions;
      el.classList.remove("hidden");
    } catch (err) {
      console.error("Suggestions failed:", err);
      alert("Error: " + err.message);
    } finally {
      hideLoading();
    }
  });

document
  .getElementById("refresh-threads-btn")
  .addEventListener("click", async () => {
    showLoading("Analysing story threads...");
    try {
      const data = await api("GET", `/api/rooms/${currentRoom.id}/threads`);
      const el = document.getElementById("threads-content");
      if (!el) {
        alert("threads-content element not found!");
        return;
      }
      el.textContent = data.threads;
      el.classList.remove("hidden");
    } catch (err) {
      console.error("Threads failed:", err);
      alert("Error: " + err.message);
    } finally {
      hideLoading();
    }
  });
