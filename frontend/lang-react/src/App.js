import React, { useState, useRef, useEffect } from 'react';
import { Send, RefreshCw, FileText, X, Mic } from 'lucide-react';

const App = () => {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chatMessages');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      handleSubmit(null, true);
    }
  }, []);

  const handleSubmit = async (e, isNewChat = false) => {
    if (e) e.preventDefault();
    if (!isNewChat && !input.trim()) return;

    const userMessage = isNewChat ? null : { role: 'user', content: input };
    if (!isNewChat) {
      setMessages(prev => [...prev, userMessage]);
      setInput('');
    }
    setIsLoading(true);

    try {
      const response = await fetch('/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: isNewChat ? "Start the lesson" : input,
          context: messages.map(m => `${m.role}: ${m.content}`).join('\n'),
          is_new_chat: isNewChat
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage = { role: 'assistant', content: data.response };
      setMessages(prev => isNewChat ? [assistantMessage] : [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { role: 'error', content: `Failed to get response. Error: ${error.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setFeedback(null);
    localStorage.removeItem('chatMessages');
    handleSubmit(null, true);
  };

  const insertSpecialChar = (char) => {
    const cursorPosition = inputRef.current.selectionStart;
    const newInput = input.slice(0, cursorPosition) + char + input.slice(cursorPosition);
    setInput(newInput);

    setTimeout(() => {
      inputRef.current.setSelectionRange(cursorPosition + 1, cursorPosition + 1);
      inputRef.current.focus();
    }, 0);
  };

  const getFeedback = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context: messages.map(m => `${m.role}: ${m.content}`).join('\n')
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setFeedback(data.feedback);
      setShowFeedback(true);  // Show the feedback pop-up when we get the feedback
    } catch (error) {
      console.error('Error:', error);
      setFeedback(`Failed to get feedback. Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const formatFeedback = (feedbackString) => {
    if (!feedbackString) return null;

    const parts = feedbackString.split(/(?=\d+\.\s)/);
    return parts.map((part, index) => {
      const [number, ...content] = part.split(/(?<=^\d+\.)\s/);
      const formattedContent = content.join(' ').split('-').map((item, i) =>
        i === 0 ? item : <React.Fragment key={i}><br />• {item.trim()}</React.Fragment>
      );

      return (
        <React.Fragment key={index}>
          <strong>{number}</strong> {formattedContent}
          {index < parts.length - 1 && <br />}
        </React.Fragment>
      );
    });
  };



  return (
    <div className="flex flex-col h-screen bg-[#003b46] text-[#c0dee5] font-['Comfortaa']">
      <header className="bg-[#003b46] p-4 text-center">
        <h1 className="text-2xl font-bold">Learn Español (Spanish) with Lang</h1>
      </header>
      <main className="flex-grow flex flex-col p-2 max-w-4xl mx-auto w-full overflow-hidden">
        <div className="flex-grow mx-2 overflow-auto mb-4 bg-[#07575b] rounded-lg">
          <div className="max-h-full overflow-y-auto p-3 bg-[#003b46]">
            {messages.map((message, index) => (
              <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                <span className={`inline-block p-3 rounded-lg ${message.role === 'user' ? 'bg-[#07575b] text-[#c0dee5]' :
                  message.role === 'assistant' ? 'bg-[#07575b] text-[#c0dee5]' : 'bg-[#ff6b6b] text-[#c0dee5]'
                  } max-w-[80%] break-words ${index === messages.length - 1 ? 'animate-fade-in' : ''}`}>
                  {message.content}
                </span>
              </div>
            ))}
            {showFeedback && feedback && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
                <div className="bg-[#07575b] rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                  <div className="flex justify-between items-center p-4 border-b border-[#003b46]">
                    <h3 className="font-bold bg-[#003b46] text-xl">Progress Summary</h3>
                    <button
                      onClick={() => setShowFeedback(false)}
                      className="text-[#c0dee5] hover:text-white transition-colors"
                    >
                      <X size={24} />
                    </button>
                  </div>
                  <div className="p-4">
                    {formatFeedback(feedback)}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
        <form onSubmit={(e) => handleSubmit(e, false)} className="flex flex-col gap-2">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message here..."
              className="flex-grow bg-[#07575b] text-[#c0dee5] rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-[#07575b]"
              disabled={isLoading}
            />
            <button
              type="button"
              className="bg-[#07575b] text-[#c0dee5] p-3 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b]">
              <Mic size={24} />
            </button>
            <button
              type="submit"
              className="bg-[#07575b] text-[#c0dee5] p-3 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b]"
              disabled={isLoading}
            >
              <Send size={24} />
            </button>
          </div>
          <div className="flex justify-center gap-2 mt-2">
            {['¿', '¡', 'ü', 'ñ', 'é', 'á', 'í', 'ó', 'ú'].map((char) => (
              <button
                key={char}
                type="button"
                onClick={() => insertSpecialChar(char)}
                className="bg-[#07575b] text-[#c0dee5] px-3 py-1 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b]"
              >
                {char}
              </button>
            ))}
          </div>
        </form>
      </main>
      <footer className="bg-[#003b46] p-4 text-center flex justify-center gap-4">
        <button
          onClick={startNewChat}
          className="flex items-center justify-center bg-[#07575b] text-[#c0dee5] p-2 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b]"
          disabled={isLoading}
        >
          <RefreshCw size={20} className="mr-2" /> New Chat
        </button>
        <button
          onClick={getFeedback}
          className="flex items-center justify-center bg-[#07575b] text-[#c0dee5] p-2 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b]"
          disabled={isLoading}
        >
          <FileText size={20} className="mr-2" /> Get Summary
        </button>
      </footer>
    </div>
  );
};

export default App;