import React, { useEffect, useState, useRef } from "react";

// Firebase SDK imports (assuming global scripts available)
import {
  initializeApp
} from "firebase/app";
import {
  getAuth,
  signInWithCustomToken,
  signInAnonymously,
  onAuthStateChanged
} from "firebase/auth";
import {
  getFirestore,
  doc,
  collection,
  onSnapshot,
  setDoc,
  addDoc,
  serverTimestamp,
} from "firebase/firestore";

// Simple Markdown to HTML rendering
function markdownToHtml(md = "") {
  // Basic, safe replacements for demo (bold, italics, lists, headers, code, links, line breaks)
  let html = md
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/gim, "<b>$1</b>")
    .replace(/\*(.*?)\*/gim, "<i>$1</i>")
    .replace(/^\s*[-+*] (.*)$/gim, "<li>$1</li>")
    .replace(/`([^`]+)`/gim, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, `<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>`)
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>");
  // wrap <li> in <ul> if present
  if (html.match(/<li>/)) {
    html = html.replace(/(<li>[\s\S]*?<\/li>)/gim, "<ul>$1</ul>");
    html = html.replace(/<\/ul>\s*<ul>/g, ""); // collapse lists
  }
  html = "<p>" + html + "</p>";
  return html;
}

const EVENT_TYPES = [
  "Birthday",
  "Wedding",
  "Corporate",
  "Anniversary",
  "Graduation",
  "Baby Shower",
  "Other"
];

function formatDate(dt) {
  if (!dt) return "";
  const d = new Date(dt);
  return d.toLocaleString();
}

// Time until/fmt
function timeUntil(dateString) {
  const now = new Date();
  const dt = new Date(dateString);
  const diffMs = dt.getTime() - now.getTime();
  if (diffMs <= 0) return "Started";
  const h = Math.floor(diffMs / (1000 * 60 * 60));
  const m = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

// Gemini (Google AI) API call
async function callGeminiAPI({ system, prompt, authToken }) {
  const body = {
    contents: [
      { role: "user", parts: [{ text: prompt }] }
    ],
    system_instruction: { role: "system", parts: [{ text: system }] }
  };
  const res = await fetch(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authToken && {
          "Authorization": `Bearer ${authToken}`
        }),
        "x-goog-api-key": "" // KEYLESS for security reasons, expects backend with proxy/key
      },
      body: JSON.stringify(body)
    }
  );
  if (!res.ok) throw new Error(`Gemini API error (${res.status})`);
  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text ?? "";
  return text.trim();
}

const loadingBtnStyle = "pointer-events-none opacity-70";

const firestorePath = (appId, userId) =>
  `/artifacts/${appId}/users/${userId}/events`;

function App() {
  // Basic global state
  const [user, setUser] = useState(null);
  const [db, setDb] = useState(null);
  const [events, setEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [eventError, setEventError] = useState("");
  const [loadingAuth, setLoadingAuth] = useState(true);

  // Form state
  const [form, setForm] = useState({
    name: "",
    type: EVENT_TYPES[0],
    datetime: "",
    recipient: ""
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState("");

  // AI Generation state
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [planPreview, setPlanPreview] = useState("");
  const [giftsPreview, setGiftsPreview] = useState("");
  const [activeView, setActiveView] = useState(null); // eventId
  const [showModal, setShowModal] = useState(false);

  // Init firebase app+auth
  useEffect(() => {
    let unsub = null;
    async function init() {
      try {
        // Import provided config from global
        const app = initializeApp(__firebase_config);
        const auth = getAuth(app);
        const _db = getFirestore(app);

        setDb(_db);
        // Try custom token first
        let currentUser = null;
        setLoadingAuth(true);
        try {
          await signInWithCustomToken(auth, __initial_auth_token);
        } catch (err) {
          await signInAnonymously(auth);
        }
        // Get user (wait for ready)
        unsub = onAuthStateChanged(auth, (usr) => {
          if (usr) {
            setUser(usr);
            setLoadingAuth(false);
          }
        });
      } catch (error) {
        setEventError("Failed to initialize Firebase: " + error.message);
        setLoadingAuth(false);
      }
    }
    init();
    return () => { if (unsub) unsub(); };
  }, []);

  // Listen to Firestore event list
  useEffect(() => {
    if (!user || !db) return;
    setLoadingEvents(true);
    setEventError("");
    const cRef = collection(
      db,
      "artifacts",
      __app_id,
      "users",
      user.uid,
      "events"
    );
    const unsub = onSnapshot(
      cRef,
      (snap) => {
        const evs = [];
        snap.forEach((doc) => {
          evs.push({ ...doc.data(), id: doc.id });
        });
        // Sort upcoming first
        evs.sort((a, b) =>
          (a.datetime || "") > (b.datetime || "") ? 1 : -1
        );
        setEvents(evs);
        setLoadingEvents(false);
      },
      (err) => {
        setEventError("Failed to load events: " + err.message);
        setLoadingEvents(false);
      }
    );
    return unsub;
  }, [user, db]);

  // Handle form inputs
  function handleFormChange(e) {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  }

  // Save event without AI plan (fast, no plan/gifts)
  async function handleEventCreate(e) {
    e.preventDefault();
    setFormError("");
    setFormLoading(true);
    if (
      !form.name.trim() ||
      !form.type.trim() ||
      !form.datetime ||
      !form.recipient.trim()
    ) {
      setFormError("All fields are required.");
      setFormLoading(false);
      return;
    }
    try {
      await addDoc(
        collection(
          db,
          "artifacts",
          __app_id,
          "users",
          user.uid,
          "events"
        ),
        {
          name: form.name,
          type: form.type,
          datetime: form.datetime,
          recipient: form.recipient,
          created: serverTimestamp(),
          plan: "",
          gifts: "",
          aiReady: false
        }
      );
      setForm({
        name: "",
        type: EVENT_TYPES[0],
        datetime: "",
        recipient: ""
      });
    } catch (err) {
      setFormError("Error creating event: " + err.message);
    }
    setFormLoading(false);
  }

  // AI PLAN+GIFT suggestion on an event
  async function generateAIContent(eventObj, eventId) {
    setAiError("");
    setAiLoading(true);
    setPlanPreview("");
    setGiftsPreview("");
    let aiPlan = "",
      aiGifts = "";
    const authToken = user?.stsTokenManager?.accessToken || undefined;
    try {
      // 1. Event Plan
      const sysPlan =
        "You are an expert event planner. Provide a detailed, step-by-step organizational plan for the event requested, covering logistics, timeline, and key actions. Respond in markdown format.";
      const userPlanPrompt = `Event Name: ${eventObj.name}
Event Type: ${eventObj.type}
Date/Time: ${formatDate(eventObj.datetime)}
Recipient/Audience: ${eventObj.recipient}`;

      aiPlan = await callGeminiAPI({
        system: sysPlan,
        prompt: userPlanPrompt,
        authToken
      });
      setPlanPreview(aiPlan);

      // 2. Gift Suggestions
      const sysGifts =
        "You are an expert gift advisor. Suggest 5 appropriate, creative, and memorable gift ideas for the specific event and recipient context provided. Format the output as an unordered markdown list.";
      const userGiftPrompt = userPlanPrompt;

      aiGifts = await callGeminiAPI({
        system: sysGifts,
        prompt: userGiftPrompt,
        authToken
      });
      setGiftsPreview(aiGifts);

      // 3. Write both outputs to Firestore
      await setDoc(
        doc(
          db,
          "artifacts",
          __app_id,
          "users",
          user.uid,
          "events",
          eventId
        ),
        {
          ...eventObj,
          plan: aiPlan,
          gifts: aiGifts,
          aiReady: true
        }
      );
      setAiLoading(false);
    } catch (err) {
      setAiError("Failed to get AI response: " + err.message);
      setAiLoading(false);
    }
  }

  // Compute upcoming events within next 48h for reminders
  const nowIso = new Date().toISOString();
  const reminders = (events || []).filter((ev) => {
    if (!ev.datetime) return false;
    const dt = new Date(ev.datetime);
    const now = new Date();
    const diff = dt.getTime() - now.getTime();
    return diff > 0 && diff <= 1000 * 60 * 60 * 48;
  });

  // ---- UI ----
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gradient-to-r from-blue-700 to-sky-500 py-6 px-4 text-white shadow-md">
        <div className="max-w-3xl mx-auto flex flex-col items-center">
          <h1 className="text-3xl font-extrabold tracking-tight mb-1">
            AI Event Manager
          </h1>
          <p className="text-lg text-white/90">
            Your AI-powered event planner &amp; gift advisor
          </p>
        </div>
      </header>

      {/* Reminders */}
      <section className="max-w-3xl mx-auto mt-6 px-4">
        {reminders.length > 0 && (
          <div className="mb-6">
            <div className="bg-yellow-100 border-l-4 border-yellow-500 rounded p-4 flex items-start gap-3 shadow">
              <span className="inline-block bg-yellow-400 text-yellow-900 px-2 py-1 rounded font-bold text-xs mr-2">
                REMINDERS
              </span>
              <div className="flex-1">
                <span className="font-semibold">
                  {reminders.length === 1 ? "Upcoming Event:" : "Upcoming Events:"}
                </span>
                <ul className="list-disc pl-4">
                  {reminders.map((ev) => (
                    <li key={ev.id} className="mt-1 flex items-center gap-2">
                      <span className="font-medium">{ev.name}</span>
                      <span className="bg-white rounded px-2 py-0.5 text-yellow-700 text-xs border border-yellow-300 ml-2">
                        in {timeUntil(ev.datetime)}
                      </span>
                      <span className="text-gray-500 text-xs ml-3">
                        ({formatDate(ev.datetime)})
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Event Form */}
      <main className="max-w-3xl mx-auto bg-white p-6 mt-4 mb-10 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-1">Create a New Event</h2>
        <p className="text-gray-600 mb-4">
          Fill in the details and save to create your event. Then, click <b>Generate Plan & Gifts</b> to have AI assist you!
        </p>
        <form
          className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end"
          onSubmit={handleEventCreate}
        >
          <div>
            <label className="block text-sm font-medium mb-1">
              Event Name
              <input
                name="name"
                value={form.name}
                onChange={handleFormChange}
                disabled={formLoading}
                className="mt-1 w-full px-3 py-2 border rounded outline-none focus:ring-2 focus:ring-sky-300"
                required
                autoComplete="off"
                placeholder="e.g., Anna's 30th Birthday"
              />
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Event Type
              <select
                name="type"
                value={form.type}
                onChange={handleFormChange}
                disabled={formLoading}
                className="mt-1 w-full px-3 py-2 border rounded outline-none focus:ring-2 focus:ring-sky-300"
                required
              >
                {EVENT_TYPES.map((tp) => (
                  <option key={tp} value={tp}>{tp}</option>
                ))}
              </select>
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Event Date/Time
              <input
                name="datetime"
                value={form.datetime}
                onChange={handleFormChange}
                type="datetime-local"
                min={new Date().toISOString().slice(0,16)}
                disabled={formLoading}
                className="mt-1 w-full px-3 py-2 border rounded outline-none focus:ring-2 focus:ring-sky-300"
                required
              />
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Target Audience / Recipient Details
              <textarea
                name="recipient"
                value={form.recipient}
                onChange={handleFormChange}
                disabled={formLoading}
                className="mt-1 w-full px-3 py-2 border rounded outline-none focus:ring-2 focus:ring-sky-300 min-h-[2.5rem]"
                rows={2}
                required
                placeholder="e.g., My sister, turning 30, loves hiking."
              />
            </label>
          </div>
          <div className="md:col-span-2 flex justify-end gap-2">
            <button
              type="submit"
              className={`bg-sky-700 text-white px-6 py-2 rounded shadow font-bold hover:bg-sky-800 focus:ring-2 focus:ring-sky-400 transition ${
                formLoading ? loadingBtnStyle : ""
              }`}
              disabled={formLoading}
            >
              {formLoading ? "Saving..." : "Save Event"}
            </button>
          </div>
        </form>
        {formError && (
          <div className="text-red-600 text-sm mt-2">{formError}</div>
        )}
      </main>

      {/* Event List */}
      <section className="max-w-3xl mx-auto px-4 mb-16">
        <h2 className="text-xl font-bold mb-2">Your Events</h2>
        {loadingAuth && (
          <div className="text-gray-500 py-8">Authenticating...</div>
        )}
        {eventError && (
          <div className="text-red-600 mt-3 mb-6">{eventError}</div>
        )}
        {loadingEvents && !events.length && (
          <div className="py-10 text-center text-gray-600">Loading your events...</div>
        )}

        {/* No events */}
        {!loadingEvents && !events.length && (
          <div className="py-12 text-center text-gray-400">
            <div className="text-5xl mb-3">🗓️</div>
            <div>No events added yet.<br />Create your first event!</div>
          </div>
        )}
        {/* Render event cards */}
        <div className="grid md:grid-cols-2 gap-5">
          {events.map((ev) => (
            <div
              key={ev.id}
              className="relative group bg-white border border-gray-200 rounded-lg shadow hover:shadow-xl transition cursor-pointer overflow-hidden"
            >
              {/* Highlight if upcoming */}
              <div
                className={`absolute right-3 top-3 z-10 font-semibold text-xs ${
                  reminders.find((r) => r.id === ev.id)
                    ? "bg-yellow-400 text-yellow-900 px-2 py-1 rounded"
                    : ""
                }`}
              >
                {reminders.find((r) => r.id === ev.id)
                  ? <>⏰ Soon</>
                  : ""}
              </div>
              <div
                className="p-5"
                onClick={() => {
                  setActiveView(ev.id);
                  setShowModal(true);
                  setPlanPreview("");
                  setGiftsPreview("");
                  setAiError("");
                }}
              >
                <h3 className="font-bold text-lg">{ev.name}</h3>
                <div className="flex items-center gap-2 text-gray-700 text-sm mt-2">
                  <span className="bg-gray-100 rounded px-2 py-0.5 text-xs mr-1 border border-sky-100">
                    {ev.type}
                  </span>
                  <span className="ml-1">
                    {formatDate(ev.datetime)}
                  </span>
                </div>
                <div className="text-gray-500 text-xs mt-1">
                  Recipient: {ev.recipient?.length > 30
                    ? ev.recipient.slice(0, 30) + "..."
                    : ev.recipient}
                </div>
                {ev.aiReady ? (
                  <div className="mt-3 py-1 px-3 bg-emerald-100 text-emerald-800 rounded text-xs font-medium inline-block">
                    <span className="mr-1">✓</span>AI plan + gifts ready!
                  </div>
                ) : (
                  <div className="mt-3 py-1 px-3 bg-gray-50 border text-gray-500 rounded text-xs font-medium inline-block">
                    <span className="mr-1">⏳</span>
                    AI plan not generated yet
                  </div>
                )}
              </div>
              {!ev.aiReady && (
                <button
                  disabled={aiLoading}
                  className={`w-full py-2 font-semibold tracking-wider bg-gradient-to-r from-pink-500 to-sky-600 text-white text-sm
                     hover:from-pink-600 hover:to-sky-700 transition disabled:opacity-60 disabled:pointer-events-none`}
                  onClick={async (e) => {
                    e.stopPropagation();
                    setActiveView(ev.id);
                    setShowModal(true);
                    setPlanPreview("");
                    setGiftsPreview("");
                    await generateAIContent(ev, ev.id);
                  }}
                >
                  {aiLoading && activeView === ev.id
                    ? "Generating..."
                    : "Generate Plan & Gifts"}
                </button>
              )}
              {/* Open Details Button */}
              <button
                className="absolute top-2 left-2 bg-sky-200 text-sky-900 px-2 py-0.5 rounded text-xs shadow hover:bg-sky-400 transition hidden group-hover:block"
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveView(ev.id);
                  setShowModal(true);
                  setPlanPreview("");
                  setGiftsPreview("");
                  setAiError("");
                }}
              >
                Details
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Modal for event details */}
      {showModal && activeView && (() => {
        const ev = events.find((e) => e.id === activeView);
        if (!ev) return null;
        return (
          <div className="fixed z-50 inset-0 flex items-center justify-center bg-black/40">
            <div className="bg-white rounded-lg max-w-lg w-full shadow-2xl relative flex flex-col">
              <button
                className="absolute right-3 top-3 text-gray-400 hover:text-red-500 text-2xl"
                onClick={() => {
                  setShowModal(false);
                  setActiveView(null);
                }}
                aria-label="Close"
              >
                &times;
              </button>
              <div className="p-6 pt-10 overflow-y-auto max-h-[85vh]">
                <h2 className="font-extrabold text-xl mb-1">{ev.name}</h2>
                <div className="text-sm mb-2 text-gray-500">
                  <b>Type:</b> {ev.type}
                  <br />
                  <b>Date/Time:</b> {formatDate(ev.datetime)}
                  <br />
                  <b>Recipient:</b> {ev.recipient}
                </div>
                <div className="mt-4 mb-2 flex gap-2 items-center">
                  {!ev.aiReady && (
                    <button
                      className={`bg-gradient-to-r from-pink-500 to-sky-600 text-white font-bold px-4 py-2 rounded shadow hover:from-pink-700 hover:to-sky-700 transition ${
                        aiLoading ? loadingBtnStyle : ""
                      }`}
                      disabled={aiLoading}
                      onClick={async () => {
                        await generateAIContent(ev, ev.id);
                      }}
                    >
                      {aiLoading ? "Generating..." : "Generate Plan & Gifts"}
                    </button>
                  )}
                  {ev.aiReady && (
                    <span className="inline-flex items-center px-2 py-1 bg-emerald-100 text-emerald-800 rounded text-xs font-semibold">
                      <span className="mr-1">✓</span>AI Content Ready
                    </span>
                  )}
                </div>
                {/* AI Plan */}
                <div className="mt-6">
                  <div className="text-gray-800 font-bold mb-2 text-base">
                    AI Event Plan
                  </div>
                  {aiLoading && !ev.plan && (
                    <div className="text-xs text-gray-500 mb-1">
                      Generating plan...
                    </div>
                  )}
                  <div
                    className="prose prose-sm max-w-full"
                    dangerouslySetInnerHTML={{
                      __html: markdownToHtml(
                        planPreview || ev.plan || (aiLoading ? "Generating..." : "Not available")
                      )
                    }}
                  />
                </div>
                {/* Gift Suggestions */}
                <div className="mt-7">
                  <div className="text-gray-800 font-bold mb-2 text-base">
                    AI Gift Suggestions
                  </div>
                  {aiLoading && !ev.gifts && (
                    <div className="text-xs text-gray-500 mb-1">
                      Generating gifts...
                    </div>
                  )}
                  <div
                    className="prose prose-sm max-w-full"
                    dangerouslySetInnerHTML={{
                      __html: markdownToHtml(
                        giftsPreview || ev.gifts || (aiLoading ? "Generating..." : "Not available")
                      )
                    }}
                  />
                </div>
                {/* Error output */}
                {aiError && (
                  <div className="text-xs text-red-600 mt-3">{aiError}</div>
                )}
              </div>
            </div>
          </div>
        );
      })()}
      <footer className="text-center text-xs text-gray-400 py-8">
        &copy; {new Date().getFullYear()} AI Event Manager. Powered by Firebase & Gemini API.<br />
        Data stored securely in your personal private cloud.
      </footer>
    </div>
  );
}

export default App;

