import React, { useState, useRef, useEffect } from 'react';
import { Send, RefreshCw, FileText, X, Mic, Speech } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost';

const App = () => {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chatMessages');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [audioSrc, setAudioSrc] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioChunks, setAudioChunks] = useState([]);
  const [recordingStatus, setRecordingStatus] = useState('');
  const [processingStatus, setProcessingStatus] = useState('');
  const [error, setError] = useState(null);
  const mediaRecorderRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const audioRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      handleSubmit(null, true);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSubmit = async (e, isNewChat = false) => {
    if (e) e.preventDefault();
    if (!isNewChat && (!input || typeof input !== 'string' || input.trim() === '')) return;

    const userMessage = isNewChat ? null : { role: 'user', content: input };
    if (!isNewChat) {
      setMessages(prev => [...prev, userMessage]);
      setInput('');
    }
    setIsLoading(true);
    setProcessingStatus('Processing request...');

    try {
      const response = await fetch(`${API_URL}/api/learn`, {
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
      setAudioSrc(`data:audio/mp3;base64,${data.audio}`);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { role: 'error', content: `Failed to get response. Error: ${error.message}` }]);
    } finally {
      setIsLoading(false);
      setProcessingStatus('');
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
      const response = await fetch(`${API_URL}/api/feedback`, {
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
      setShowFeedback(true);
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
      const [number, ...content] = part.trim().split(/(?<=^\d+\.)\s/);
      const formattedContent = content.join(' ').split('-').map((item, i) =>
        i === 0 ? item.trim() : (
          <React.Fragment key={i}>
            <br />• {item.trim()}
          </React.Fragment>
        )
      );

      return (
        <React.Fragment key={index}>
          <strong>{number}</strong> {formattedContent}
          {index < parts.length - 1 && <br />}
        </React.Fragment>
      );
    });
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      setAudioChunks([]);
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks((chunks) => [...chunks, event.data]);
        }
      };

      mediaRecorder.onstart = () => {
        setRecordingStatus('Recording...');
      };

      mediaRecorder.onstop = () => {
        setRecordingStatus('Processing audio...');
      };

      mediaRecorder.start();
      setIsRecording(true);
      setError(null);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Failed to access microphone. Please check your permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    }
  };

  const sendAudioToServer = async () => {
    if (audioChunks.length === 0) {
      setError('No audio recorded. Please try again.');
      setRecordingStatus('');
      return;
    }

    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'output.wav');

    try {
      setIsLoading(true);
      const response = await fetch(`${API_URL}/api/speech-to-text`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.transcript) {
        setInput(data.transcript);
        setError(null);
        setRecordingStatus('Transcription complete');
      } else {
        throw new Error('No transcription returned from server');
      }
    } catch (error) {
      console.error('Error sending audio to server:', error);
      setError(`Failed to transcribe audio: ${error.message}`);
    } finally {
      setIsLoading(false);
      setAudioChunks([]);
      setTimeout(() => setRecordingStatus(''), 3000); // Clear status after 3 seconds
    }
  };

  useEffect(() => {
    if (audioChunks.length > 0 && !isRecording) {
      sendAudioToServer();
    }
  }, [audioChunks, isRecording]);


  const toggleAudio = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.onended = () => {
        setIsPlaying(false);
      };
    }
  }, [audioSrc]);


  return (
    <div className="flex flex-col h-screen bg-[#003b46] text-[#c0dee5] font-['Comfortaa']">
      <header className="bg-[#003b46] p-4 text-center">
        <h1 className="text-2xl font-bold">Learn Español with Lang</h1>
      </header>
      <main className="flex-grow flex flex-col p-2 max-w-4xl mx-auto w-full overflow-hidden">
        <div className="flex-grow mx-2 overflow-auto mb-4 bg-[#003b46] rounded-lg">
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
                  <div className="flex justify-between items-center p-4 bg-[#003b46]">
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
              value={input || ''}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message here..."
              className="flex-grow bg-[#07575b] text-[#c0dee5] rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-[#07575b]"
              disabled={isLoading || isRecording}
            />
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              className={`bg-[#07575b] text-[#c0dee5] p-3 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b] ${isRecording ? 'animate-pulse' : ''}`}
              disabled={isLoading || isPlaying}
            >
              <Mic size={24} />
            </button>
            <button
              type="submit"
              className="bg-[#07575b] text-[#c0dee5] p-3 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b]"
              disabled={isLoading || isRecording || input === null || input.trim() === ''}
            >
              <Send size={24} />
            </button>
          </div>
          {processingStatus && (
            <div className="text-center text-[#c0dee5] mt-2">{processingStatus}</div>
          )}
          {recordingStatus && (
            <div className="text-center text-[#c0dee5] mt-2">{recordingStatus}</div>
          )}
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
          {error && <div className="text-red-400 mt-2">{error}</div>}
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
        <button
          onClick={toggleAudio}
          className="flex items-center justify-center bg-[#07575b] text-[#c0dee5] p-2 rounded-lg transition-colors duration-200 hover:bg-[#07575b] focus:outline-none focus:ring-2 focus:ring-[#07575b]"
          disabled={!audioSrc}
        >
          <Speech size={20} className="mr-2" /> {isPlaying ? 'Stop Audio' : 'Read Aloud'}
        </button>
      </footer>
      <audio ref={audioRef} src={audioSrc} />
    </div>
  );
};

export default App;