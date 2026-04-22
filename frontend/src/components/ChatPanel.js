import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Loader2, Bot, User, Zap, AlertCircle, Wrench } from 'lucide-react';
import { api } from '../services/api';

const SUGGESTED_QUESTIONS = [
  'What are the key trends in this dataset?',
  'Are there any anomalies or outliers I should know about?',
  'What are the top performing segments?',
  'Summarize the main insights from this data.',
  'What correlations exist between the variables?',
];

function EventBadge({ event }) {
  if (event.type === 'thinking') {
    return (
      <div className="event-badge thinking">
        <Loader2 size={12} className="spin" /> {event.content}
      </div>
    );
  }
  if (event.type === 'tool_call') {
    return (
      <div className="event-badge tool-call">
        <Wrench size={12} /> Calling <strong>{event.content.tool}</strong>
        {Object.keys(event.content.args).length > 0 && (
          <span className="tool-args"> ({JSON.stringify(event.content.args)})</span>
        )}
      </div>
    );
  }
  if (event.type === 'tool_result') {
    return (
      <div className="event-badge tool-result">
        <Zap size={12} /> Tool result received ({
          typeof event.content === 'object'
            ? `${Object.keys(event.content).length} fields`
            : 'data'
        })
      </div>
    );
  }
  if (event.type === 'error') {
    return (
      <div className="event-badge error">
        <AlertCircle size={12} /> {event.content}
      </div>
    );
  }
  return null;
}

export default function ChatPanel({ datasetId, model }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamEvents, setStreamEvents] = useState([]);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamEvents]);

  const sendMessage = async (text) => {
    const userText = text || input.trim();
    if (!userText || loading) return;
    setInput('');
    setLoading(true);
    setStreamEvents([]);

    const newMessages = [...messages, { role: 'user', content: userText }];
    setMessages(newMessages);

    const history = newMessages.slice(0, -1).map(m => ({ role: m.role, content: m.content }));

    try {
      let answer = '';
      const events = [];

      for await (const event of api.chatStream(userText, datasetId, history, model)) {
        events.push(event);
        if (event.type === 'answer') {
          answer = event.content;
        }
        setStreamEvents([...events]);
      }

      setMessages(prev => [...prev, { role: 'assistant', content: answer, events }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}. Make sure Ollama is running and the model is available.`,
        isError: true,
      }]);
    } finally {
      setLoading(false);
      setStreamEvents([]);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <Bot size={48} className="chat-empty-icon" />
            <h3>Ask anything about your data</h3>
            <p>The AI agent will analyze your dataset and provide real-time insights.</p>
            <div className="suggested-questions">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button key={i} className="suggested-btn" onClick={() => sendMessage(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className="message-body">
              {msg.events && msg.events.filter(e => e.type !== 'answer' && e.type !== 'done').map((ev, j) => (
                <EventBadge key={j} event={ev} />
              ))}
              <div className={`message-content ${msg.isError ? 'error-content' : ''}`}>
                {msg.role === 'assistant'
                  ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                  : <p>{msg.content}</p>
                }
              </div>
            </div>
          </div>
        ))}

        {loading && streamEvents.length > 0 && (
          <div className="message assistant streaming">
            <div className="message-avatar"><Bot size={16} /></div>
            <div className="message-body">
              {streamEvents.filter(e => e.type !== 'answer' && e.type !== 'done').map((ev, j) => (
                <EventBadge key={j} event={ev} />
              ))}
              <div className="typing-indicator">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
          }}
          placeholder={datasetId ? `Ask about ${datasetId}…` : 'Upload a dataset first, then ask questions…'}
          rows={2}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          {loading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}
