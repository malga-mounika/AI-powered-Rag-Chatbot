import { useEffect, useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  Trash2,
  Send,
  Bot,
  User,
  Sparkles,
  Copy,
  Check,
  BookOpen,
  Layers,
  Menu,
  X,
  RefreshCw,
  AlertCircle,
  MessageSquare,
  Paperclip
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  // Document state
  const [selectedFile, setSelectedFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [currentDocument, setCurrentDocument] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { text, type: 'info'|'success'|'error' }
  const [isDragOver, setIsDragOver] = useState(false);

  // Chat state
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // System & UI state
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState(true);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  // Load documents and check backend health on start
  useEffect(() => {
    checkHealth();
    loadDocuments();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      if (res.ok) {
        setBackendOnline(true);
      } else {
        setBackendOnline(false);
      }
    } catch {
      setBackendOnline(false);
    }
  };

  // Get document list from backend
  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/documents`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to load documents");
      }

      setDocuments(data.documents || []);

      // Auto-select latest document if none selected
      if (data.documents && data.documents.length > 0) {
        setCurrentDocument((prev) => {
          if (!prev) return data.documents[data.documents.length - 1];
          // Keep current if still exists
          const exists = data.documents.find((d) => d.filename === prev.filename);
          return exists || data.documents[data.documents.length - 1];
        });
      } else {
        setCurrentDocument(null);
      }
    } catch (error) {
      console.error("Document loading error:", error);
    }
  };

  // Handle PDF file picking
  const processSelectedFile = (file) => {
    if (!file) return;

    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      setUploadStatus({
        text: "Please select a valid PDF document.",
        type: "error",
      });
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setUploadStatus({
      text: `Selected: ${file.name}`,
      type: "info",
    });
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    processSelectedFile(file);
  };

  // Drag & drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  // Upload PDF to backend
  const handleUpload = async (fileToUpload = selectedFile) => {
    if (!fileToUpload) {
      setUploadStatus({
        text: "Please select or drop a PDF file first.",
        type: "error",
      });
      return;
    }

    setUploading(true);
    setUploadStatus({
      text: "Parsing PDF and generating embeddings...",
      type: "info",
    });

    const formData = new FormData();
    formData.append("file", fileToUpload);

    try {
      const response = await fetch(`${API_URL}/store-document`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to process document");
      }

      setCurrentDocument({
        filename: data.filename,
        chunks: data.total_chunks,
      });

      setUploadStatus({
        text: `✅ ${data.filename} indexed (${data.total_chunks} chunks).`,
        type: "success",
      });

      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      await loadDocuments();
      setMessages([]);
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus({
        text: `❌ ${error.message || "Upload failed."}`,
        type: "error",
      });
    } finally {
      setUploading(false);
    }
  };

  // Switch active document
  const handleSelectDocument = (doc) => {
    setCurrentDocument(doc);
    setMessages([]);
    setUploadStatus({
      text: `Switched to ${doc.filename}`,
      type: "info",
    });
    setMobileSidebarOpen(false);
  };

  // Delete single document
  const handleDeleteDocument = async (docToDelete, e) => {
    e.stopPropagation();
    if (!docToDelete) return;

    const confirmed = window.confirm(`Delete document "${docToDelete.filename}"?`);
    if (!confirmed) return;

    try {
      const response = await fetch(
        `${API_URL}/documents/${encodeURIComponent(docToDelete.filename)}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to delete document");
      }

      setUploadStatus({
        text: `Deleted ${docToDelete.filename}`,
        type: "info",
      });

      setMessages([]);
      await loadDocuments();
    } catch (error) {
      console.error("Delete error:", error);
      setUploadStatus({
        text: `❌ ${error.message}`,
        type: "error",
      });
    }
  };

  // Clear all documents
  const handleClearDocuments = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete ALL uploaded documents?"
    );
    if (!confirmed) return;

    try {
      const response = await fetch(`${API_URL}/documents`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to clear documents");
      }

      setDocuments([]);
      setCurrentDocument(null);
      setMessages([]);
      setUploadStatus({
        text: "All documents cleared.",
        type: "info",
      });
    } catch (error) {
      console.error("Clear documents error:", error);
      setUploadStatus({
        text: `❌ ${error.message}`,
        type: "error",
      });
    }
  };

  // Send question to RAG backend
  const handleSend = async (customPrompt) => {
    const queryText = (customPrompt || question).trim();

    if (!queryText) return;

    if (!currentDocument) {
      const userMessage = { role: "user", text: queryText };
      const errorMessage = {
        role: "bot",
        text: "Please upload a PDF document first so I can retrieve relevant knowledge.",
      };
      setMessages((prev) => [...prev, userMessage, errorMessage]);
      setQuestion("");
      return;
    }

    const userMessage = { role: "user", text: queryText };
    const updatedHistory = [...messages, userMessage];

    setMessages(updatedHistory);
    setQuestion("");
    setSending(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: queryText,
          filename: currentDocument.filename,
          history: messages.map((m) => ({
            role: m.role === "bot" ? "assistant" : "user",
            content: m.text,
          })),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to receive response from AI");
      }

      const botMessage = {
        role: "bot",
        text: data.answer,
        sources: data.sources || [],
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "❌ Unable to fetch an answer. Please check if the FastAPI backend is running.",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="app-layout">
      {/* =================================================================== */}
      {/* Sidebar Navigation */}
      {/* =================================================================== */}
      <aside className={`sidebar ${mobileSidebarOpen ? "open" : ""}`}>
        {/* Sidebar Header */}
        <div className="sidebar-header">
          <div className="brand-icon">
            <Sparkles size={22} />
          </div>
          <div className="brand-info">
            <h1>RAG Brain</h1>
            <p>AI Knowledge Hub</p>
          </div>
        </div>

        {/* Sidebar Body */}
        <div className="sidebar-body">
          {/* Upload Dropzone */}
          <div>
            <div className="sidebar-section-title">
              <span>Upload Document</span>
              <FileText size={14} />
            </div>

            <div
              className={`dropzone ${isDragOver ? "active-drag" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                id="pdfInput"
                type="file"
                accept=".pdf,application/pdf"
                className="file-input-hidden"
                onChange={handleFileChange}
              />
              <div className="dropzone-icon">
                <UploadCloud size={22} />
              </div>
              <div className="dropzone-text">
                <p>{selectedFile ? selectedFile.name : "Click or drag PDF file"}</p>
                <span>Supports PDF documents up to 50MB</span>
              </div>
            </div>

            {selectedFile && !uploading && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleUpload();
                }}
                className="send-btn"
                style={{
                  width: "100%",
                  borderRadius: "var(--radius-md)",
                  height: "38px",
                  marginTop: "0.75rem",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                }}
              >
                Index & Upload PDF
              </button>
            )}

            {uploading && (
              <div className="upload-progress-bar">
                <div className="upload-progress-fill" />
              </div>
            )}

            {uploadStatus && (
              <div className={`status-toast ${uploadStatus.type}`}>
                {uploadStatus.type === "error" ? (
                  <AlertCircle size={14} />
                ) : (
                  <FileText size={14} />
                )}
                <span>{uploadStatus.text}</span>
              </div>
            )}
          </div>

          {/* Document Library */}
          <div>
            <div className="sidebar-section-title">
              <span>Knowledge Base ({documents.length})</span>
              {documents.length > 0 && (
                <button
                  className="clear-all-btn"
                  onClick={handleClearDocuments}
                  title="Clear all documents"
                >
                  Clear All
                </button>
              )}
            </div>

            {documents.length === 0 ? (
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "var(--text-muted)",
                  textAlign: "center",
                  padding: "1.5rem 0",
                }}
              >
                No documents indexed yet.
              </div>
            ) : (
              <div className="doc-list">
                {documents.map((doc) => {
                  const isActive = currentDocument?.filename === doc.filename;
                  return (
                    <div
                      key={doc.filename}
                      className={`doc-card ${isActive ? "active" : ""}`}
                      onClick={() => handleSelectDocument(doc)}
                    >
                      <div className="doc-info">
                        <FileText size={18} className="doc-icon" />
                        <div className="doc-details">
                          <span className="doc-name">{doc.filename}</span>
                          <span className="doc-meta">
                            {doc.chunks} chunks {isActive ? "• Active" : ""}
                          </span>
                        </div>
                      </div>
                      <div className="doc-actions">
                        <button
                          className="icon-btn"
                          onClick={(e) => handleDeleteDocument(doc, e)}
                          title="Delete PDF"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <div className="status-badge">
            <span className={`status-dot ${backendOnline ? "" : "offline"}`} />
            <span>FastAPI RAG: {backendOnline ? "Online" : "Offline"}</span>
          </div>
          <button
            className="icon-btn"
            onClick={() => {
              checkHealth();
              loadDocuments();
            }}
            title="Refresh documents"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </aside>

      {/* =================================================================== */}
      {/* Main Workspace */}
      {/* =================================================================== */}
      <main className="main-content">
        {/* Top Header Bar */}
        <header className="top-bar">
          <button
            className="icon-btn mobile-toggle"
            onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          >
            {mobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div className="top-bar-active-doc">
            <span className="active-doc-dot" />
            <span style={{ color: "var(--text-secondary)" }}>
              {currentDocument
                ? `Active Context: ${currentDocument.filename}`
                : "No document selected"}
            </span>
          </div>

          {messages.length > 0 && (
            <button className="clear-chat-btn" onClick={() => setMessages([])}>
              <RefreshCw size={14} />
              Clear Chat
            </button>
          )}
        </header>

        {/* Chat Stream */}
        <div className="chat-stream">
          <div className="chat-inner-width">
            {messages.length === 0 && (
              <div className="welcome-hero">
                <div className="welcome-logo">
                  <Sparkles size={32} />
                </div>
                <h2>RAG Brain Workspace</h2>
                <p>
                  {currentDocument
                    ? `Ready to query "${currentDocument.filename}". Ask questions or summarize key sections.`
                    : "Upload a PDF document to begin intelligent semantic Q&A."}
                </p>

                {currentDocument && (
                  <div className="prompt-suggestions">
                    <div
                      className="prompt-card"
                      onClick={() =>
                        handleSend("Summarize the key points of this document.")
                      }
                    >
                      <span className="prompt-card-title">
                        <BookOpen size={16} color="#818cf8" />
                        Executive Summary
                      </span>
                      <span className="prompt-card-sub">
                        Get an overview of the main topics & arguments
                      </span>
                    </div>

                    <div
                      className="prompt-card"
                      onClick={() =>
                        handleSend(
                          "List the most important concepts and definitions mentioned."
                        )
                      }
                    >
                      <span className="prompt-card-title">
                        <Layers size={16} color="#a855f7" />
                        Key Concepts
                      </span>
                      <span className="prompt-card-sub">
                        Extract core definitions & terminology
                      </span>
                    </div>

                    <div
                      className="prompt-card"
                      onClick={() =>
                        handleSend("What are the main conclusions or findings?")
                      }
                    >
                      <span className="prompt-card-title">
                        <MessageSquare size={16} color="#ec4899" />
                        Key Takeaways
                      </span>
                      <span className="prompt-card-sub">
                        Highlight actionable conclusions & insights
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {messages.map((msg, index) => (
              <div
                key={index}
                className={`msg-wrapper ${msg.role === "user" ? "user" : "bot"}`}
              >
                {msg.role === "bot" && (
                  <div className="msg-avatar bot">
                    <Bot size={20} />
                  </div>
                )}

                <div className="msg-bubble-container">
                  <div className="msg-header">
                    <span>{msg.role === "user" ? "You" : "Gemini AI"}</span>
                  </div>

                  <div className="msg-body">{msg.text}</div>

                  {/* Sources display */}
                  {msg.role === "bot" && msg.sources && msg.sources.length > 0 && (
                    <div className="sources-card">
                      <div className="sources-header">
                        <BookOpen size={14} />
                        <span>Sources Cited ({msg.sources.length} Chunks)</span>
                      </div>
                      <div className="sources-grid">
                        {msg.sources.map((src, sIdx) => (
                          <div key={sIdx} className="source-badge">
                            <FileText size={12} />
                            <span>
                              {src.filename} (Chunk #{src.chunk_index})
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Toolbar */}
                  {msg.role === "bot" && (
                    <div className="msg-toolbar">
                      <button
                        className="copy-btn"
                        onClick={() => copyToClipboard(msg.text, index)}
                      >
                        {copiedIndex === index ? (
                          <>
                            <Check size={14} color="#10b981" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy size={14} />
                            <span>Copy response</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="msg-avatar user">
                    <User size={20} />
                  </div>
                )}
              </div>
            ))}

            {sending && (
              <div className="msg-wrapper bot">
                <div className="msg-avatar bot">
                  <Bot size={20} />
                </div>
                <div className="msg-bubble-container">
                  <div className="msg-header">
                    <span>Gemini AI</span>
                  </div>
                  <div className="msg-body">
                    <div className="typing-loader">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-muted)",
                          marginLeft: "0.4rem",
                        }}
                      >
                        Searching document chunks & generating answer...
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Bottom Input Panel */}
        <div className="input-panel">
          <div className="input-box-container">
            <textarea
              className="input-textarea"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                currentDocument
                  ? `Ask a question about ${currentDocument.filename}...`
                  : "Upload a PDF from the sidebar to ask questions..."
              }
              rows={2}
            />

            <div className="input-toolbar">
              <div className="input-actions-left">
                <button
                  className="attach-btn"
                  onClick={() => fileInputRef.current?.click()}
                  title="Upload PDF"
                >
                  <Paperclip size={14} />
                  <span>Attach PDF</span>
                </button>
              </div>

              <button
                className="send-btn"
                onClick={() => handleSend()}
                disabled={!question.trim() || sending || !currentDocument}
                title="Send Message"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
