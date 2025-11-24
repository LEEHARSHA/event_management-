import React, { useState, useEffect } from 'react';
import { Plus, Sparkles, X, Loader2 } from 'lucide-react';
import EventCard from './components/EventCard'; // Import the component

const apiKey = "YOUR_API_KEY_HERE"; // Replace with your actual Gemini API Key

export default function App() {
  const [events, setEvents] = useState(() => {
    const saved = localStorage.getItem('ai_events_v1');
    return saved ? JSON.parse(saved) : [];
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: 'Any',
    eventType: ''
  });

  useEffect(() => {
    localStorage.setItem('ai_events_v1', JSON.stringify(events));
  }, [events]);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const generateEventPlan = async () => {
    if (!formData.name || !formData.age || !formData.eventType) {
      setError("Please fill in all required fields.");
      return;
    }

    setIsLoading(true);
    setError(null);

    const prompt = `
      Act as an expert event planner. Plan an event with the following details:
      - Name of person: ${formData.name}
      - Age: ${formData.age}
      - Gender: ${formData.gender}
      - Event Type: ${formData.eventType}

      Please generate a JSON object containing specific suggestions. 
      The JSON must strictly follow this schema:
      {
        "theme_suggestions": ["string", "string", "string"],
        "activities": ["string", "string", "string", "string"],
        "todo_list": ["string", "string", "string", "string", "string"],
        "gift_ideas": ["string", "string", "string", "string"]
      }
      
      Make the suggestions age-appropriate, creative, and fun.
      Return ONLY the raw JSON string. Do not use Markdown formatting.
    `;

    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to generate plan');

      const data = await response.json();
      const textResponse = data.candidates[0].content.parts[0].text;
      const cleanJson = textResponse.replace(/```json/g, '').replace(/```/g, '').trim();
      const aiData = JSON.parse(cleanJson);

      const newEvent = {
        id: Date.now(),
        ...formData,
        ...aiData,
        createdAt: new Date().toLocaleDateString()
      };

      setEvents([newEvent, ...events]);
      setIsModalOpen(false);
      setFormData({ name: '', age: '', gender: 'Any', eventType: '' });
    } catch (err) {
      console.error(err);
      setError("Oops! The AI had a hiccup. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const deleteEvent = (id) => {
    setEvents(events.filter(e => e.id !== id));
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-purple-200">
      {/* Background Blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-20 -left-20 w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-0 -right-20 w-96 h-96 bg-cyan-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-20 w-96 h-96 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <header className="flex flex-col md:flex-row md:items-center justify-between mb-12">
          <div className="mb-4 md:mb-0">
            <h1 className="text-4xl md:text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600">
              EventFlow AI
            </h1>
            <p className="text-slate-500 mt-2 text-lg">Smart planning for unforgettable moments.</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="group flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white px-6 py-3 rounded-full font-semibold shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1"
          >
            <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
            Create New Event
          </button>
        </header>

        {events.length === 0 && (
          <div className="text-center py-20 bg-white/50 backdrop-blur-sm rounded-3xl border border-dashed border-slate-300">
            <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-slate-700">No events planned yet</h3>
            <p className="text-slate-500 mt-2">Click the button above to let AI plan your first celebration!</p>
          </div>
        )}

        <div className="grid grid-cols-1 gap-8">
          {events.map((event) => (
            <EventCard key={event.id} event={event} onDelete={deleteEvent} />
          ))}
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm transition-opacity">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden relative animate-in fade-in zoom-in duration-300">
            <div className="bg-gradient-to-r from-violet-600 to-indigo-600 p-6 text-white">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  Plan an Event
                </h2>
                <button onClick={() => setIsModalOpen(false)} className="hover:bg-white/20 p-1 rounded-full transition-colors">
                  <X className="w-6 h-6" />
                </button>
              </div>
              <p className="text-indigo-100 mt-1 text-sm">Tell us a little bit, we'll do the rest.</p>
            </div>

            <div className="p-6 space-y-4">
              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm font-medium">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Event Name / Occasion</label>
                <input
                  type="text"
                  name="eventType"
                  placeholder="e.g. Birthday, Anniversary, Graduation"
                  value={formData.eventType}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-violet-500 focus:ring-2 focus:ring-violet-200 transition-all outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Who is it for?</label>
                <input
                  type="text"
                  name="name"
                  placeholder="Person's Name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-violet-500 focus:ring-2 focus:ring-violet-200 transition-all outline-none"
                />
              </div>

              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-700 mb-1">Age</label>
                  <input
                    type="number"
                    name="age"
                    placeholder="25"
                    value={formData.age}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-violet-500 focus:ring-2 focus:ring-violet-200 transition-all outline-none"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-700 mb-1">Gender</label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-violet-500 focus:ring-2 focus:ring-violet-200 transition-all outline-none bg-white"
                  >
                    <option value="Any">Any</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Non-binary">Non-binary</option>
                  </select>
                </div>
              </div>

              <button
                onClick={generateEventPlan}
                disabled={isLoading}
                className="w-full mt-4 bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700 text-white font-bold py-3 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Consulting AI...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate Magic Plan
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
