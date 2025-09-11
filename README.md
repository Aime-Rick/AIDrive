# AIDrive 🚀

**Multimodal & Multilingual RAG-powered Document Intelligence Platform**

AIDrive is a cutting-edge document intelligence platform that leverages Google Drive integration and advanced RAG (Retrieval-Augmented Generation) technology to provide seamless querying across multiple file formats and languages. With support for **100+ languages** and a focus on 30 major languages (including English, Spanish, Chinese, Arabic, French, German, Hindi, Japanese, Portuguese, Russian, and more), AIDrive transforms how you interact with your digital documents.

## ✨ Key Features

### 🌍 **Multimodal Document Support**
- **Documents**: files with intelligent text extraction
- **Images**: with visual content analysis
- **Audio**: with speech-to-text transcription
- **Video**: with audio extraction and frame analysis

### 🗣️ **Multilingual Intelligence**
- **100+ Languages Supported**: Query and process documents in virtually any language
- **Focus on 30 Major Languages**: Optimized performance for English, Spanish, Chinese (Simplified & Traditional), Arabic, French, German, Hindi, Japanese, Portuguese, Russian, Italian, Korean, Dutch, Turkish, and more
- **Cross-Language Queries**: Ask questions in one language about documents in another
- **Advanced NLP**: Powered by Google's Gemini 2.5 Flash for superior multilingual understanding

### 🔄 **Intelligent RAG Pipeline**
- **Vector Database**: Supabase-powered vector storage with semantic search
- **Smart Chunking**: Optimized text segmentation for better retrieval
- **Multimodal Embeddings**: Jina CLIP v2 for unified text and image understanding
- **Context-Aware Responses**: Grounded answers with source attribution

### ☁️ **Seamless Google Drive Integration**
- **OAuth2 Authentication**: Secure Google Drive connection
- **Real-time Synchronization**: Automatic document processing upon upload
- **Folder Management**: Organize and query documents by folder structure
- **Batch Processing**: Bulk document processing for large collections

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                         │
│              (React/Next.js)                        │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                FastAPI Backend                      │
│  ┌─────────────┬──────────────┬─────────────────┐  │
│  │   Auth      │    Drive     │      RAG        │  │
│  │   System    │   Manager    │    Engine       │  │
│  └─────────────┴──────────────┴─────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              External Services                      │
│  ┌─────────────┬──────────────┬─────────────────┐  │
│  │  Google     │   Supabase   │    Google       │  │
│  │  Drive API  │   Vector DB  │   Gemini AI     │  │
│  └─────────────┴──────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 📚 API Endpoints

### Authentication & User Management
- `POST /users/signup` - Create new user account
- `POST /users/signin` - Authenticate user
- `POST /users/signout` - Sign out user
- `GET /users/me` - Get current user info
- `DELETE /users/{user_id}` - Delete user account

### Google Drive Integration
- `GET /authorize` - Initiate Google Drive OAuth flow
- `GET /oauth2callback` - Handle OAuth callback
- `GET /drive/connection-status` - Check Drive connection status
- `DELETE /drive/disconnect` - Disconnect Google Drive
- `POST /drive/upload` - Upload file to Drive
- `GET /drive/files` - List Drive files
- `POST /drive/folder` - Create Drive folder
- `POST /drive/download` - Download and process file

### Vector Database Management
- `GET /vector-db/status` - Check database initialization status
- `POST /vector-db/initialize` - Initialize database with all files
- `POST /vector-db/populate` - Populate database with specific files

### RAG Query Interface
- `POST /rag/query` - Query documents using natural language

### Health & Monitoring
- `GET /health` - API health check

## 🎯 Usage Examples

### Querying Documents
```python
# Query in English about multilingual documents
{
  "query": "What are the key findings in the research papers?",
  "top_k": 5
}

# Query in Spanish
{
  "query": "¿Cuáles son los principales hallazgos en los documentos?",
  "top_k": 3
}

# Query in Chinese
{
  "query": "这些文档中的主要发现是什么？",
  "top_k": 5
}
```

### Multimodal Queries
```python
# Query combining text and image analysis
{
  "query": "Analyze the charts and explain the trends shown in the financial reports",
  "top_k": 7
}

# Audio content queries
{
  "query": "Summarize the key points discussed in the meeting recordings",
  "top_k": 5
}
```

## 🔧 Configuration

### Supported File Types
- **Documents**: `.pdf`, `.docx`, `.txt`
- **Images**: `.png`, `.jpg`, `.jpeg`
- **Audio**: `.mp3`, `.wav`, `.flac`, `.aac`
- **Video**: `.mp4`, `.mov`, `.avi`, `.mkv`

### Language Support
AIDrive supports 100+ languages with optimized performance for:
- **European**: English, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Polish, Swedish, Norwegian, Danish, Finnish
- **Asian**: Chinese (Simplified & Traditional), Japanese, Korean, Hindi, Arabic, Thai, Vietnamese, Indonesian, Malay
- **Others**: Turkish, Hebrew, Greek, Czech, Hungarian, Romanian, Bulgarian, Croatian, Slovak, Ukrainian

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: Supabase (PostgreSQL with pgvector)
- **AI/ML**: Google Gemini 2.5 Flash, Jina CLIP v2
- **Storage**: Google Drive API
- **Authentication**: OAuth2, Supabase Auth
- **Audio Processing**: SpeechRecognition, PyDub, LibROSA
- **Video Processing**: MoviePy
- **Document Processing**: PyPDF2, docx2txt, LangChain

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙋‍♂️ Support

For support, please:
- Open an issue on GitHub
- Contact: [lotsuaimerick@gmail.com](mailto:lotsuaimerickgmail.com)

## 🌟 Acknowledgments

- Google Drive API for seamless cloud integration
- Supabase for powerful vector database capabilities
- Google Gemini for advanced multilingual AI
- Jina AI for multimodal embeddings
- The open-source community for amazing libraries

---

**Built by [Aime-Rick](https://github.com/Aime-Rick)**