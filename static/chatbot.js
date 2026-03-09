(() => {
  const toggle = document.getElementById('chatbot-toggle');
  const win = document.getElementById('chatbot-window');
  const closeBtn = document.getElementById('chatbot-close');
  const form = document.getElementById('chatbot-form');
  const input = document.getElementById('chatbot-input');
  const messages = document.getElementById('chatbot-messages');

  function openWindow(){ 
    win.style.display='flex'; 
    win.setAttribute('aria-hidden','false'); 
    input.focus(); 
  }
  
  function closeWindow(){ 
    win.style.display='none'; 
    win.setAttribute('aria-hidden','true'); 
  }

  toggle && toggle.addEventListener('click', ()=>{
    if(win.style.display==='flex') closeWindow(); else openWindow();
  });
  
  closeBtn && closeBtn.addEventListener('click', closeWindow);

  // Helper function to format markdown-like text to HTML
  function formatMarkdown(text) {
    // Escape HTML first
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    // Convert code blocks ```code``` to <code>
    html = html.replace(/```([^`]+)```/g, '<code style="background: rgba(255,255,255,0.08); padding: 2px 5px; border-radius: 3px; font-family: monospace; font-size: 12px;">$1</code>');
    
    // Convert inline code `code` to <code>
    html = html.replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.08); padding: 2px 5px; border-radius: 3px; font-family: monospace; font-size: 12px;">$1</code>');
    
    // Convert **bold** to <strong>
    html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong style="color: #bfe9d7;">$1</strong>');
    
    // Convert bullet points • to proper formatting
    html = html.replace(/^• (.+)$/gm, '<div style="margin-left: 16px; margin-top: 4px;">• $1</div>');
    
    // Convert line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
  }

  function appendMessage(text, cls='bot'){
    const el = document.createElement('div'); 
    el.className = cls; 
    
    if (cls === 'bot') {
      // Format bot messages with markdown/HTML
      el.innerHTML = formatMarkdown(text);
    } else {
      // User messages are plain text
      el.textContent = text;
    }
    
    messages.appendChild(el); 
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage(message){
    appendMessage(message, 'user');
    appendMessage('⏳ Loading...', 'bot');
    
    try{
      const res = await fetch('/chatbot_api', { 
        method: 'POST', 
        headers: {'Content-Type':'application/json'}, 
        body: JSON.stringify({message}),
        timeout: 15000
      });
      
      const json = await res.json();
      
      // Remove the loading message
      const last = messages.querySelectorAll('.bot');
      if(last.length) last[last.length-1].remove();
      
      if(json && json.reply){ 
        appendMessage(json.reply, 'bot'); 
      } else {
        appendMessage('❌ Unable to process your question. Please ensure it\'s cybersecurity-related and try again.', 'bot');
      }
    } catch(err){
      const last = messages.querySelectorAll('.bot'); 
      if(last.length) last[last.length-1].remove();
      appendMessage('⚠️ Error contacting assistant. Please check your internet and try again.', 'bot');
      console.error('Chat error:', err);
    }
  }

  form && form.addEventListener('submit', (e)=>{
    e.preventDefault();
    const v = input.value && input.value.trim();
    if(!v) return;
    input.value='';
    sendMessage(v);
  });

})();
