// UVM Testbench Generator - Authentication Module

let sbClient = null;
let currentUser = null;
let authEnabled = false;

// ── Init ─────────────────────────────────────────────────────────────────────
async function initAuth() {
  try {
    const res = await fetch("/api/config");
    const cfg = await res.json();
    authEnabled = cfg.auth_enabled;

    if (!authEnabled) {
      console.log("[auth] Not configured - guest-only mode");
      return;
    }

    sbClient = window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key);

    const { data: { session } } = await sbClient.auth.getSession();
    if (session) {
      await setUser(session.user);
    }

    sbClient.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setUser(session.user);
      } else {
        clearUser();
      }
    });
  } catch (e) {
    console.error("[auth] init error:", e.message);
  }
}

// ── User state ───────────────────────────────────────────────────────────────
async function setUser(user) {
  currentUser = user;
  const name = user.user_metadata?.full_name || user.email?.split("@")[0] || "User";
  const initials = name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

  document.getElementById("guest-badge").style.display = "none";
  document.getElementById("user-menu").style.display = "flex";
  document.getElementById("user-initials").textContent = initials;
  document.getElementById("dropdown-name").textContent = name;
  document.getElementById("dropdown-email").textContent = user.email;
  document.getElementById("download-btn-text").textContent = "Download ZIP";

  if (sbClient) {
    try {
      const { data: profile } = await sbClient.from("profiles").select("role").eq("id", user.id).single();
      if (profile && profile.role === "admin") {
        const adminLink = document.getElementById("admin-link");
        if (adminLink) adminLink.style.display = "inline";
      }
    } catch (e) {}
  }
}

function clearUser() {
  currentUser = null;
  document.getElementById("guest-badge").style.display = "flex";
  document.getElementById("user-menu").style.display = "none";
  document.getElementById("user-dropdown").style.display = "none";
  document.getElementById("feedback-panel").style.display = "none";
  document.getElementById("download-btn-text").textContent = "Download ZIP";
  const adminLink = document.getElementById("admin-link");
  if (adminLink) adminLink.style.display = "none";
}

function isLoggedIn() {
  return currentUser !== null;
}

function getSbClient() {
  return sbClient;
}

// ── Auth Modal ───────────────────────────────────────────────────────────────
function showAuthModal(tab = "login") {
  document.getElementById("auth-modal").style.display = "flex";
  switchAuthTab(tab);
  clearAuthErrors();
}

function hideAuthModal() {
  document.getElementById("auth-modal").style.display = "none";
  clearAuthErrors();
}

function switchAuthTab(tab) {
  const isLogin = tab === "login";
  document.getElementById("tab-login").classList.toggle("active", isLogin);
  document.getElementById("tab-register").classList.toggle("active", !isLogin);
  document.getElementById("login-form").style.display = isLogin ? "block" : "none";
  document.getElementById("register-form").style.display = isLogin ? "none" : "block";
}

function clearAuthErrors() {
  document.getElementById("login-error").style.display = "none";
  document.getElementById("reg-error").style.display = "none";
  document.getElementById("reg-success").style.display = "none";
}

// ── Login ────────────────────────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  if (!authEnabled || !sbClient) {
    showAuthError("login", "Authentication not configured. Contact admin.");
    return;
  }

  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const btn = document.getElementById("login-btn");

  btn.textContent = "Signing in...";
  btn.disabled = true;

  try {
    const { data, error } = await sbClient.auth.signInWithPassword({ email, password });

    btn.textContent = "Sign In";
    btn.disabled = false;

    if (error) {
      showAuthError("login", error.message);
      return;
    }

    hideAuthModal();
    toast("Welcome back, " + (data.user.user_metadata?.full_name || email.split("@")[0]) + "!");
  } catch (ex) {
    btn.textContent = "Sign In";
    btn.disabled = false;
    showAuthError("login", "Unexpected error: " + ex.message);
  }
}

// ── Register ─────────────────────────────────────────────────────────────────
async function handleRegister(e) {
  e.preventDefault();
  if (!authEnabled || !sbClient) {
    showAuthError("reg", "Authentication not configured. Contact admin.");
    return;
  }

  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const company = document.getElementById("reg-company").value.trim();
  const password = document.getElementById("reg-password").value;
  const btn = document.getElementById("reg-btn");

  btn.textContent = "Creating account...";
  btn.disabled = true;

  const { data, error } = await sbClient.auth.signUp({
    email,
    password,
    options: {
      data: { full_name: name, company: company },
    },
  });

  btn.textContent = "Create Account";
  btn.disabled = false;

  if (error) {
    showAuthError("reg", error.message);
    return;
  }

  if (data.user && !data.user.confirmed_at) {
    const el = document.getElementById("reg-success");
    el.textContent = "Account created! Check your email to confirm, then sign in.";
    el.style.display = "block";
    document.getElementById("reg-error").style.display = "none";
  } else {
    hideAuthModal();
    toast("Account created! Welcome, " + name + "!");
  }
}

// ── Logout ───────────────────────────────────────────────────────────────────
async function handleLogout() {
  if (sbClient) {
    await sbClient.auth.signOut();
  }
  clearUser();
  toast("Signed out");
  document.getElementById("user-dropdown").style.display = "none";
}

// ── User Dropdown ────────────────────────────────────────────────────────────
function toggleUserDropdown() {
  const dd = document.getElementById("user-dropdown");
  dd.style.display = dd.style.display === "none" ? "block" : "none";
}

document.addEventListener("click", (e) => {
  const dd = document.getElementById("user-dropdown");
  const btn = document.getElementById("user-avatar-btn");
  if (dd.style.display !== "none" && !dd.contains(e.target) && !btn.contains(e.target)) {
    dd.style.display = "none";
  }
});

// ── Feedback Panel ───────────────────────────────────────────────────────────
function toggleFeedbackPanel() {
  const panel = document.getElementById("feedback-panel");
  const isOpen = panel.style.display !== "none";
  panel.style.display = isOpen ? "none" : "flex";
  if (!isOpen) loadMessages();
}

async function loadMessages() {
  if (!sbClient || !currentUser) return;

  const list = document.getElementById("messages-list");
  list.innerHTML = '<p style="color:#6b7280; text-align:center; padding:1rem;">Loading...</p>';

  const { data, error } = await sbClient
    .from("messages")
    .select("*")
    .eq("user_id", currentUser.id)
    .order("created_at", { ascending: false })
    .limit(50);

  if (error) {
    list.innerHTML = '<p style="color:#f87171; text-align:center; padding:1rem;">Failed to load messages</p>';
    return;
  }

  if (!data || data.length === 0) {
    list.innerHTML = '<p style="color:#6b7280; text-align:center; padding:2rem;">No messages yet. Send your first feedback!</p>';
    return;
  }

  list.innerHTML = data.map(m => `
    <div class="msg-bubble msg-user">
      <div class="msg-meta">
        <span class="msg-category msg-cat-${m.category}">${m.category}</span>
        <span class="msg-time">${timeAgo(m.created_at)}</span>
      </div>
      <p class="msg-text">${esc(m.content)}</p>
      ${m.admin_reply ? `
        <div class="msg-bubble msg-admin">
          <div class="msg-meta"><span style="color:#34d399; font-weight:600;">Admin</span> <span class="msg-time">${timeAgo(m.replied_at)}</span></div>
          <p class="msg-text">${esc(m.admin_reply)}</p>
        </div>
      ` : ''}
    </div>
  `).join("");
}

async function sendMessage(e) {
  e.preventDefault();
  if (!sbClient || !currentUser) {
    toast("Please sign in to send messages", "error");
    return;
  }

  const content = document.getElementById("msg-content").value.trim();
  const category = document.getElementById("msg-category").value;
  if (!content) return;

  const { error } = await sbClient.from("messages").insert({
    user_id: currentUser.id,
    user_email: currentUser.email,
    user_name: currentUser.user_metadata?.full_name || "",
    content,
    category,
  });

  if (error) {
    toast("Failed to send: " + error.message, "error");
    return;
  }

  document.getElementById("msg-content").value = "";
  toast("Message sent!");
  loadMessages();
}

function showMyMessages() {
  document.getElementById("user-dropdown").style.display = "none";
  const panel = document.getElementById("feedback-panel");
  panel.style.display = "flex";
  loadMessages();
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function showAuthError(prefix, msg) {
  const el = document.getElementById(prefix + "-error");
  el.textContent = msg;
  el.style.display = "block";
}

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return mins + "m ago";
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return hrs + "h ago";
  const days = Math.floor(hrs / 24);
  return days + "d ago";
}
