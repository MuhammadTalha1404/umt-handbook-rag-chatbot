const chat = document.getElementById("chat");
const input = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const sourcesEl = document.getElementById("sources");
const statusPill = document.getElementById("statusPill");

function addMessage(role, text){
  const row = document.createElement("div");
  row.className = `msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "Bot";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  row.appendChild(avatar);
  row.appendChild(bubble);

  if(role === "user"){
    row.style.flexDirection = "row-reverse";
  }

  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
}

function setSources(sources){
  sourcesEl.innerHTML = "";
  if(!sources || sources.length === 0){
    sourcesEl.innerHTML = '<div class="hint">No sources returned.</div>';
    return;
  }
  sources.forEach((s, idx) => {
    const div = document.createElement("div");
    div.className = "source";
    const meta = s.metadata || {};
    const title = meta.source || meta.file_name || meta.path || "unknown";
    const page = (meta.page !== undefined && meta.page !== null) ? `, page ${meta.page}` : "";
    div.innerHTML = `
      <span class="k">Source ${idx+1}: ${escapeHtml(title)}${escapeHtml(page)}</span>
      ${escapeHtml(s.snippet || "")}
    `;
    sourcesEl.appendChild(div);
  });
}

function escapeHtml(str){
  return (str || "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}

let typingRow = null;

function showTyping(){
  statusPill.textContent = "Thinking…";
  typingRow = document.createElement("div");
  typingRow.className = "msg bot";
  typingRow.innerHTML = `
    <div class="avatar">Bot</div>
    <div class="bubble">Typing<span style="opacity:.8">...</span></div>
  `;
  chat.appendChild(typingRow);
  chat.scrollTop = chat.scrollHeight;
}

function hideTyping(){
  statusPill.textContent = "Ready";
  if(typingRow){
    typingRow.remove();
    typingRow = null;
  }
}

async function send(){
  const text = input.value.trim();
  if(!text) return;

  addMessage("user", text);
  input.value = "";
  input.style.height = "auto";
  sendBtn.disabled = true;
  showTyping();

  try{
    const res = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({message: text})
    });

    const data = await res.json();
    hideTyping();

    if(!res.ok){
      addMessage("bot", data.error || "Something went wrong.");
      setSources([]);
    }else{
      addMessage("bot", data.answer || "(No answer returned)");
      setSources(data.sources || []);
    }
  }catch(err){
    hideTyping();
    addMessage("bot", "Network error. Check the Flask server is running.");
    setSources([]);
  }finally{
    sendBtn.disabled = false;
    input.focus();
  }
}

sendBtn.addEventListener("click", send);
sendBtn.addEventListener("click", () => console.log("send clicked"));


clearBtn.addEventListener("click", () => {
  chat.innerHTML = "";
  sourcesEl.innerHTML = '<div class="hint">Ask a question and I’ll show the top retrieved chunks here so you can verify the answer.</div>';
});

input.addEventListener("keydown", (e) => {
  if(e.key === "Enter" && !e.shiftKey){
    e.preventDefault();
    send();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 140) + "px";
});

// Welcome message
addMessage("bot", "Ask me anything from your knowledge base. I’ll show sources on the right.");
