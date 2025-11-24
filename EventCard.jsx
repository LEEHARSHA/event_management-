import React, { useState } from 'react';
import { Trash2, Gift, CheckSquare, User, PartyPopper, ChevronDown, ChevronUp } from 'lucide-react';

export default function EventCard({ event, onDelete }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden hover:shadow-2xl transition-shadow duration-300">
      <div className="p-6 md:p-8">
        {/* Card Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-100 to-fuchsia-100 flex items-center justify-center text-3xl shadow-inner">
              🎉
            </div>
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-slate-800">{event.eventType}</h2>
              <div className="flex items-center gap-3 text-slate-500 mt-1 text-sm md:text-base">
                <span className="flex items-center gap-1"><User className="w-4 h-4" /> {event.name}</span>
                <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                <span>{event.age} Years Old</span>
                <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                <span>{event.gender}</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => onDelete(event.id)}
            className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-lg transition-colors"
            title="Delete Event"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>

        {/* Theme Chips */}
        <div className="flex flex-wrap gap-2 mb-8">
          {event.theme_suggestions?.map((theme, i) => (
            <span key={i} className="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-sm font-medium border border-indigo-100">
              ✨ {theme}
            </span>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          
          {/* To-Do List */}
          <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
            <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-4">
              <CheckSquare className="w-5 h-5 text-emerald-500" />
              To-Do List
            </h3>
            <ul className="space-y-3">
              {event.todo_list?.slice(0, expanded ? undefined : 3).map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                  <div className="mt-1 min-w-[6px] h-[6px] rounded-full bg-emerald-400"></div>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Activities */}
          <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
            <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-4">
              <PartyPopper className="w-5 h-5 text-orange-500" />
              Fun Activities
            </h3>
            <ul className="space-y-3">
              {event.activities?.slice(0, expanded ? undefined : 3).map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                  <div className="mt-1 min-w-[6px] h-[6px] rounded-full bg-orange-400"></div>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Gift Ideas */}
          <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
            <h3 className="font-bold text-slate-800 flex items-center gap-2 mb-4">
              <Gift className="w-5 h-5 text-pink-500" />
              Best Gifts
            </h3>
            <ul className="space-y-3">
              {event.gift_ideas?.slice(0, expanded ? undefined : 3).map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                  <div className="mt-1 min-w-[6px] h-[6px] rounded-full bg-pink-400"></div>
                  {item}
                </li>
              ))}
            </ul>
          </div>

        </div>

        {/* Expand/Collapse Toggle */}
        <button 
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-6 py-2 flex items-center justify-center gap-1 text-slate-400 hover:text-violet-600 text-sm font-medium transition-colors border-t border-slate-100"
        >
          {expanded ? (
            <>Show Less <ChevronUp className="w-4 h-4" /></>
          ) : (
            <>View Full Plan <ChevronDown className="w-4 h-4" /></>
          )}
        </button>
      </div>
    </div>
  );
}
