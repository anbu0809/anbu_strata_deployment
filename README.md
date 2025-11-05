# AI Automated Data Migration Platform

A comprehensive database migration platform that leverages AI to automatically analyze, extract, migrate, and validate data across different database systems.

## 🚀 Features

- **Intelligent Schema Analysis**: AI-powered database schema analysis and comparison
- **Cross-Platform Migration**: Support for MySQL, PostgreSQL, SQLite, and more
- **Automated Extraction**: Smart data extraction with progress tracking
- **Schema Translation**: AI-powered DDL translation between database types
- **Data Migration**: Efficient bulk data transfer with validation
- **Real-time Monitoring**: Live progress tracking and status updates
- **Reconciliation**: Comprehensive data validation and comparison
- **Modern UI**: React-based dashboard with responsive design

## 🏗️ Architecture

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: React Hooks
- **UI Components**: Custom components with modern design

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (development), PostgreSQL (production ready)
- **AI Integration**: OpenAI GPT for schema translation
- **API**: RESTful API with automatic documentation
- **Real-time Updates**: Polling-based status updates

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Git

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/anbu0809/mig_strata_ai.git
cd mig_strata_ai
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Initialize database
python init_db.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Option 1: Quick Start (Recommended)
```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

### Option 2: Manual Startup
**Terminal 1 - Backend:**
```bash
cd c:/Users/Localuser/Desktop/final strata
venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 3: Production Build
```bash
# Build frontend
cd frontend
npm run build

# Start production backend
cd ..
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --host 0.0.0.0 --port 8000
```

## 🌐 Application Access

- **Frontend Dashboard**: http://localhost:5173/
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 📊 Migration Workflow

1. **Connect Sources**: Configure source and target database connections
2. **Analyze**: AI-powered schema analysis and comparison
3. **Extract**: Smart data extraction with progress tracking
4. **Migrate**: 
   - **Structure Migration**: AI-powered DDL translation and table creation
   - **Data Migration**: Bulk data transfer with validation
5. **Reconcile**: Comprehensive data validation and comparison

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=sqlite:///./strata.db
API_SECRET_KEY=your-secret-key-here
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
OPENAI_API_KEY=your-openai-api-key
```

### Database Configuration
The application supports multiple database types:
- **MySQL**: Configure connection parameters in the UI
- **PostgreSQL**: Set up connection details
- **SQLite**: File-based database support
- **Others**: Extensible architecture for additional databases

## 🧪 Testing

```bash
# Backend tests
python -m pytest backend/tests/

# Frontend tests
cd frontend
npm run test

# Integration tests
python test_core_functionality.py
python test_live_connection.py
```

## 📁 Project Structure

```
mig_strata_ai/
├── backend/                 # FastAPI backend
│   ├── routes/             # API routes
│   ├── models.py           # Database models
│   ├── database.py         # Database configuration
│   ├── ai.py              # AI integration
│   └── main.py            # Application entry point
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/        # Page components
│   │   ├── types.ts      # TypeScript definitions
│   │   └── main.tsx      # Application entry point
│   ├── package.json      # Dependencies and scripts
│   └── vite.config.ts    # Vite configuration
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore           # Git ignore rules
└── start.sh/.bat        # Startup scripts
```

## 🔒 Security Features

- Input validation and sanitization
- Secure database connections with SSL/TLS support
- Environment-based configuration
- CORS protection
- Rate limiting (production ready)
- SQL injection prevention

## 🚀 Deployment

### Docker Deployment
```dockerfile
# Dockerfile included for containerized deployment
docker build -t mig-strata-ai .
docker run -p 8000:8000 -p 5173:5173 mig-strata-ai
```

### Cloud Deployment Ready
- Environment configuration for production
- Database connection pooling
- Load balancing support
- Monitoring and logging integration
- CI/CD pipeline ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛟 Support

For support, please open an issue on GitHub or contact the development team.

## 🎯 Roadmap

- [ ] Real-time WebSocket support
- [ ] Advanced conflict resolution
- [ ] Incremental migration support
- [ ] Cloud database integration
- [ ] Advanced monitoring dashboard
- [ ] Multi-tenant support
- [ ] API rate limiting
- [ ] Advanced user authentication

## 🏷️ Version History

- **v1.0.0**: Initial release with core migration features
- **v1.1.0**: Added AI-powered schema translation
- **v1.2.0**: Enhanced UI with real-time progress tracking
- **v1.3.0**: Production deployment optimizations

---

**Built with ❤️ by DecisionMinds**

*Powered by AI for seamless database migration*