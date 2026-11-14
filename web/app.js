const form=document.querySelector("#chat-form"), input=document.querySelector("#message-input");
const messages=document.querySelector("#messages"), sendButton=document.querySelector("#send-button");
const micButton=document.querySelector("#mic-button"), typing=document.querySelector("#typing-row");
const searchToggle=document.querySelector("#search-toggle"), speechToggle=document.querySelector("#speech-toggle");
const stopSpeech=document.querySelector("#stop-speech"), modal=document.querySelector("#settings-modal");
const transcript=[];

let currentAudio=null;
let cachedVoices=[];

// =============================================================
// GLOBAL VOICE TURN-TAKING STATE MACHINE
// "idle"      : Live voice paused / off
// "listening" : User's turn to speak (Mic ON)
// "thinking"  : AI processing answer (Mic OFF)
// "speaking"  : AI speaking out loud (Mic OFF)
// "cooldown"  : 500ms safety pause after AI speech to avoid echo (Mic OFF)
// =============================================================
let voiceTurnState = "idle";
let isLiveVoiceActive = false;
let isAiSpeaking = false;
let silenceTimer = null;
const SILENCE_TIMEOUT = 1000; // 1s natural pause before auto-submitting user speech
let currentVoiceTranscript = "";
let recognitionInstance = null;

function loadVoices(){
 if("speechSynthesis" in window){
  try{ cachedVoices=window.speechSynthesis.getVoices()||[]; }catch{}
 }
}
if("speechSynthesis" in window){
 loadVoices();
 window.speechSynthesis.onvoiceschanged=loadVoices;
}

function setRobotSpeaking(active) {
  const fullRobot = document.querySelector("#full-bg-robot");
  const orb = document.querySelector("#voice-orb");
  const vp = document.querySelector("#voice-viewport");
  if (fullRobot) fullRobot.classList.toggle("speaking", active);
  if (orb) orb.classList.toggle("speaking", active);
  if (vp) vp.classList.toggle("speaking", active);
}

function stopAllAudio(){
 if(currentAudio){
  try{ currentAudio.pause(); currentAudio.currentTime=0; }catch{}
  currentAudio=null;
 }
 if("speechSynthesis" in window){
  try{ window.speechSynthesis.cancel(); }catch{}
 }
 isAiSpeaking = false;
 setRobotSpeaking(false);
 if(stopSpeech) stopSpeech.hidden=true;
}

let serverOnlineLabel = (!["localhost", "127.0.0.1"].includes(window.location.hostname)) ? "24/7 Cloud Server Online 🌐" : "Local server online";

function getOnlineStatusLabel(data){
 const isCloudHost = !["localhost", "127.0.0.1"].includes(window.location.hostname);
 if(data && (data.is_cloud || data.permanent_server || isCloudHost)){
  return "24/7 Cloud Server Online 🌐";
 }
 return "Local server online";
}

function setStatus(text,ok=true){
 const pill=document.querySelector("#server-status");
 if(pill){
  pill.classList.toggle("offline",!ok);
  pill.querySelector("span:last-child").textContent=text;
 }
}

function connection(textId,markId,text,ok){
 const el=document.querySelector(textId);
 if(el) el.textContent=text;
 const mark=document.querySelector(markId);
 if(mark){
  mark.textContent=ok?"●":"!";
  mark.classList.toggle("good",ok);
  mark.classList.toggle("bad",!ok);
 }
}

async function refreshStatus(){
 try{
  const response=await fetch("/api/status");
  if(!response.ok)throw Error();
  const data=await response.json();
  serverOnlineLabel=getOnlineStatusLabel(data);
  setStatus(serverOnlineLabel);

  const serverTitleEl=document.querySelector("#server-title-text");
  const serverNoteEl=document.querySelector("#server-location-note");
  if(data.is_cloud || !["localhost", "127.0.0.1"].includes(window.location.hostname)){
   if(serverTitleEl) serverTitleEl.textContent="24/7 Cloud Server";
   if(serverNoteEl) serverNoteEl.textContent="Global High Availability · Render";
  }else{
   if(serverTitleEl) serverTitleEl.textContent="Local server";
   if(serverNoteEl) serverNoteEl.textContent="Sirf is computer par";
  }

  const ready=data.gemini==="ready";
  const gemLabel=ready?"Connected · "+data.model:(data.gemini==="key_format_invalid"?"Key format invalid":"API key zaroori hai");
  connection("#gemini-status","#gemini-mark",gemLabel,ready);
  connection("#search-status","#search-mark",ready?"Grounded web jawab ready":"Gemini key ke baad ready",ready);
  connection("#anti-status","#anti-mark",data.antigravity_mcp?"MCP config taiyar":"Config nahi mili",data.antigravity_mcp);

  if(data.openai){
    const opReady=data.openai.status==="ready";
    const opLabel=opReady?(data.openai.summary||"Connected · OpenAI"):"Optional · Key / Codex CLI";
    connection("#openai-status","#openai-mark",opLabel,opReady);
    const opModeText=document.querySelector("#openai-mode-text");
    const opBadge=document.querySelector("#openai-badge-text");
    if(opModeText) opModeText.textContent=data.openai.summary||(opReady?"Ready":"Not configured");
    if(opBadge){
      opBadge.textContent=opReady?"● Ready":"○ Optional";
      opBadge.style.color=opReady?"#10b981":"#94a3b8";
    }
  }
  
  if(data.gmail){
   const gUser=data.gmail.user||"kumaranil70115@gmail.com";
   const gConn=Boolean(data.gmail.connected);
   const gLabel=gConn?"Connected · "+gUser:(data.gmail.configured?"Login error":"Password zaroori");
   connection("#gmail-status","#gmail-mark",gLabel,gConn);
   const gHelp=document.querySelector("#gmail-help");
   if(gHelp){
    gHelp.textContent=gConn?`Gmail connected hai (${gUser}). Unread inbox sync ready hai.`:`Gmail (${gUser}) connect karne ke liye 16-akshar ka App Password daalein.`;
   }
  }

  if(data.google_tools){
   renderTools(data.google_tools);
   const toolsStatus=document.querySelector("#tools-status");
   if(toolsStatus) toolsStatus.textContent=(data.google_tools.total||7)+" Tools Connected";
  }

  if(data.permissions){
   renderPermissions(data.permissions);
  }

  if(data.version){
   const bVer=document.querySelector("#brand-version-badge");
   if(bVer) bVer.textContent=data.version;
   const sVer=document.querySelector("#sidebar-version");
   if(sVer) sVer.textContent=data.version+" · Active";
   const mVer=document.querySelector("#modal-cur-version");
   if(mVer) mVer.textContent=data.version;
  }

  if(data.learning){
   const sLearn=document.querySelector("#learning-status");
   if(sLearn) sLearn.textContent=`⭐ ${data.learning.average_rating} (${data.learning.total_ratings}) · Auto-Improve`;
  }

  if(data.opensource_agents){
   const sAgents=document.querySelector("#agents-sidebar-status");
   if(sAgents) sAgents.textContent=`${data.opensource_agents.total} Free GitHub Agents`;
  }

  const keyHelp=document.querySelector("#key-help");
  const keyNotice=document.querySelector("#key-saved-notice");
  const keyInput=document.querySelector("#api-key");
  if(ready){
   if(keyNotice) keyNotice.textContent="✅ Gemini Key active hai (Google AI Studio model connected).";
   if(keyInput) keyInput.placeholder="Pehle se saved hai (••••••••••••••)";
  }else if(data.gemini==="key_format_invalid"){
   if(keyNotice) keyNotice.textContent="⚠️ Key format invalid hai. AI Studio se copy ki gayi key paste karein.";
   if(keyInput) keyInput.placeholder="Google AI Studio Key...";
  }else{
   if(keyNotice) keyNotice.textContent="ℹ️ Smart AI Live Core chal raha hai. Deep AI search ke liye free Gemini key save karein.";
   if(keyInput) keyInput.placeholder="Google AI Studio Key...";
  }
  if(keyHelp){
   keyHelp.textContent=ready?
    "Gemini 1.5 Flash connected hai. Key source: "+data.key_source+".":
    "Smart AI 24/7 online hai. Gemini Flash ke liye upar diye gaye link se 1-click free key banayein.";
  }
 }catch{
  setStatus("Server connect nahi hua",false);
 }
}

function speakBrowserFallback(clean, onFinished = null){
 if(!("speechSynthesis" in window)){
  if(onFinished) onFinished();
  return;
 }
 try{
  window.speechSynthesis.cancel();
  setTimeout(()=>{
   const utterance = new SpeechSynthesisUtterance(clean);
   if(!cachedVoices.length) loadVoices();
   // Prioritize natural high-quality human Hindi & Indian English neural voices
   const humanVoice = cachedVoices.find(v => /google\s*हिन्दी/i.test(v.name))
     || cachedVoices.find(v => /swara/i.test(v.name))
     || cachedVoices.find(v => /madhur/i.test(v.name))
     || cachedVoices.find(v => /^hi(-|_)/i.test(v.lang))
     || cachedVoices.find(v => /heera|neerja|prabhat/i.test(v.name))
     || cachedVoices.find(v => /natural/i.test(v.name) && v.lang.includes("IN"))
     || cachedVoices.find(v => v.lang.includes("IN"))
     || cachedVoices[0];
   if(humanVoice) utterance.voice = humanVoice;
   utterance.lang = humanVoice ? humanVoice.lang : "hi-IN";
   utterance.rate = 0.98;
   utterance.pitch = 1.02;

   let finished = false;
   const handleEnd = () => {
    if(finished) return;
    finished = true;
    isAiSpeaking = false;
    if(!isLiveVoiceActive || voiceTurnState !== "speaking") setRobotSpeaking(false);
    if(stopSpeech) stopSpeech.hidden = true;
    if(onFinished) onFinished();
    else if(isLiveVoiceActive && typeof onAiFinishedSpeaking === "function") onAiFinishedSpeaking();
   };

   utterance.onstart = () => {
    isAiSpeaking = true;
    setRobotSpeaking(true);
    if(stopSpeech) stopSpeech.hidden = false;
    if(isLiveVoiceActive){
     voiceTurnState = "speaking";
     if(typeof setVoiceStateUI === "function") setVoiceStateUI("speaking");
     if(typeof safeStopRecognition === "function") safeStopRecognition();
    }
   };
   utterance.onend = handleEnd;
   utterance.onerror = handleEnd;

   window.speechSynthesis.speak(utterance);
   window.speechSynthesis.resume();
  }, 50);
 }catch{
  isAiSpeaking = false;
  setRobotSpeaking(false);
  if(onFinished) onFinished();
  else if(isLiveVoiceActive && typeof onAiFinishedSpeaking === "function") onAiFinishedSpeaking();
 }
}

function safeEncodeURIComponent(str) {
  if (!str) return "";
  try {
    return encodeURIComponent(str);
  } catch (e) {
    try {
      if (typeof str.toWellFormed === "function") {
        return encodeURIComponent(str.toWellFormed());
      }
      const cleaned = str.replace(/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/g, "");
      return encodeURIComponent(cleaned);
    } catch (e2) {
      return encodeURI(str.replace(/[^\x00-\x7F]/g, ""));
    }
  }
}

function speak(text, onFinished = null){
 // In Live Voice mode, ALWAYS speak! Otherwise check speechToggle
 if(!speechToggle.checked && !isLiveVoiceActive){
  if(onFinished) onFinished();
  return;
 }
 try {
   stopAllAudio();
   const clean = text
     .replace(/https?:\/\/\S+/g, "")
     .replace(/[#*_`~\[\]\(\)\{\}\<\>\\\/|]/g, " ")
     .replace(/[✦⚡⭐🤖🧠👥🕵️💡💻⚖️🎯📋📌🙌👨‍💻🦙💎💬🔧🏗️]/g, "")
     .replace(/\s+/g, " ")
     .trim();
   if(!clean){
    if(onFinished) onFinished();
    return;
   }

   isAiSpeaking = true;
   setRobotSpeaking(true);
   if(isLiveVoiceActive){
    voiceTurnState = "speaking";
    if(typeof setVoiceStateUI === "function") setVoiceStateUI("speaking");
    if(typeof safeStopRecognition === "function") safeStopRecognition();
   }

   if(stopSpeech) stopSpeech.hidden = false;

   const safeSlice = typeof clean.toWellFormed === "function"
     ? clean.toWellFormed().slice(0, 450)
     : Array.from(clean).slice(0, 350).join("");

   const audioUrl = "/api/tts?text=" + safeEncodeURIComponent(safeSlice);
   const audio = new Audio(audioUrl);
   currentAudio = audio;

   let finished = false;
   const handleEnd = () => {
    if(finished) return;
    finished = true;
    isAiSpeaking = false;
    currentAudio = null;
    if(!isLiveVoiceActive || voiceTurnState !== "speaking") setRobotSpeaking(false);
    if(stopSpeech) stopSpeech.hidden = true;
    if(onFinished) onFinished();
    else if(isLiveVoiceActive && typeof onAiFinishedSpeaking === "function") onAiFinishedSpeaking();
   };

   audio.onplay = () => {
    isAiSpeaking = true;
    setRobotSpeaking(true);
    if(stopSpeech) stopSpeech.hidden = false;
    if(isLiveVoiceActive){
     voiceTurnState = "speaking";
     if(typeof setVoiceStateUI === "function") setVoiceStateUI("speaking");
     if(typeof safeStopRecognition === "function") safeStopRecognition();
    }
   };
   audio.onended = handleEnd;
   audio.onerror = () => {
    currentAudio = null;
    speakBrowserFallback(safeSlice, handleEnd);
   };

   audio.play().catch(() => {
    currentAudio = null;
    speakBrowserFallback(safeSlice, handleEnd);
   });
 } catch (err) {
   console.warn("speak error handled gracefully:", err);
   isAiSpeaking = false;
   if(onFinished) onFinished();
 }
}

function addMessage(role,text,sources=[],options={}){
 const article=document.createElement("article");
 article.className="message "+role;
 const avatar=document.createElement("div");
 if(role==="user"){
  avatar.className="avatar avatar-user";
  avatar.innerHTML='<svg viewBox="0 0 24 24" class="avatar-user-svg"><path fill="#77e7c0" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>';
 }else{
  avatar.className="avatar avatar-humanoid";
  avatar.innerHTML='<svg viewBox="0 0 36 36" class="avatar-humanoid-svg"><circle cx="18" cy="18" r="17" fill="#111c2e" stroke="#38bdf8" stroke-width="1.5"/><path d="M10 16c0-6 3.5-10 8-10s8 4 8 10c0 1-.4 2-.8 3-1.2-3-4-4.5-7.2-4.5s-6 1.5-7.2 4.5c-.5-1-.8-2-.8-3z" fill="#38bdf8" opacity="0.85"/><ellipse cx="18" cy="17" rx="6.5" ry="7.5" fill="#fce7f3"/><ellipse cx="15.5" cy="16" rx="1.2" ry="1" fill="#0284c7"/><ellipse cx="20.5" cy="16" rx="1.2" ry="1" fill="#0284c7"/><circle cx="15.8" cy="15.7" r="0.4" fill="#ffffff"/><circle cx="20.8" cy="15.7" r="0.4" fill="#ffffff"/><circle cx="14" cy="18.5" r="1.2" fill="#f43f5e" opacity="0.45"/><circle cx="22" cy="18.5" r="1.2" fill="#f43f5e" opacity="0.45"/><path d="M16 20.2 Q18 22 20 20.2" fill="none" stroke="#e11d48" stroke-width="1.2" stroke-linecap="round"/><path d="M12 28 c1.5-3 3.5-4 6-4s4.5 1 6 4" fill="none" stroke="#38bdf8" stroke-width="2"/></svg>';
 }
 const content=document.createElement("div");
 content.className="message-content";
 const sender=document.createElement("span");
 sender.className="sender";
 sender.textContent=role==="user"?"AAP":"SMART AI";
 const time=document.createElement("small");
 time.textContent=new Date().toLocaleTimeString("hi-IN",{hour:"2-digit",minute:"2-digit"});
 sender.append(time);
 const bubble=document.createElement("div");
 bubble.className="bubble";
 const body=document.createElement("div");
 body.className="message-text";
 body.textContent=text;
 bubble.append(body);

 if(options && options.attachments && options.attachments.length){
  const attWrap=document.createElement("div");
  attWrap.className="msg-attachments";
  options.attachments.forEach(att=>{
   if(att.dataUrl && att.type && att.type.startsWith("image/")){
    const thumbWrap=document.createElement("div");
    thumbWrap.className="msg-thumb-wrap";
    const img=document.createElement("img");
    img.src=att.dataUrl;
    img.alt=att.name||"image";
    thumbWrap.appendChild(img);
    attWrap.appendChild(thumbWrap);
   } else {
    const fcard=document.createElement("div");
    fcard.className="msg-file-card";
    const sizeKb=((att.size||0)/1024).toFixed(1)+" KB";
    fcard.innerHTML=`<span>📄</span><strong>${att.name||"File"}</strong><small>${sizeKb}</small>`;
    attWrap.appendChild(fcard);
   }
  });
  bubble.prepend(attWrap);
 }

 if(options.collaborating_agent){
  const colAgent=options.collaborating_agent;
  const aBadge=document.createElement("div");
  aBadge.className="agent-collab-badge";
  const reasonAttr = colAgent.reason ? ` title="${colAgent.reason.replace(/"/g, '&quot;')}"` : "";
  aBadge.innerHTML=`
    <span class="acb-icon">${colAgent.icon||"🤖"}</span>
    <span class="acb-text"${reasonAttr}>🧠 Autonomous Agent: <strong>${colAgent.name}</strong> (${colAgent.category||"Agent"})</span>
    <a href="${colAgent.github_url}" target="_blank" rel="noopener noreferrer" class="acb-link" title="Open ${colAgent.name} GitHub Repository">GitHub ↗</a>
  `;
  bubble.prepend(aBadge);
 }

 if(sources.length){
  const box=document.createElement("div");
  box.className="sources";
  const heading=document.createElement("strong");
  heading.textContent="Google sources";
  box.append(heading);
  sources.forEach(source=>{
   try{
    const url=new URL(source.url);
    if(url.protocol!=="https:")return;
    const link=document.createElement("a");
    link.href=url.href; link.target="_blank"; link.rel="noopener noreferrer";
    link.textContent=source.title||url.hostname;
    box.append(link);
   }catch{}
  });
  if(box.querySelectorAll("a").length)bubble.append(box);
 }

 if(options.permission_blocked){
  const pBox=document.createElement("div");
  pBox.className="perm-prompt-box";
  pBox.innerHTML=`
   <div class="perm-alert-title">🔒 <strong>Permission Blocked</strong></div>
   <div class="perm-alert-desc">Aapke niyam ke anusar yeh action bina permission allow kiye rok diya gaya hai.</div>
   <button class="perm-open-modal-btn" type="button">🛡️ Permissions Allow Karein</button>
  `;
  pBox.querySelector(".perm-open-modal-btn").addEventListener("click",()=>{
   if(permsModal) permsModal.showModal();
  });
  bubble.append(pBox);
 }

 if(role==="assistant"){
  const speakBtn=document.createElement("button");
  speakBtn.className="speak-msg-btn";
  speakBtn.type="button";
  speakBtn.innerHTML="🔊 <span>Bolkar suniye</span>";
  speakBtn.addEventListener("click",()=>speak(text));
  bubble.append(speakBtn);

  // ⭐ Continuous Self-Learning Star Rating & Feedback Bar
  const feedbackBar=document.createElement("div");
  feedbackBar.className="msg-feedback-bar";
  feedbackBar.innerHTML=`
    <span class="msg-feedback-label">⭐ AI Rating & Feedback:</span>
    <div class="star-rating-group">
      <button class="star-btn" data-star="1" type="button" title="1 Star - Galti hui">★</button>
      <button class="star-btn" data-star="2" type="button" title="2 Star - Adhoora">★</button>
      <button class="star-btn" data-star="3" type="button" title="3 Star - Thik-thaak">★</button>
      <button class="star-btn" data-star="4" type="button" title="4 Star - Acha hai">★</button>
      <button class="star-btn" data-star="5" type="button" title="5 Star - Perfect">★</button>
    </div>
    <span class="feedback-status-tag" style="display:none"></span>
  `;

  const corrBox=document.createElement("div");
  corrBox.className="feedback-correction-box";
  corrBox.style.display="none";
  corrBox.innerHTML=`
    <div class="fc-title">🧠 <span>Smart AI ko sikhao taki agli baar galti na ho:</span></div>
    <div class="fc-chips">
      <span class="fc-chip" data-tag="Galat Jankari">Galat Jankari</span>
      <span class="fc-chip" data-tag="Adhoora Jawab">Adhoora Jawab</span>
      <span class="fc-chip" data-tag="Format ya Point-Wise">Format / Points</span>
      <span class="fc-chip" data-tag="Bhasa ya Tone">Bhasa / Tone</span>
    </div>
    <div class="fc-input-row">
      <input type="text" class="fc-input" placeholder="Sahi niyam likhein... (e.g. Agli baar point-wise jawab do)" maxlength="300">
      <button type="button" class="fc-submit-btn">Sikhao 🧠</button>
    </div>
  `;

  let chosenRating=0;
  const starBtns=feedbackBar.querySelectorAll(".star-btn");
  const statusTag=feedbackBar.querySelector(".feedback-status-tag");

  starBtns.forEach(btn=>{
    btn.addEventListener("mouseenter",()=>{
      if(chosenRating>0) return;
      const sVal=parseInt(btn.dataset.star,10);
      starBtns.forEach((b,idx)=>{
        b.classList.toggle("rated-gold",idx<sVal);
      });
    });
    btn.addEventListener("mouseleave",()=>{
      if(chosenRating>0) return;
      starBtns.forEach(b=>b.classList.remove("rated-gold"));
    });
    btn.addEventListener("click",async()=>{
      if(chosenRating>0) return;
      chosenRating=parseInt(btn.dataset.star,10);
      starBtns.forEach((b,idx)=>{
        b.classList.toggle("rated-gold",idx<chosenRating);
        b.disabled=true;
        b.style.cursor="default";
      });

      const uQuery=options.userQuery||"";
      if(chosenRating>=4){
        try{
          await fetch("/api/feedback",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({rating:chosenRating,query:uQuery,response:text,feedback:"Acha laga / Perfect"})
          });
          statusTag.textContent="⭐ Dhanyawaad! Saved.";
          statusTag.style.display="inline-block";
          refreshStatus();
        }catch{}
      }else{
        corrBox.style.display="block";
        const inp=corrBox.querySelector(".fc-input");
        if(inp) inp.focus();
      }
    });
  });

  corrBox.querySelectorAll(".fc-chip").forEach(chip=>{
    chip.addEventListener("click",()=>chip.classList.toggle("selected"));
  });

  const submitCorrBtn=corrBox.querySelector(".fc-submit-btn");
  if(submitCorrBtn){
    submitCorrBtn.addEventListener("click",async()=>{
      const inp=corrBox.querySelector(".fc-input");
      const feedbackText=(inp?inp.value:"").trim();
      const selectedTags=Array.from(corrBox.querySelectorAll(".fc-chip.selected")).map(c=>c.dataset.tag);
      const uQuery=options.userQuery||"";
      try{
        submitCorrBtn.disabled=true;
        submitCorrBtn.textContent="Sikh raha hoon…";
        await fetch("/api/feedback",{
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({
            rating:chosenRating||2,
            query:uQuery,
            response:text,
            feedback:feedbackText,
            tags:selectedTags
          })
        });
        corrBox.innerHTML=`<div style="font-size:11px;color:#34d399;font-weight:600;padding:4px 0">✅ Sikh Liya! Smart AI ne yeh niyam permanently save kar liya hai. Agli baar yeh galti nahi karega!</div>`;
        statusTag.textContent=`⭐ ${chosenRating}/5 - Learned!`;
        statusTag.style.display="inline-block";
        refreshStatus();
      }catch(e){
        submitCorrBtn.disabled=false;
        submitCorrBtn.textContent="Dobara koshish karein";
      }
    });
  }

  bubble.append(feedbackBar,corrBox);
 }

 // ⏩ Continuous Autonomous Project / Task Pipeline ("next fir auto start ho")
 if (options && options.next_step) {
  const ns = options.next_step;
  if (ns.completed) {
   const compBadge = document.createElement("div");
   compBadge.className = "pipeline-completed-badge";
   compBadge.innerHTML = `<span>✅</span> <strong>Project Complete!</strong> Sabhi phases safalta se poore ho gaye hain.`;
   bubble.append(compBadge);
  } else if (ns.auto_start && ns.prompt) {
   const pipeCard = document.createElement("div");
   pipeCard.className = "auto-pipeline-card";
   let remaining = ns.delay_seconds || 3;
   let isPaused = false;
   let timerId = null;

   pipeCard.innerHTML = `
     <div class="pipeline-header">
       <span class="pipeline-badge">⚡ AUTO PIPELINE · STEP ${ns.step_number || 2} / ${ns.total_steps || 3}</span>
       <span class="pipeline-timer">Auto-start <b class="pipeline-secs">${remaining}s</b> me...</span>
     </div>
     <div class="pipeline-task-desc">Agla Task: <strong>${ns.title || "Next Milestone"}</strong></div>
     <div class="pipeline-progress-track">
       <div class="pipeline-progress-fill" style="animation-duration: ${remaining}s"></div>
     </div>
     <div class="pipeline-actions">
       <button type="button" class="pipeline-btn run-btn" title="Turant agla step chalu karein">Turant Chalao ⏩</button>
       <button type="button" class="pipeline-btn pause-btn" title="Timer rokein">⏸️ Rokein</button>
       <button type="button" class="pipeline-btn cancel-btn" title="Auto-start cancel karein">✕ Cancel</button>
     </div>
   `;

   const secsEl = pipeCard.querySelector(".pipeline-secs");
   const pauseBtn = pipeCard.querySelector(".pause-btn");
   const runBtn = pipeCard.querySelector(".run-btn");
   const cancelBtn = pipeCard.querySelector(".cancel-btn");
   const fillEl = pipeCard.querySelector(".pipeline-progress-fill");

   const executeStep = () => {
    if (timerId) clearInterval(timerId);
    pipeCard.classList.add("pipeline-running");
    pipeCard.innerHTML = `<div class="pipeline-started-msg">🚀 <strong>Step ${ns.step_number || 2}:</strong> Chalu ho gaya hai… Jawab taiyar ho raha hai!</div>`;
    sendMessage(ns.prompt);
   };

   runBtn.addEventListener("click", () => {
    executeStep();
   });

   pauseBtn.addEventListener("click", () => {
    isPaused = !isPaused;
    if (isPaused) {
     pauseBtn.textContent = "▶️ Chalu Karein";
     if (fillEl) fillEl.style.animationPlayState = "paused";
    } else {
     pauseBtn.textContent = "⏸️ Rokein";
     if (fillEl) fillEl.style.animationPlayState = "running";
    }
   });

   cancelBtn.addEventListener("click", () => {
    if (timerId) clearInterval(timerId);
    pipeCard.remove();
   });

   timerId = setInterval(() => {
    if (isPaused) return;
    remaining--;
    if (secsEl) secsEl.textContent = `${remaining}s`;
    if (remaining <= 0) {
     clearInterval(timerId);
     executeStep();
    }
   }, 1000);

   bubble.append(pipeCard);
  }
 }

 // 💬 Interactive WhatsApp Automation Card
 if(options.whatsapp_card || (options.client_action && (options.client_action.type === "whatsapp_send" || options.client_action.app === "whatsapp"))){
   const wc = options.whatsapp_card || options.client_action;
   const waCard = document.createElement("div");
   waCard.className = "chat-whatsapp-card";
   const cleanNum = (wc.phone || "").replace(/[^0-9]/g, "");
   const initialMsg = wc.message_text || "";
   const isOpenOnly = Boolean(wc.is_open || !initialMsg);

   const initialWaMe = cleanNum
     ? (initialMsg ? `https://wa.me/${cleanNum}?text=${safeEncodeURIComponent(initialMsg)}` : `https://wa.me/${cleanNum}`)
     : (initialMsg ? `https://api.whatsapp.com/send?text=${safeEncodeURIComponent(initialMsg)}` : `https://api.whatsapp.com/send`);
   const initialWebUrl = cleanNum
     ? (initialMsg ? `https://web.whatsapp.com/send?phone=${cleanNum}&text=${safeEncodeURIComponent(initialMsg)}` : `https://web.whatsapp.com/send?phone=${cleanNum}`)
     : (initialMsg ? `https://web.whatsapp.com/send?text=${safeEncodeURIComponent(initialMsg)}` : `https://web.whatsapp.com`);

   if (isOpenOnly) {
     waCard.innerHTML = `
       <div class="wa-card-header">
         <span class="wa-badge">💬 WhatsApp Quick Open</span>
         <span class="wa-status-pill">Ready</span>
       </div>
       <div class="wa-card-body">
         <div class="wa-field-row">
           <span class="wa-label">📱 Action:</span>
           <strong class="wa-val">WhatsApp App & Web Connect</strong>
         </div>
       </div>
       <div class="wa-card-actions">
         <a href="https://api.whatsapp.com/send" target="_blank" rel="noopener noreferrer" class="wa-send-btn primary-wa-btn">
           <span>💬 Open WhatsApp App</span>
         </a>
         <a href="https://web.whatsapp.com" target="_blank" rel="noopener noreferrer" class="wa-send-btn secondary-wa-btn">
           <span>💻 WhatsApp Web</span>
         </a>
       </div>
     `;
   } else {
     waCard.innerHTML = `
       <div class="wa-card-header">
         <span class="wa-badge">💬 WhatsApp Automation</span>
         <span class="wa-status-pill">Ready to Send</span>
       </div>
       <div class="wa-card-body">
         <div class="wa-field-row">
           <span class="wa-label">👤 Recipient:</span>
           <strong class="wa-val">${wc.contact_name || wc.phone || "WhatsApp Chat"}</strong>
         </div>
         ${wc.phone ? `<div class="wa-field-row"><span class="wa-label">📱 Number:</span> <span class="wa-val-phone">${wc.phone}</span></div>` : ''}
         <div class="wa-msg-bubble">
           <div class="wa-msg-label">📝 Message Preview (Aap chahein toh edit kar sakte hain):</div>
           <textarea class="wa-msg-edit" rows="2" placeholder="Message text...">${initialMsg}</textarea>
         </div>
       </div>
       <div class="wa-card-actions">
         <a href="${initialWaMe}" target="_blank" rel="noopener noreferrer" class="wa-send-btn primary-wa-btn">
           <span>🚀 Send on WhatsApp</span>
         </a>
         <a href="${initialWebUrl}" target="_blank" rel="noopener noreferrer" class="wa-send-btn secondary-wa-btn">
           <span>💻 WhatsApp Web</span>
         </a>
       </div>
     `;
     const editArea = waCard.querySelector(".wa-msg-edit");
     const sendBtn = waCard.querySelector(".primary-wa-btn");
     const webBtn = waCard.querySelector(".secondary-wa-btn");
     if (editArea && sendBtn && webBtn) {
       editArea.addEventListener("input", () => {
         const newText = safeEncodeURIComponent(editArea.value.trim());
         if(cleanNum){
           sendBtn.href = `https://wa.me/${cleanNum}?text=${newText}`;
           webBtn.href = `https://web.whatsapp.com/send?phone=${cleanNum}&text=${newText}`;
         } else {
           sendBtn.href = `https://api.whatsapp.com/send?text=${newText}`;
           webBtn.href = `https://web.whatsapp.com/send?text=${newText}`;
         }
       });
     }
   }
   bubble.append(waCard);
 }

 // 🎵 Interactive Media / YouTube Player Card in Chat
 if(options.media_card || (options.client_action && options.client_action.type === "youtube")){
   const mc = options.media_card || options.client_action;
   const mediaCard = document.createElement("div");
   mediaCard.className = "chat-media-action-card";
   mediaCard.innerHTML = `
     <div class="media-card-title-row">
       <span class="media-card-badge">🎵</span>
       <div>
         <div class="media-card-title">${mc.title || "YouTube Music"}</div>
         <div class="media-card-sub">YouTube Background Media, Inline & App Play</div>
       </div>
     </div>
     <div class="media-card-btn-group">
       <button type="button" class="media-inline-play-btn">
         <span>📺 Yahan Play Karein</span>
       </button>
       <a href="${mc.web_url}" target="_blank" rel="noopener noreferrer" class="media-action-link-btn" title="YouTube App ya Browser me kholein">
         <span>▶️ YouTube Open</span>
       </a>
       <button type="button" class="media-bg-toggle-btn">
         <span>🔊 Background Player</span>
       </button>
     </div>
     <div class="media-inline-player-box" style="display:none; margin-top:10px; border-radius:12px; overflow:hidden; aspect-ratio:16/9; box-shadow:0 4px 18px rgba(0,0,0,0.5);">
       <iframe width="100%" height="100%" src="" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
     </div>
   `;
   const inlineBtn = mediaCard.querySelector(".media-inline-play-btn");
   const playerBox = mediaCard.querySelector(".media-inline-player-box");
   const iframe = playerBox.querySelector("iframe");
   inlineBtn.addEventListener("click", () => {
     if(playerBox.style.display === "none"){
       iframe.src = mc.embed_url;
       playerBox.style.display = "block";
       inlineBtn.innerHTML = "<span>⏸️ Player Chhupayein</span>";
     } else {
       iframe.src = "";
       playerBox.style.display = "none";
       inlineBtn.innerHTML = "<span>📺 Yahan Play Karein</span>";
     }
   });
   const bgBtn = mediaCard.querySelector(".media-bg-toggle-btn");
   bgBtn.addEventListener("click", () => {
     playBackgroundMedia(mc.query || mc.title, mc.embed_url, mc.web_url);
   });
   bubble.append(mediaCard);
 } else if (options.client_action && options.client_action.type === "open_app") {
   const ca = options.client_action;
   const appCard = document.createElement("div");
   appCard.className = "chat-app-action-card";
   const targetUrl = ca.mobile_url || ca.web_url;
   appCard.innerHTML = `
     <div class="media-card-title-row">
       <span class="media-card-badge">📱</span>
       <div>
         <div class="media-card-title">${ca.title || ca.name || "App"}</div>
         <div class="media-card-sub">Phone aur Computer par open karne ke liye</div>
       </div>
     </div>
     <div class="media-card-btn-group">
       <a href="${targetUrl}" target="_blank" rel="noopener noreferrer" class="app-action-link-btn">
         <span>🚀 ${ca.name || "App"} Kholein</span>
       </a>
     </div>
   `;
   bubble.append(appCard);
 }

 content.append(sender,bubble);
 article.append(avatar,content);
 messages.append(article);
 messages.scrollTop=messages.scrollHeight;
}

// =============================================================
// BACKGROUND MEDIA & PHONE APP CLIENT EXECUTOR
// =============================================================
const bgPlayer = document.querySelector("#smart-bg-media-player");
const bgPlayerTitle = document.querySelector("#bg-player-title");
const bgPlayerStatus = document.querySelector("#bg-player-status");
const bgPlayerIframe = document.querySelector("#bg-player-iframe");
const bgPlayerDisc = document.querySelector("#bg-player-disc");
const bgPlayerToggleBtn = document.querySelector("#bg-player-toggle-btn");
const bgPlayerMinBtn = document.querySelector("#bg-player-min-btn");
const bgPlayerCloseBtn = document.querySelector("#bg-player-close-btn");
const bgPlayerFrameBox = document.querySelector("#bg-player-frame-box");
const bgPlayerOpenLink = document.querySelector("#bg-player-open-link");

let isBgMediaPlaying = false;
let isBgMediaMinimized = false;

function playBackgroundMedia(title, embedUrl, webUrl) {
  if (!bgPlayer) return;
  bgPlayer.hidden = false;
  if (bgPlayerTitle) bgPlayerTitle.textContent = title || "YouTube Music";
  if (bgPlayerStatus) bgPlayerStatus.textContent = "Background me play ho raha hai...";
  if (bgPlayerOpenLink && webUrl) bgPlayerOpenLink.href = webUrl;

  if (bgPlayerIframe && embedUrl) {
    const safeUrl = embedUrl.includes("autoplay=1") ? embedUrl : `${embedUrl}&autoplay=1`;
    bgPlayerIframe.src = safeUrl;
  }
  isBgMediaPlaying = true;
  if (bgPlayerDisc) bgPlayerDisc.classList.remove("paused");
  if (bgPlayerToggleBtn) bgPlayerToggleBtn.textContent = "⏸";
}

if (bgPlayerToggleBtn) {
  bgPlayerToggleBtn.addEventListener("click", () => {
    isBgMediaPlaying = !isBgMediaPlaying;
    if (bgPlayerDisc) bgPlayerDisc.classList.toggle("paused", !isBgMediaPlaying);
    bgPlayerToggleBtn.textContent = isBgMediaPlaying ? "⏸" : "▶️";
    if (bgPlayerStatus) bgPlayerStatus.textContent = isBgMediaPlaying ? "Playing..." : "Paused";
    if (bgPlayerIframe) {
      try {
        if (!isBgMediaPlaying) {
          bgPlayerIframe.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
        } else {
          bgPlayerIframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
        }
      } catch (e) {}
    }
  });
}

if (bgPlayerMinBtn && bgPlayerFrameBox) {
  bgPlayerMinBtn.addEventListener("click", () => {
    isBgMediaMinimized = !isBgMediaMinimized;
    bgPlayerFrameBox.classList.toggle("minimized", isBgMediaMinimized);
    bgPlayerMinBtn.textContent = isBgMediaMinimized ? "□" : "_";
  });
}

if (bgPlayerCloseBtn) {
  bgPlayerCloseBtn.addEventListener("click", () => {
    if (bgPlayer) bgPlayer.hidden = true;
    if (bgPlayerIframe) bgPlayerIframe.src = "";
    isBgMediaPlaying = false;
  });
}

function handleClientAction(actionData) {
  if (!actionData) return;
  const isMobile = /android|iphone|ipad|ipod/i.test(navigator.userAgent);

  if (actionData.type === "youtube" || actionData.type === "play_media") {
    // 1. Play in background player
    playBackgroundMedia(actionData.title || actionData.query, actionData.embed_url, actionData.web_url);

    // 2. Open on phone / browser
    const targetUrl = (isMobile && actionData.intent_url) ? actionData.intent_url : actionData.web_url;
    if (targetUrl) {
      try {
        const win = window.open(targetUrl, "_blank");
        if (!win && isMobile) {
          window.location.href = targetUrl;
        }
      } catch (e) {
        console.warn("Could not auto open URL:", e);
      }
    }
  } else if (actionData.type === "open_app" || actionData.type === "open_url") {
    const url = (isMobile && actionData.mobile_url) ? actionData.mobile_url : actionData.web_url;
    if (url) {
      try {
        const win = window.open(url, "_blank");
        if (!win && isMobile) {
          window.location.href = url;
        }
      } catch (e) {
        window.location.href = url;
      }
    }
  } else if (actionData.type === "whatsapp_send" || actionData.app === "whatsapp") {
    const target = actionData.wa_me_url || actionData.mobile_url || "https://api.whatsapp.com/send";
    if (target) {
      if (isMobile) {
        window.location.href = target;
      } else {
        const win = window.open(target, "_blank");
        if (!win) window.location.href = target;
      }
    }
  } else if (actionData.type === "sms_send") {
    window.location.href = actionData.sms_url || "sms:";
  } else if (actionData.type === "phone_call") {
    window.location.href = actionData.tel_url || "tel:";
  } else if (actionData.type === "open_camera") {
    const camInput = document.createElement("input");
    camInput.type = "file";
    camInput.accept = "image/*";
    camInput.capture = "environment";
    camInput.style.display = "none";
    document.body.appendChild(camInput);
    camInput.click();
    camInput.remove();
  } else if (actionData.type === "open_calculator") {
    const calcCmd = document.querySelector("#cmd-calc");
    if (calcCmd) calcCmd.click();
  }
}

async function sendMessage(raw){
 const message=raw.trim();
 if(!message && pendingAttachments.length===0) return;
 stopAllAudio();
 input.value=""; input.style.height="auto";
 const attToSend = pendingAttachments.slice();
 pendingAttachments = [];
 renderAttachmentTray();
 addMessage("user", message || (attToSend.length ? "Attached files" : ""), [], { attachments: attToSend });
 const history=transcript.slice(-16);
 if(message) transcript.push({role:"user",content:message});
 sendButton.disabled=true;
 typing.hidden=false;
 setStatus("Jawab taiyar ho raha hai…");

 try{
  let response,data;
  if(message.toLowerCase().startsWith("/calc ")){
   response=await fetch("/api/calculate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({expression:message.slice(6)})});
   data=await response.json();
   if(!response.ok)throw Error(data.error||"Hisaab nahi hua.");
   data.reply="Python hisaab: "+data.result;
  }else{
   const agentHelpEl = document.querySelector("#agent-help-select");
   const agentHelpVal = agentHelpEl ? agentHelpEl.value : "auto";
   response=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message,history,use_search:searchToggle.checked,agent_help:agentHelpVal,attachments:attToSend})});
   data=await response.json();
   if(!response.ok)throw Error(data.error||"Request poori nahi hui.");
  }
  transcript.push({role:"assistant",content:data.reply});
  addMessage("assistant",data.reply,data.sources||[],{
    permission_blocked: data.permission_blocked,
    userQuery: message,
    collaborating_agent: data.collaborating_agent,
    next_step: data.next_step,
    client_action: data.client_action,
    media_card: data.media_card,
    whatsapp_card: data.whatsapp_card
  });
  speak(data.reply);

  if(data.client_action){
    handleClientAction(data.client_action);
  }

  if(data.show_permissions_modal&&permsModal){
   permsModal.showModal();
  }
  if(data.show_version_modal&&typeof openVersionModal==="function"){
   openVersionModal();
  }
  if(data.show_learning_modal&&typeof openLearningModal==="function"){
   openLearningModal();
  }
  if(data.show_agents_modal&&typeof openAgentsModal==="function"){
   openAgentsModal();
  }
  if(data.new_version){
   const bVer = document.querySelector("#brand-version-badge");
   if(bVer) bVer.textContent = data.new_version;
   const sVer = document.querySelector("#sidebar-version");
   if(sVer) sVer.textContent = `${data.new_version} · Active`;
   const mVer = document.querySelector("#modal-cur-version");
   if(mVer) mVer.textContent = data.new_version;
   if(typeof loadVersionHistory === "function") loadVersionHistory();
  }
  if(data.client_action==="open_camera"){
   // camera action handled
  }

  setStatus(serverOnlineLabel);
 }catch(error){
  console.warn("sendMessage error:", error);
  const friendlyMsg = "Maaf kijiye, abhi connect hone mein thodi dikkat aayi. Kripya dobara koshish karein.";
  addMessage("assistant", friendlyMsg);
  try { speak(friendlyMsg); } catch(e){}
  setStatus("24/7 Cloud Server Online 🌐", true);
 }finally{
  typing.hidden=true;
  sendButton.disabled=false;
  input.focus();
 }
}

// =============================================================
// ATTACHMENT TRAY & UPLOAD ENGINE
// =============================================================
let pendingAttachments = [];
const attachBtn = document.querySelector("#attach-btn");
const attachMenu = document.querySelector("#attach-menu");
const attachCloseBtn = document.querySelector("#attach-close-btn");
const attachmentTray = document.querySelector("#attachment-tray");

function renderAttachmentTray() {
  if (!attachmentTray) return;
  if (!pendingAttachments.length) {
    attachmentTray.innerHTML = "";
    attachmentTray.hidden = true;
    return;
  }
  attachmentTray.hidden = false;
  attachmentTray.innerHTML = "";
  pendingAttachments.forEach((att, idx) => {
    const chip = document.createElement("div");
    chip.className = "attach-chip";
    const isImg = att.type && att.type.startsWith("image/");
    const sizeKb = ((att.size || 0) / 1024).toFixed(1) + " KB";
    chip.innerHTML = `
      ${isImg ? `<img class="attach-chip-thumb" src="${att.dataUrl}" alt="${att.name}">` : `<span class="attach-chip-icon">📄</span>`}
      <div class="attach-chip-info">
        <span class="attach-chip-name" title="${att.name}">${att.name}</span>
        <span class="attach-chip-size">${sizeKb}</span>
      </div>
      <button type="button" class="attach-chip-remove" data-idx="${idx}" title="Hataayein">✕</button>
    `;
    chip.querySelector(".attach-chip-remove").addEventListener("click", () => {
      pendingAttachments.splice(idx, 1);
      renderAttachmentTray();
    });
    attachmentTray.appendChild(chip);
  });
}

if (attachBtn && attachMenu) {
  attachBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = attachMenu.hasAttribute("hidden");
    if (isHidden) {
      attachMenu.removeAttribute("hidden");
      attachBtn.classList.add("open");
    } else {
      attachMenu.setAttribute("hidden", "");
      attachBtn.classList.remove("open");
    }
  });

  if (attachCloseBtn) {
    attachCloseBtn.addEventListener("click", () => {
      attachMenu.setAttribute("hidden", "");
      attachBtn.classList.remove("open");
    });
  }

  document.addEventListener("click", (e) => {
    if (!attachMenu.contains(e.target) && !attachBtn.contains(e.target)) {
      attachMenu.setAttribute("hidden", "");
      attachBtn.classList.remove("open");
    }
  });

  document.querySelectorAll(".attach-item").forEach(item => {
    item.addEventListener("click", () => {
      const type = item.dataset.type;
      const fileInput = document.querySelector(`#input-${type}`);
      if (fileInput) {
        fileInput.value = "";
        fileInput.click();
      }
      attachMenu.setAttribute("hidden", "");
      attachBtn.classList.remove("open");
    });
  });

  const allFileInputs = document.querySelectorAll(".hidden-file-inputs input[type='file']");
  allFileInputs.forEach(inp => {
    inp.addEventListener("change", () => {
      const files = Array.from(inp.files || []);
      if (!files.length) return;
      files.forEach(file => {
        const reader = new FileReader();
        reader.onload = () => {
          pendingAttachments.push({
            name: file.name,
            type: file.type || "application/octet-stream",
            size: file.size,
            dataUrl: reader.result
          });
          renderAttachmentTray();
        };
        reader.readAsDataURL(file);
      });
    });
  });
}

form.addEventListener("submit",event=>{event.preventDefault();sendMessage(input.value);});
input.addEventListener("input",()=>{input.style.height="auto";input.style.height=Math.min(input.scrollHeight,140)+"px";});
input.addEventListener("keydown",event=>{if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();sendMessage(input.value);}});
document.querySelectorAll(".quick-command").forEach(button=>button.addEventListener("click",()=>sendMessage(button.dataset.prompt||"")));
document.querySelector("#clear-chat").addEventListener("click",()=>{
 stopAllAudio();
 transcript.length=0;
 messages.querySelectorAll(".message:not(.welcome-message)").forEach(node=>node.remove());
});

document.querySelector("#settings-open").addEventListener("click",()=>modal.showModal());
document.querySelector("#settings-cancel").addEventListener("click",()=>modal.close());
document.querySelector("#reveal-key").addEventListener("click",event=>{
 const field=document.querySelector("#api-key"),show=field.type==="password";
 field.type=show?"text":"password";
 event.currentTarget.textContent=show?"Chhupaayein":"Dikhaayein";
});

document.querySelector("#settings-form").addEventListener("submit",async event=>{
 event.preventDefault();
 const field=document.querySelector("#api-key"),feedback=document.querySelector("#settings-feedback");
 if(!field.value.trim()){feedback.textContent="Pehle API key daalein.";return;}
 feedback.textContent="Local settings mein save ho raha hai…";
 try{
  const response=await fetch("/api/settings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({api_key:field.value.trim()})});
  const data=await response.json();
  if(!response.ok)throw Error(data.error||"Save nahi hua.");
  field.value="";
  feedback.textContent="Key local settings mein save ho gayi.";
  await refreshStatus();
 }catch(error){
  feedback.textContent=error.message||"Key save nahi hui.";
 }
});

// Gmail Form Handler
const gmailForm=document.querySelector("#gmail-form");
if(gmailForm){
 const gmailEmail=document.querySelector("#gmail-email");
 const gmailPwd=document.querySelector("#gmail-pwd");
 const gmailFeedback=document.querySelector("#gmail-feedback");
 const revealGmailPwd=document.querySelector("#reveal-gmail-pwd");
 if(revealGmailPwd){
  revealGmailPwd.addEventListener("click",()=>{
   const show=gmailPwd.type==="password";
   gmailPwd.type=show?"text":"password";
   revealGmailPwd.textContent=show?"Chhupaayein":"Dikhaayein";
  });
 }
 gmailForm.addEventListener("submit",async event=>{
  event.preventDefault();
  if(!gmailPwd.value.trim()){
   gmailFeedback.textContent="Kripya 16-akshar ka App Password daalein.";
   return;
  }
  gmailFeedback.textContent="Gmail account verify ho raha hai…";
  try{
   const response=await fetch("/api/gmail/settings",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({email:gmailEmail.value.trim(),app_password:gmailPwd.value.trim()})
   });
   const data=await response.json();
   if(!response.ok)throw Error(data.error||"Gmail connect nahi hua.");
   if(data.gmail&&data.gmail.connected){
    gmailFeedback.textContent="✅ Gmail ("+data.gmail.user+") safalta se connect ho gaya!";
    gmailPwd.value="";
   }else{
    gmailFeedback.textContent="⚠️ "+(data.gmail?data.gmail.message:"Login nahi hua.");
   }
   await refreshStatus();
  }catch(error){
   gmailFeedback.textContent=error.message||"Gmail save nahi ho saka.";
  }
 });
}

// OpenAI Form Handler
const openaiForm=document.querySelector("#openai-form");
if(openaiForm){
 const openaiField=document.querySelector("#openai-api-key");
 const openaiFeedback=document.querySelector("#openai-feedback");
 const revealOpenaiKey=document.querySelector("#reveal-openai-key");
 if(revealOpenaiKey&&openaiField){
  revealOpenaiKey.addEventListener("click",()=>{
   const show=openaiField.type==="password";
   openaiField.type=show?"text":"password";
   revealOpenaiKey.textContent=show?"Chhupaayein":"Dikhaayein";
  });
 }
 openaiForm.addEventListener("submit",async event=>{
  event.preventDefault();
  if(!openaiField.value.trim()){
   openaiFeedback.textContent="Pehle OpenAI API key daalein.";
   return;
  }
  openaiFeedback.textContent="OpenAI key save ho rahi hai…";
  try{
   const response=await fetch("/api/openai/settings",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({api_key:openaiField.value.trim()})
   });
   const data=await response.json();
   if(!response.ok)throw Error(data.error||"Save nahi hua.");
   openaiField.value="";
   openaiFeedback.textContent="✅ OpenAI key safalta se save ho gayi!";
   await refreshStatus();
  }catch(error){
   openaiFeedback.textContent=error.message||"Key save nahi hui.";
  }
 });
}

// Google Tools Modal & Handlers
const toolsModal=document.querySelector("#tools-modal");
const toolsOpen=document.querySelector("#tools-open");
const toolsClose=document.querySelector("#tools-close");
const toolsRow=document.querySelector("#tools-row");
const toolsGrid=document.querySelector("#tools-grid");

if(toolsOpen&&toolsModal) toolsOpen.addEventListener("click",()=>toolsModal.showModal());
if(toolsRow&&toolsModal) toolsRow.addEventListener("click",()=>toolsModal.showModal());
if(toolsClose&&toolsModal) toolsClose.addEventListener("click",()=>toolsModal.close());

function renderTools(toolsData){
 if(!toolsGrid||!toolsData||!toolsData.tools) return;
 const emailEl=document.querySelector("#tools-account-email");
 if(emailEl&&toolsData.account) emailEl.textContent=toolsData.account;
 toolsGrid.innerHTML="";
 toolsData.tools.forEach(tool=>{
  const card=document.createElement("a");
  card.className="tool-card";
  card.href=tool.url;
  card.target="_blank";
  card.rel="noopener noreferrer";
  card.innerHTML=`
   <span class="tool-card-icon">${tool.icon}</span>
   <div class="tool-card-info">
    <strong>${tool.name}</strong>
    <small>${tool.desc}</small>
   </div>
   <span class="tool-card-badge">Kholiye ↗</span>
  `;
  toolsGrid.append(card);
 });
}

// Device Permissions Handlers
const permsModal=document.querySelector("#permissions-modal");
const permsOpen=document.querySelector("#perms-open");
const permsClose=document.querySelector("#perms-close");
const permsRow=document.querySelector("#perms-row");
const permsList=document.querySelector("#perms-list");
const permsAllowAll=document.querySelector("#perms-allow-all");
const permsBlockAll=document.querySelector("#perms-block-all");
const permsBannerCount=document.querySelector("#perms-banner-count");
const permsFeedback=document.querySelector("#perms-feedback");

if(permsOpen&&permsModal) permsOpen.addEventListener("click",()=>permsModal.showModal());
if(permsRow&&permsModal) permsRow.addEventListener("click",()=>permsModal.showModal());
if(permsClose&&permsModal) permsClose.addEventListener("click",()=>permsModal.close());

async function updatePermissionToggle(permId, allowed){
 try{
  const res=await fetch("/api/permissions",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({updates:{[permId]:allowed}})
  });
  const d=await res.json();
  if(d.permissions) renderPermissions(d.permissions);
  refreshStatus();
 }catch{}
}

async function setAllPermissions(allowAll){
 if(!permsFeedback) return;
 permsFeedback.textContent="Permissions update ho rahi hain…";
 try{
  const res=await fetch("/api/permissions",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({allow_all:allowAll})
  });
  const d=await res.json();
  if(d.permissions){
   renderPermissions(d.permissions);
   permsFeedback.textContent=allowAll?"✅ Sabhi 10 Permissions Allow kar di gayi hain.":"⛔ Sabhi 10 Permissions Block kar di gayi hain.";
  }
  refreshStatus();
 }catch{
  permsFeedback.textContent="Permissions update nahi ho saki.";
 }
}

if(permsAllowAll) permsAllowAll.addEventListener("click",()=>setAllPermissions(true));
if(permsBlockAll) permsBlockAll.addEventListener("click",()=>setAllPermissions(false));

function renderPermissions(permsData){
 if(!permsList||!permsData||!permsData.permissions) return;
 if(permsBannerCount){
  permsBannerCount.textContent=`${permsData.allowed_count}/${permsData.total} Allowed`;
 }
 const permsStatus=document.querySelector("#perms-status");
 if(permsStatus){
  permsStatus.textContent=`${permsData.allowed_count}/${permsData.total} Allowed`;
 }
 const permsMark=document.querySelector("#perms-mark");
 if(permsMark){
  const isAny=permsData.allowed_count>0;
  permsMark.textContent=isAny?"●":"!";
  permsMark.classList.toggle("good",isAny);
  permsMark.classList.toggle("bad",!isAny);
 }

 permsList.innerHTML="";
 permsData.permissions.forEach(p=>{
  const row=document.createElement("div");
  row.className="perm-row";
  row.innerHTML=`
   <div class="perm-main">
    <span class="perm-icon">${p.icon}</span>
    <div class="perm-info">
     <strong>${p.name}</strong>
     <small>${p.desc}</small>
    </div>
   </div>
   <div class="perm-control">
    <span class="perm-status-badge ${p.allowed?'allowed':'blocked'}">${p.allowed?'ALLOWED':'BLOCKED'}</span>
    <label class="toggle-option" style="margin:0">
     <input type="checkbox" ${p.allowed?'checked':''} data-id="${p.id}">
     <i class="toggle"></i>
    </label>
   </div>
  `;
  const chk=row.querySelector("input");
  chk.addEventListener("change",()=>updatePermissionToggle(p.id, chk.checked));
  permsList.append(row);
 });
}

// Bind initial speak buttons (e.g. welcome message)
document.querySelectorAll(".speak-msg-btn").forEach(btn=>{
 btn.addEventListener("click",()=>{
  const txt=btn.dataset.text||btn.parentElement.textContent;
  speak(txt);
 });
});

// Version Manager Modal & Controls
const versionModal = document.querySelector("#version-modal");
const versionOpen = document.querySelector("#version-open");
const versionRow = document.querySelector("#version-row");
const versionCloseX = document.querySelector("#version-close-x");
const versionCancelBtn = document.querySelector("#version-cancel-btn");
const versionForm = document.querySelector("#version-form");
const versionFeedback = document.querySelector("#version-feedback");
const versionHistoryList = document.querySelector("#version-history-list");
const versionSubmitBtn = document.querySelector("#version-submit-btn");

async function loadVersionHistory() {
  if (!versionHistoryList) return;
  try {
    const res = await fetch("/api/version");
    if (!res.ok) throw new Error();
    const data = await res.json();
    if (data.current_version) {
      const mVer = document.querySelector("#modal-cur-version");
      if (mVer) mVer.textContent = data.current_version;
    }
    const list = data.created_versions || [];
    if (!list.length) {
      versionHistoryList.innerHTML = '<div style="font-size:11px;color:#8b9bb1;padding:6px 0">Abhi tak koi extra version nahi banaya gaya. Current version hi base hai.</div>';
      return;
    }
    versionHistoryList.innerHTML = list.map(item => `
      <div class="version-list-item">
        <div class="version-list-header">
          <span style="color:#38bdf8">🏷️ ${item.version}</span>
          <small style="color:#64748b;font-size:10px">${item.created_at || ""}</small>
        </div>
        <div class="version-list-path">📁 ${item.folder}</div>
        ${item.note ? `<div style="font-size:10px;color:#94a3b8;margin-top:2px">Note: ${item.note}</div>` : ""}
      </div>
    `).join("");
  } catch (err) {
    versionHistoryList.innerHTML = '<div style="font-size:11px;color:#f87171">Version history load nahi ho saki.</div>';
  }
}

function openVersionModal() {
  if (versionModal) {
    versionModal.showModal();
    loadVersionHistory();
  }
}

function closeVersionModal() {
  if (versionModal) {
    versionModal.close();
  }
}

if (versionOpen) versionOpen.addEventListener("click", openVersionModal);
if (versionRow) versionRow.addEventListener("click", openVersionModal);
if (versionCloseX) versionCloseX.addEventListener("click", closeVersionModal);
if (versionCancelBtn) versionCancelBtn.addEventListener("click", closeVersionModal);

if (versionForm) {
  versionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const vInput = document.querySelector("#new-version-input");
    const tSelect = document.querySelector("#version-target-select");
    const nInput = document.querySelector("#version-note-input");
    const oCheck = document.querySelector("#version-overwrite-check");

    const newVer = (vInput ? vInput.value : "").trim();
    if (!newVer) {
      alert("Kripya naya version number likhein!");
      return;
    }

    if (versionFeedback) {
      versionFeedback.textContent = "⏳ Naya version folder ban raha hai aur sabhi files copy ho rahi hain...";
      versionFeedback.className = "settings-feedback";
      versionFeedback.style.color = "#38bdf8";
    }
    if (versionSubmitBtn) versionSubmitBtn.disabled = true;

    try {
      const bodyPayload = {
        version: newVer,
        note: nInput ? nInput.value.trim() : "",
        overwrite: oCheck ? oCheck.checked : false
      };
      if (tSelect && tSelect.value === "subfolder") {
        bodyPayload.target = `versions/SmartAI_${newVer}`;
      }

      const res = await fetch("/api/version/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bodyPayload)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        if (versionFeedback) {
          versionFeedback.innerHTML = `✅ <b>Mubarak ho!</b> Naya version <b>${data.version}</b> ban gaya!<br><small style="color:#cbd5e1;display:block;margin-top:4px">📁 Naya Folder: <b>${data.folder}</b><br>📄 Copied: ${data.items_copied} items<br>Purani files bilkul safe hain.</small>`;
          versionFeedback.className = "settings-feedback success";
          versionFeedback.style.color = "#34d399";
        }
        await loadVersionHistory();
        await refreshStatus();
      } else {
        if (versionFeedback) {
          versionFeedback.textContent = "❌ " + (data.error || "Naya version create nahi ho saka.");
          versionFeedback.className = "settings-feedback error";
          versionFeedback.style.color = "#f87171";
        }
      }
    } catch (err) {
      if (versionFeedback) {
        versionFeedback.textContent = "❌ Server error: " + err.message;
        versionFeedback.className = "settings-feedback error";
        versionFeedback.style.color = "#f87171";
      }
    } finally {
      if (versionSubmitBtn) versionSubmitBtn.disabled = false;
    }
  });
}

// =============================================================
// CONTINUOUS HANDS-FREE LIVE VOICE CONVERSATION SYSTEM
// STRICT TURN-TAKING: User speaks -> AI thinks -> AI speaks (mic OFF) -> Cooldown -> User speaks
// =============================================================
const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

const liveVoiceWidget = document.querySelector("#live-voice-widget");
const voiceOrb = document.querySelector("#voice-orb");
const voiceViewport = document.querySelector("#voice-viewport");
const voicePulseDot = document.querySelector("#voice-pulse-dot");
const voiceHeaderTitle = document.querySelector("#voice-header-title");
const voiceHudTag = document.querySelector("#voice-hud-tag");
const voiceStateText = document.querySelector("#voice-state-text");
const voiceStateSub = document.querySelector("#voice-state-sub");
const voiceMainBtn = document.querySelector("#voice-main-btn");
const voiceBtnText = document.querySelector("#voice-btn-text");
const voiceStopBtn = document.querySelector("#voice-stop-btn");
const voiceLiveTranscript = document.querySelector("#voice-live-transcript");
const transcriptLiveText = document.querySelector("#transcript-live-text");
const liveVoiceOpen = document.querySelector("#live-voice-open");
const voiceRow = document.querySelector("#voice-row");
const voiceModeStatus = document.querySelector("#voice-mode-status");
const voiceModeMark = document.querySelector("#voice-mode-mark");

function setVoiceStateUI(state, customText = "") {
  const fullRobot = document.querySelector("#full-bg-robot");
  if (fullRobot) {
    fullRobot.classList.remove("listening", "thinking", "speaking");
    if (state === "listening" || state === "thinking" || state === "speaking") {
      fullRobot.classList.add(state);
    }
  }

  if (!voiceViewport) return;

  voiceViewport.classList.remove("listening", "thinking", "speaking");
  if (voiceOrb) voiceOrb.classList.remove("listening", "thinking", "speaking");
  if (voicePulseDot) voicePulseDot.classList.remove("listening", "thinking", "speaking");
  if (voiceHudTag) voiceHudTag.classList.remove("listening", "thinking", "speaking");

  if (state === "listening") {
    voiceViewport.classList.add("listening");
    if (voiceOrb) voiceOrb.classList.add("listening");
    if (voicePulseDot) voicePulseDot.classList.add("listening");
    if (voiceHudTag) {
      voiceHudTag.classList.add("listening");
      voiceHudTag.textContent = "LISTENING";
    }
    if (voiceStateText) voiceStateText.textContent = "🎙️ Sun raha hoon… Boliye!";
    if (voiceStateSub) voiceStateSub.textContent = "Aapke chup hote hi Smart AI turant jawab dega.";
    if (voiceBtnText) voiceBtnText.textContent = "⏹️ Voice Baat-Cheet Rokein";
    if (voiceMainBtn) voiceMainBtn.classList.add("active");
    if (voiceStopBtn) voiceStopBtn.hidden = false;
    if (voiceModeStatus) voiceModeStatus.textContent = "Active · Sun raha hoon";
    if (voiceModeMark) { voiceModeMark.textContent = "●"; voiceModeMark.className = "connection-mark good"; }
    if (micButton) micButton.classList.add("listening");
  } else if (state === "thinking") {
    voiceViewport.classList.add("thinking");
    if (voiceOrb) voiceOrb.classList.add("thinking");
    if (voicePulseDot) voicePulseDot.classList.add("thinking");
    if (voiceHudTag) {
      voiceHudTag.classList.add("thinking");
      voiceHudTag.textContent = "THINKING";
    }
    if (voiceStateText) voiceStateText.textContent = "⚡ AI Soch raha hai…";
    if (voiceStateSub) voiceStateSub.textContent = customText ? `"${customText}" ka jawab taiyar ho raha hai...` : "Jawab taiyar ho raha hai...";
    if (voiceModeStatus) voiceModeStatus.textContent = "Jawab taiyar ho raha hai...";
    if (micButton) micButton.classList.remove("listening");
  } else if (state === "speaking") {
    voiceViewport.classList.add("speaking");
    if (voiceOrb) voiceOrb.classList.add("speaking");
    if (voicePulseDot) voicePulseDot.classList.add("speaking");
    if (voiceHudTag) {
      voiceHudTag.classList.add("speaking");
      voiceHudTag.textContent = "SPEAKING";
    }
    if (voiceStateText) voiceStateText.textContent = "🔊 AI Jawab de raha hai…";
    if (voiceStateSub) voiceStateSub.textContent = "AI bol raha hai (Mic band hai). Poora hone par dobara aapko sunega.";
    if (voiceModeStatus) voiceModeStatus.textContent = "Bol raha hai...";
    if (micButton) micButton.classList.remove("listening");
  } else if (state === "cooldown") {
    if (voiceHudTag) voiceHudTag.textContent = "READY";
    if (voiceStateText) voiceStateText.textContent = "⏳ Taiyar ho raha hai…";
    if (voiceStateSub) voiceStateSub.textContent = "Mic taiyar ho raha hai...";
    if (voiceModeStatus) voiceModeStatus.textContent = "Taiyar ho raha hai...";
    if (micButton) micButton.classList.remove("listening");
  } else {
    if (voiceHudTag) voiceHudTag.textContent = "READY";
    if (voiceStateText) voiceStateText.textContent = "Tap karke Live Voice shuru karein";
    if (voiceStateSub) voiceStateSub.textContent = "Aap bolenge to AI sunega, chup hone par bolkar jawab dega.";
    if (voiceBtnText) voiceBtnText.textContent = "Live Voice Baat-Cheet Chalu Karein";
    if (voiceMainBtn) voiceMainBtn.classList.remove("active");
    if (voiceStopBtn) voiceStopBtn.hidden = true;
    if (voiceLiveTranscript) voiceLiveTranscript.hidden = true;
    if (voiceModeStatus) voiceModeStatus.textContent = "Hands-Free · Auto Reply";
    if (voiceModeMark) { voiceModeMark.textContent = "●"; voiceModeMark.className = "connection-mark good"; }
    if (micButton) micButton.classList.remove("listening");
  }
}

function safeStartRecognition() {
  if (!recognitionInstance || !isLiveVoiceActive || voiceTurnState !== "listening" || isAiSpeaking) {
    return;
  }
  try {
    recognitionInstance.start();
  } catch (err) {
    setTimeout(() => {
      if (isLiveVoiceActive && voiceTurnState === "listening" && !isAiSpeaking) {
        try {
          recognitionInstance.start();
        } catch {}
      }
    }, 150);
  }
}

function safeStopRecognition() {
  if (!recognitionInstance) return;
  try {
    recognitionInstance.abort();
  } catch {}
}

function initSpeechRecognition() {
  if (!SpeechAPI) {
    if (micButton) micButton.disabled = true;
    if (voiceStateText) voiceStateText.textContent = "Voice Assistant Chrome/Edge me chalega";
    return null;
  }

  function cleanSpeechStutter(text) {
    if (!text) return "";
    let str = text.trim();
    // Remove immediate duplicate words in Unicode / Hindi: "तुम तुम" -> "तुम"
    str = str.replace(/([^\s]+)\s+\1(?:\s+|$)/gu, "$1 ");
    // Remove immediate duplicate 2-word phrases: "तुम खुद तुम खुद" -> "तुम खुद"
    str = str.replace(/([^\s]+\s+[^\s]+)\s+\1(?:\s+|$)/gu, "$1 ");
    return str.trim();
  }

  const isMobileDevice = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  const rec = new SpeechAPI();
  rec.lang = "hi-IN";
  rec.continuous = !isMobileDevice; // On mobile, single utterance per turn prevents Android cumulative buffer stacking
  rec.interimResults = true;

  rec.onstart = () => {
    if (isLiveVoiceActive && voiceTurnState === "listening") {
      setVoiceStateUI("listening");
    }
  };

  rec.onresult = (event) => {
    // STRICT HALF-DUPLEX GATE:
    // If AI is speaking, or thinking, or cooling down, or live voice is paused:
    // COMPLETELY IGNORE all speech events so mic NEVER picks up AI's own audio!
    if (!isLiveVoiceActive || voiceTurnState !== "listening" || isAiSpeaking) {
      return;
    }

    let finalTranscript = "";
    let interimTranscript = "";

    // Properly parse event.results without Android cumulative duplication
    for (let i = 0; i < event.results.length; ++i) {
      const chunk = event.results[i][0].transcript.trim();
      if (!chunk) continue;

      if (event.results[i].isFinal) {
        // If chunk is a cumulative continuation of what we already have (Android Chrome quirk),
        // REPLACE it instead of appending!
        if (finalTranscript && chunk.startsWith(finalTranscript.trim())) {
          finalTranscript = chunk;
        } else if (finalTranscript && finalTranscript.trim().startsWith(chunk)) {
          // chunk is an earlier sub-part, already subsumed
        } else {
          // On desktop where results are separate non-overlapping segments:
          finalTranscript = (finalTranscript + " " + chunk).trim();
        }
      } else {
        interimTranscript = chunk;
      }
    }

    let liveDisplay = "";
    if (interimTranscript) {
      if (finalTranscript && interimTranscript.startsWith(finalTranscript.trim())) {
        liveDisplay = interimTranscript;
      } else {
        liveDisplay = (finalTranscript + " " + interimTranscript).trim();
      }
    } else {
      liveDisplay = finalTranscript.trim();
    }

    liveDisplay = cleanSpeechStutter(liveDisplay);

    if (liveDisplay) {
      currentVoiceTranscript = liveDisplay;
      if (voiceLiveTranscript) voiceLiveTranscript.hidden = false;
      if (transcriptLiveText) transcriptLiveText.textContent = `"${liveDisplay}"`;
      if (input) input.value = liveDisplay;

      clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {
        handleUserSilenceTrigger(liveDisplay);
      }, SILENCE_TIMEOUT);
    }
  };

  rec.onerror = (event) => {
    console.warn("Speech error:", event.error);
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      isLiveVoiceActive = false;
      voiceTurnState = "idle";
      setVoiceStateUI("paused");
      alert("Microphone permission allow karein taaki AI aapko sun sake.");
    }
  };

  rec.onend = () => {
    // If recognition ended and user had spoken text that hasn't been submitted yet:
    if (isLiveVoiceActive && voiceTurnState === "listening" && !isAiSpeaking) {
      const pendingText = currentVoiceTranscript.trim();
      if (pendingText) {
        clearTimeout(silenceTimer);
        handleUserSilenceTrigger(pendingText);
        return;
      }
      setTimeout(() => {
        safeStartRecognition();
      }, 100);
    }
  };

  return rec;
}

recognitionInstance = initSpeechRecognition();

async function handleUserSilenceTrigger(userSaid) {
  clearTimeout(silenceTimer);
  const textToSend = userSaid.trim();
  if (!textToSend) return;

  // USER TURN FINISHED -> TRANSITION TO THINKING TURN
  voiceTurnState = "thinking";
  currentVoiceTranscript = "";
  if (voiceLiveTranscript) voiceLiveTranscript.hidden = true;
  if (input) input.value = "";

  // IMMEDIATELY ABORT MIC TO PREVENT CAPTURING ANY RESIDUAL AUDIO
  safeStopRecognition();

  setVoiceStateUI("thinking", textToSend);

  try {
    await sendVoiceMessage(textToSend);
  } catch (err) {
    console.error("sendVoiceMessage error:", err);
  }
}

async function sendVoiceMessage(message) {
  addMessage("user", message);
  const history = transcript.slice(-16);
  transcript.push({ role: "user", content: message });
  if (sendButton) sendButton.disabled = true;
  if (typing) typing.hidden = false;
  setStatus("Jawab taiyar ho raha hai…");

  try {
    let response, data;
    if (message.toLowerCase().startsWith("/calc ")) {
      response = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expression: message.slice(6) })
      });
      data = await response.json();
      if (!response.ok) throw Error(data.error || "Hisaab nahi hua.");
      data.reply = "Python hisaab: " + data.result;
    } else {
      const eng = document.querySelector("#engine-select") ? document.querySelector("#engine-select").value : "auto";
      response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history,
          use_search: searchToggle.checked,
          engine: eng
        })
      });
      data = await response.json();
      if (!response.ok) throw Error(data.error || "Request poori nahi hui.");
    }

    transcript.push({ role: "assistant", content: data.reply });
    addMessage("assistant", data.reply, data.sources || [], {
      permission_blocked: data.permission_blocked,
      userQuery: message,
      collaborating_agent: data.collaborating_agent,
      next_step: data.next_step,
      client_action: data.client_action,
      media_card: data.media_card,
      whatsapp_card: data.whatsapp_card
    });

    if (data.client_action) {
      handleClientAction(data.client_action);
    }

    setStatus(serverOnlineLabel);

    // SPEAKING TURN:
    // AI speaks its reply. The callback will transition to cooldown and then listening turn.
    speak(data.reply, () => {
      onAiFinishedSpeaking();
    });

  } catch (err) {
    console.warn("voice loop error:", err);
    const isNetworkErr = !err || err.message === "Failed to fetch" || (err.message && err.message.includes("fetch"));
    let errMsg = "Maaf kijiye, samajhne me thodi dikkat aayi. Kripya dobara boliye.";
    if (isNetworkErr) {
      errMsg = "Smart AI server se connect nahi ho saka. Kripya connection check karein.";
      setStatus("Server Offline", false);
    } else {
      setStatus(serverOnlineLabel);
    }

    addMessage("assistant", errMsg);

    if (isNetworkErr) {
      // Server down -> stop live loop to avoid infinite loop
      voiceTurnState = "idle";
      isLiveVoiceActive = false;
      isAiSpeaking = false;
      setVoiceStateUI("paused");
      return;
    }

    speak(errMsg, () => {
      onAiFinishedSpeaking();
    });
  } finally {
    if (typing) typing.hidden = true;
    if (sendButton) sendButton.disabled = false;
  }
}

function onAiFinishedSpeaking(immediate = false) {
  isAiSpeaking = false;
  currentAudio = null;
  if (stopSpeech) stopSpeech.hidden = true;

  if (!isLiveVoiceActive) {
    voiceTurnState = "idle";
    setVoiceStateUI("paused");
    return;
  }

  // AI has finished speaking.
  // Wait a short cooldown (500ms) to ensure speakers have stopped and room echo cleared!
  const delay = immediate ? 50 : 500;
  voiceTurnState = "cooldown";
  setVoiceStateUI("cooldown");

  setTimeout(() => {
    if (!isLiveVoiceActive) {
      voiceTurnState = "idle";
      setVoiceStateUI("paused");
      return;
    }

    // Now safely open the microphone for user's turn
    currentVoiceTranscript = "";
    if (voiceLiveTranscript) voiceLiveTranscript.hidden = true;
    voiceTurnState = "listening";
    setVoiceStateUI("listening");

    safeStartRecognition();
  }, delay);
}

function toggleLiveVoice() {
  if (!recognitionInstance) {
    recognitionInstance = initSpeechRecognition();
  }
  if (!recognitionInstance) {
    alert("Voice recognition is browser me support nahi hai. Chrome ya Edge use karein.");
    return;
  }

  if (isLiveVoiceActive) {
    // User is pausing/stopping live voice
    isLiveVoiceActive = false;
    voiceTurnState = "idle";
    clearTimeout(silenceTimer);
    safeStopRecognition();
    stopAllAudio();
    setVoiceStateUI("paused");
  } else {
    // User is turning ON live voice
    stopAllAudio();
    isLiveVoiceActive = true;
    if (speechToggle) speechToggle.checked = true;
    currentVoiceTranscript = "";
    if (voiceLiveTranscript) voiceLiveTranscript.hidden = true;

    // AI immediately speaks a greeting out loud!
    // This gives instant audio confirmation, moves the robot mouth, and unlocks browser autoplay
    voiceTurnState = "speaking";
    setVoiceStateUI("speaking");
    speak("Namaste! Main sun raha hoon. Boliye main aapki kya madad karoon?", () => {
      onAiFinishedSpeaking();
    });
  }
}

if (voiceMainBtn) voiceMainBtn.addEventListener("click", toggleLiveVoice);
if (voiceOrb) voiceOrb.addEventListener("click", toggleLiveVoice);
const fullRobotEl = document.querySelector("#full-bg-robot");
if (fullRobotEl) fullRobotEl.addEventListener("click", toggleLiveVoice);
if (voiceStopBtn) voiceStopBtn.addEventListener("click", toggleLiveVoice);
if (liveVoiceOpen) liveVoiceOpen.addEventListener("click", () => {
  if (liveVoiceWidget) liveVoiceWidget.scrollIntoView({ behavior: "smooth", block: "center" });
  if (!isLiveVoiceActive) toggleLiveVoice();
});
if (voiceRow) voiceRow.addEventListener("click", () => {
  if (liveVoiceWidget) liveVoiceWidget.scrollIntoView({ behavior: "smooth", block: "center" });
  if (!isLiveVoiceActive) toggleLiveVoice();
});

if (micButton) {
  micButton.addEventListener("click", () => {
    toggleLiveVoice();
  });
}

// Stop speech button handler
if (stopSpeech) {
  stopSpeech.addEventListener("click", () => {
    stopAllAudio();
    if (isLiveVoiceActive) {
      onAiFinishedSpeaking(true);
    }
  });
}

// Phone Modal Handlers & Dynamic Link Population
const phoneModal = document.querySelector("#phone-modal");
const phoneOpen = document.querySelector("#phone-open");
const phoneRow = document.querySelector("#phone-row");
const phoneClose = document.querySelector("#phone-close");
const phoneTunnelInput = document.querySelector("#phone-tunnel-url-field");
const phoneTunnelCopyBtn = document.querySelector("#phone-tunnel-copy-btn");
const phoneLocalInput = document.querySelector("#phone-url-field");
const phoneLocalCopyBtn = document.querySelector("#phone-copy-btn");
const phoneQrImg = document.querySelector("#phone-qr-img");
const fixFirewallBtn = document.querySelector("#fix-firewall-btn");
const firewallStatus = document.querySelector("#firewall-status");

async function loadPhoneInfo() {
  try {
    const res = await fetch("/api/phone/info");
    if (!res.ok) return;
    const data = await res.json();
    if (phoneLocalInput) phoneLocalInput.value = data.url || `http://${data.local_ip}:${data.port}`;
    if (phoneTunnelInput) {
      if (data.tunnel_url) {
        phoneTunnelInput.value = data.tunnel_url;
      } else {
        phoneTunnelInput.value = "Starting secure tunnel… please wait 5s";
        setTimeout(loadPhoneInfo, 4000);
      }
    }
    if (phoneQrImg) {
      phoneQrImg.src = "/api/phone/qr?t=" + Date.now();
    }
  } catch (e) {
    console.error("loadPhoneInfo error:", e);
  }
}

if (phoneOpen && phoneModal) {
  phoneOpen.addEventListener("click", () => {
    phoneModal.showModal();
    loadPhoneInfo();
  });
}
if (phoneRow && phoneModal) {
  phoneRow.addEventListener("click", () => {
    phoneModal.showModal();
    loadPhoneInfo();
  });
}
if (phoneClose && phoneModal) {
  phoneClose.addEventListener("click", () => phoneModal.close());
}

if (phoneTunnelCopyBtn && phoneTunnelInput) {
  phoneTunnelCopyBtn.addEventListener("click", () => {
    if (phoneTunnelInput.value && !phoneTunnelInput.value.includes("Starting")) {
      navigator.clipboard.writeText(phoneTunnelInput.value);
      phoneTunnelCopyBtn.textContent = "Copied! ✅";
      setTimeout(() => phoneTunnelCopyBtn.textContent = "Copy 📋", 2000);
    }
  });
}

if (phoneLocalCopyBtn && phoneLocalInput) {
  phoneLocalCopyBtn.addEventListener("click", () => {
    if (phoneLocalInput.value) {
      navigator.clipboard.writeText(phoneLocalInput.value);
      phoneLocalCopyBtn.textContent = "Copied! ✅";
      setTimeout(() => phoneLocalCopyBtn.textContent = "Copy 📋", 2000);
    }
  });
}

if (fixFirewallBtn) {
  fixFirewallBtn.addEventListener("click", async () => {
    try {
      fixFirewallBtn.disabled = true;
      fixFirewallBtn.textContent = "Popup bhej raha hai…";
      await fetch("/api/phone/fix-firewall");
      if (firewallStatus) firewallStatus.textContent = "Windows popup me 'Yes' dabayein!";
      fixFirewallBtn.textContent = "Popup sent! 'Yes' dabayein";
      setTimeout(() => {
        fixFirewallBtn.disabled = false;
        fixFirewallBtn.textContent = "🛡️ Windows Firewall Allow Karein (1-Click Fix)";
      }, 5000);
    } catch (e) {
      fixFirewallBtn.disabled = false;
      fixFirewallBtn.textContent = "Failed. Dobara dabayein";
    }
  });
}

loadPhoneInfo();

// Weather Modal Handlers
const weatherModal = document.querySelector("#weather-modal");
const weatherOpen = document.querySelector("#weather-open");
const weatherRow = document.querySelector("#weather-row");
const weatherClose = document.querySelector("#weather-close");
if (weatherOpen && weatherModal) weatherOpen.addEventListener("click", () => weatherModal.showModal());
if (weatherRow && weatherModal) weatherRow.addEventListener("click", () => weatherModal.showModal());
if (weatherClose && weatherModal) weatherClose.addEventListener("click", () => weatherModal.close());

// CMD / Terminal Modal Handlers
const cmdModal = document.querySelector("#cmd-modal");
const cmdRow = document.querySelector("#cmd-row");
const cmdClose = document.querySelector("#cmd-close");
if (cmdRow && cmdModal) cmdRow.addEventListener("click", () => cmdModal.showModal());
if (cmdClose && cmdModal) cmdClose.addEventListener("click", () => cmdModal.close());

// AI Self-Learning Modal Handlers
const learningModal = document.querySelector("#learning-modal");
const learningOpen = document.querySelector("#learning-open");
const learningRow = document.querySelector("#learning-row");
const learningCloseBtn = document.querySelector("#learning-close-btn");
const learningCloseX = document.querySelector("#learning-close-x");
const learningResetBtn = document.querySelector("#learning-reset-btn");

async function openLearningModal(){
  if (!learningModal) return;
  learningModal.showModal();
  await refreshLearningModal();
}

async function refreshLearningModal(){
  try {
    const res = await fetch("/api/feedback/stats");
    if (!res.ok) return;
    const stats = await res.json();

    const avgEl = document.querySelector("#learning-modal-avg");
    if (avgEl) avgEl.textContent = stats.average_rating || "5.0";

    const totalEl = document.querySelector("#learning-modal-total");
    if (totalEl) totalEl.textContent = stats.total_ratings || 0;

    const starsEl = document.querySelector("#learning-modal-stars");
    if (starsEl) {
      const avg = Math.round(Number(stats.average_rating) || 5);
      starsEl.textContent = "⭐".repeat(Math.max(1, Math.min(5, avg)));
    }

    const total = stats.total_ratings || 0;
    for (let s = 1; s <= 5; s++) {
      const cnt = (stats.star_counts && stats.star_counts[s]) || 0;
      const cntEl = document.querySelector(`#lb-cnt-${s}`);
      if (cntEl) cntEl.textContent = cnt;
      const fillEl = document.querySelector(`#lb-fill-${s}`);
      if (fillEl) fillEl.style.width = total > 0 ? `${Math.round((cnt / total) * 100)}%` : (s === 5 ? "100%" : "0%");
    }

    const rulesList = document.querySelector("#learned-rules-list");
    const rulesCount = document.querySelector("#learned-rules-count");
    const rules = stats.learned_rules || [];
    if (rulesCount) rulesCount.textContent = rules.length;

    if (rulesList) {
      if (rules.length === 0) {
        rulesList.innerHTML = `<div style="font-size:11px;color:#8b9bb1;padding:8px">Abhi tak koi naya rule add nahi hua hai. Har jawab ke niche bane ⭐ stars par click karke Smart AI ko sikhao!</div>`;
      } else {
        rulesList.innerHTML = rules.map(r => `
          <div class="learned-rule-card" data-rule-id="${r.id}">
            <div class="lrc-body">
              <span class="lrc-topic">${r.topic || "NIYAM"}</span>
              <div class="lrc-rule">${r.rule || ""}</div>
              <div class="lrc-meta">Sikha gaya: ${r.timestamp || "Haal hi me"} · User: ${r.user_name || "Aap"}</div>
            </div>
            <button class="lrc-del-btn" title="Yeh niyam hatayein" data-del-id="${r.id}">🗑️</button>
          </div>
        `).join("");

        rulesList.querySelectorAll(".lrc-del-btn").forEach(btn => {
          btn.addEventListener("click", async () => {
            const rid = btn.dataset.delId;
            if (!rid) return;
            await fetch("/api/feedback/rule/delete", {
              method: "POST",
              headers: {"Content-Type": "application/json"},
              body: JSON.stringify({id: rid})
            });
            await refreshLearningModal();
            await refreshStatus();
          });
        });
      }
    }
  } catch(err) {
    console.error("Learning stats error:", err);
  }
}

if (learningOpen) learningOpen.addEventListener("click", openLearningModal);
if (learningRow) learningRow.addEventListener("click", openLearningModal);
if (learningCloseBtn && learningModal) learningCloseBtn.addEventListener("click", () => learningModal.close());
if (learningCloseX && learningModal) learningCloseX.addEventListener("click", () => learningModal.close());
if (learningResetBtn) {
  learningResetBtn.addEventListener("click", async () => {
    if (confirm("Kya aap Smart AI ki sari self-learning memory reset karna chahte hain?")) {
      await fetch("/api/feedback/reset", {method: "POST"});
      await refreshLearningModal();
      await refreshStatus();
    }
  });
}

// PWA Install Handling & Play Store APK Helper
let deferredInstallPrompt = null;
const pwaInstallBtn = document.querySelector("#pwa-install-btn");
const copyApkCmdBtn = document.querySelector("#copy-apk-cmd-btn");

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  if (pwaInstallBtn) {
    pwaInstallBtn.hidden = false;
  }
});

if (pwaInstallBtn) {
  pwaInstallBtn.addEventListener("click", async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      if (outcome === "accepted") {
        pwaInstallBtn.hidden = true;
      }
      deferredInstallPrompt = null;
    } else {
      alert("Phone me install karne ke liye Chrome ke 3-dots (⋮) par tap karein aur 'Install app' ya 'Add to Home screen' chunein.");
    }
  });
}

if (copyApkCmdBtn) {
  copyApkCmdBtn.addEventListener("click", () => {
    navigator.clipboard.writeText("build_android_apk.bat");
    copyApkCmdBtn.textContent = "Copied! ✓";
    setTimeout(() => { copyApkCmdBtn.textContent = "build_android_apk.bat 📋"; }, 2000);
  });
}

// OpenSource AI Agents Modal Handlers
const agentsModal = document.querySelector("#agents-modal");
const agentsOpen = document.querySelector("#agents-open");
const agentsRow = document.querySelector("#agents-row");
const agentsCloseBtn = document.querySelector("#agents-close-btn");
const agentsCloseX = document.querySelector("#agents-close-x");
const agentsGrid = document.querySelector("#agents-grid");
const agentsSearchInput = document.querySelector("#agents-search-input");
const agentsCatFilters = document.querySelector("#agents-cat-filters");

let activeAgentCat = "all";
let cachedAgentsList = [];

async function openAgentsModal() {
  if (!agentsModal) return;
  agentsModal.showModal();
  await loadOpenSourceAgents();
}

async function loadOpenSourceAgents() {
  if (!agentsGrid) return;
  try {
    const q = agentsSearchInput ? encodeURIComponent(agentsSearchInput.value.trim()) : "";
    const cat = encodeURIComponent(activeAgentCat);
    const url = `/api/agents/opensource?category=${cat}&q=${q}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error();
    const data = await res.json();
    cachedAgentsList = data.agents || [];
    renderAgentsGrid(cachedAgentsList);
  } catch (err) {
    agentsGrid.innerHTML = `<div style="font-size:11px;color:#ef4444;padding:12px">Agents load karne me dikkat aayi. Network check karein.</div>`;
  }
}

function renderAgentsGrid(agents) {
  if (!agentsGrid) return;
  if (!agents.length) {
    agentsGrid.innerHTML = `<div style="font-size:11px;color:#8b9bb1;padding:16px;text-align:center;grid-column:1/-1">Koi open-source agent nahi mila. Koi doosra keyword ya category chunein.</div>`;
    return;
  }
  agentsGrid.innerHTML = agents.map(a => `
    <div class="agent-card" data-agent-id="${a.id}">
      <div>
        <div class="agent-card-top">
          <div class="agent-avatar">${a.icon || "🤖"}</div>
          <div class="agent-info">
            <div class="agent-name-row">
              <span class="agent-name">${a.name}</span>
              <span class="agent-stars">${a.stars || ""}</span>
            </div>
            <span class="agent-cat-badge">${a.category}</span>
          </div>
        </div>
        <p class="agent-desc">${a.desc}</p>
        <div class="agent-tags">
          ${(a.tags || []).map(t => `<span class="agent-tag">#${t}</span>`).join("")}
        </div>
      </div>
      <div class="agent-card-actions">
        <button type="button" class="agent-use-btn" data-agent-id="${a.id}" data-agent-name="${a.name}" title="Is agent ki help se kaam karwayein">
          Help Lein ▶
        </button>
        <a href="${a.github_url}" target="_blank" rel="noopener noreferrer" class="agent-gh-btn" title="Open GitHub Repo">
          GitHub ↗
        </a>
        <button type="button" class="agent-clone-btn" data-clone="${encodeURIComponent(a.clone_cmd)}" title="Copy install/clone command">
          Cmd 📋
        </button>
      </div>
    </div>
  `).join("");

  agentsGrid.querySelectorAll(".agent-use-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const aid = btn.dataset.agentId;
      const aname = btn.dataset.agentName;
      const agentHelpEl = document.querySelector("#agent-help-select");
      if (agentHelpEl) {
        if (agentHelpEl.querySelector(`option[value="${aid}"]`)) {
          agentHelpEl.value = aid;
        }
      }
      if (agentsModal) agentsModal.close();
      if (input) {
        input.value = `${aname} ki help se: `;
        input.focus();
        input.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  agentsGrid.querySelectorAll(".agent-clone-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const cmd = decodeURIComponent(btn.dataset.clone);
      navigator.clipboard.writeText(cmd);
      const prev = btn.textContent;
      btn.textContent = "Copied! ✓";
      btn.style.color = "#34d399";
      setTimeout(() => {
        btn.textContent = prev;
        btn.style.color = "";
      }, 1800);
    });
  });
}

if (agentsOpen) agentsOpen.addEventListener("click", openAgentsModal);
if (agentsRow) agentsRow.addEventListener("click", openAgentsModal);
if (agentsCloseBtn && agentsModal) agentsCloseBtn.addEventListener("click", () => agentsModal.close());
if (agentsCloseX && agentsModal) agentsCloseX.addEventListener("click", () => agentsModal.close());

if (agentsSearchInput) {
  let debounceTimer = null;
  agentsSearchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadOpenSourceAgents, 250);
  });
}

if (agentsCatFilters) {
  agentsCatFilters.querySelectorAll(".agents-cat-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      agentsCatFilters.querySelectorAll(".agents-cat-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeAgentCat = pill.dataset.cat || "all";
      loadOpenSourceAgents();
    });
  });
}

// OpenAI Row opens settings modal
const openaiRow = document.querySelector("#openai-row");
if (openaiRow && modal) openaiRow.addEventListener("click", () => modal.showModal());

// =============================================================
// GLOBAL MODAL CLOSE HANDLERS & BACKDROP CLICK (CSP Compliant)
// =============================================================
// 1. Any button with .modal-close-btn or inside .modal-close-row
document.querySelectorAll(".modal-close-btn, .modal-close-row button").forEach(btn => {
  btn.addEventListener("click", () => {
    const dlg = btn.closest("dialog");
    if (dlg) dlg.close();
  });
});

// 2. Specific modal footer close/cancel buttons
[
  "#settings-cancel",
  "#tools-close",
  "#perms-close",
  "#phone-close",
  "#weather-close",
  "#cmd-close",
  "#version-close-x",
  "#version-cancel-btn",
  "#learning-close-x",
  "#learning-close-btn",
  "#agents-close-x",
  "#agents-close-btn"
].forEach(sel => {
  const el = document.querySelector(sel);
  if (el) {
    el.addEventListener("click", () => {
      const dlg = el.closest("dialog");
      if (dlg) dlg.close();
    });
  }
});

// 3. Click outside dialog box (backdrop) closes the modal
document.querySelectorAll("dialog").forEach(dialog => {
  dialog.addEventListener("click", (e) => {
    const rect = dialog.getBoundingClientRect();
    const isInDialog = (
      rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
      rect.left <= e.clientX && e.clientX <= rect.left + rect.width
    );
    if (!isInDialog) {
      dialog.close();
    }
  });
});

refreshStatus();
