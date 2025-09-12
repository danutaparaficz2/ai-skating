# Data on Ice - ISU Archive Transformation

A cutting-edge AI-powered platform that transforms International Skating Union (ISU) archive data into engaging narratives for fans, media, and stakeholders. Built using Alibaba Cloud technologies including Qwen LLM, AnalyticDB, OpenSearch, and PAI-EAS.

## 🚀 Features

- **AI-Powered Story Generation**: Create personalized narratives using Alibaba Qwen LLM
- **Advanced Search**: Find content across skater bios, competition results, and videos using OpenSearch
- **Predictive Analytics**: Generate performance predictions based on historical data
- **Data Mining**: Extract insights from structured and unstructured ISU archive data
- **Multi-Audience Content**: Tailor stories for general fans, media professionals, and skating experts
- **Real-time Processing**: Handle live competition data and updates

## 🏗️ Architecture

The platform is built using modern microservices architecture:

- **Data Ingestion**: Automated pipeline for ISU archive data (bios, videos, results)
- **AI Processing**: Qwen LLM integration for natural language generation
- **Search Engine**: OpenSearch for fast, accurate content discovery  
- **Analytics**: AnalyticDB for structured data storage and analysis
- **API Layer**: FastAPI for RESTful services
- **Web Interface**: Modern responsive frontend

## 🛠️ Technology Stack

### Alibaba Cloud Services
- **Qwen LLM**: Advanced language model for story generation
- **AnalyticDB**: High-performance analytical database
- **OpenSearch**: Elasticsearch-compatible search engine
- **PAI-EAS**: Elastic Algorithm Service for ML model deployment
- **ECS-GPU**: GPU-enabled compute instances

### Framework & Libraries
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **Transformers**: Hugging Face library for NLP
- **OpenSearch-py**: Python client for OpenSearch
- **Pydantic**: Data validation and settings

## 📦 Installation

### Prerequisites
- Python 3.8+
- Access to Alibaba Cloud services
- OpenSearch cluster
- AnalyticDB instance

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/danutaparaficz2/ai-skating.git
   cd ai-skating
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Alibaba Cloud credentials and service endpoints
   ```

4. **Generate sample data**
   ```bash
   python -c "from src.utils import generate_sample_data; generate_sample_data()"
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## 🔧 Configuration

Edit the `.env` file with your service configurations:

```env
# Alibaba Cloud Configuration
ALIBABA_ACCESS_KEY_ID=your_access_key_id
ALIBABA_ACCESS_KEY_SECRET=your_access_key_secret

# Qwen LLM Configuration  
QWEN_API_KEY=your_qwen_api_key
QWEN_MODEL_NAME=qwen-turbo

# AnalyticDB Configuration
ANALYTICDB_HOST=your_analyticdb_host
ANALYTICDB_USER=your_username
ANALYTICDB_PASSWORD=your_password

# OpenSearch Configuration
OPENSEARCH_HOST=your_opensearch_host
OPENSEARCH_USERNAME=your_username
OPENSEARCH_PASSWORD=your_password
```

## 🚀 Usage

### Web Interface
Visit `http://localhost:8000` to access the interactive web interface featuring:
- Content search across all data types
- AI story generation demos
- Trending content discovery
- Personalized recommendations

### API Endpoints

#### Search
```bash
# Search all content
GET /search/?q=Nathan+Chen&discipline=singles

# Search specific content types
GET /search/skaters?q=Olympic+champion
GET /search/competitions?q=World+Championships&year=2023
```

#### Story Generation
```bash
# Generate skater profile
POST /stories/generate
{
  "skater_ids": [1],
  "story_type": "profile",
  "audience": "general"
}

# Generate competition recap
POST /stories/generate  
{
  "competition_ids": [1],
  "story_type": "competition_recap",
  "audience": "media"
}
```

#### Data Retrieval
```bash
# Get skaters
GET /skaters/?country=USA&discipline=singles

# Get competition results
GET /competitions/1/results

# Get recommendations
GET /recommendations/1?limit=5
```

## 📊 Data Schema

### Skater Data
- Personal information (name, country, birth date)
- Biographical content
- Achievement records
- Performance history

### Competition Data
- Event details (name, location, dates)
- Discipline and level information
- Results and rankings
- Video content

### Generated Stories
- AI-generated narratives
- Audience-specific content
- Performance predictions
- Trend analysis

## 🤖 AI Story Generation

The platform uses Alibaba Qwen LLM to generate three types of content:

1. **Skater Profiles**: Comprehensive biographical narratives
2. **Competition Recaps**: Event summaries and highlights  
3. **Performance Predictions**: Data-driven forecasting

Stories are tailored for different audiences:
- **General**: Accessible language for casual fans
- **Media**: Professional content for journalists
- **Fans**: Technical details for skating enthusiasts

## 🔍 Search Capabilities

OpenSearch powers advanced search features:
- **Full-text search** across all content types
- **Faceted filtering** by discipline, country, year
- **Semantic search** for related content discovery
- **Real-time indexing** of new data
- **Personalized recommendations** based on user interests

## 📈 Analytics & Insights

The platform provides data-driven insights:
- Performance trend analysis
- Competition outcome predictions
- Skater progression tracking
- Audience engagement metrics
- Content popularity trends

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t data-on-ice .

# Run container
docker run -p 8000:8000 --env-file .env data-on-ice
```

### Cloud Deployment
The application is optimized for deployment on Alibaba Cloud ECS instances with GPU support for enhanced AI processing performance.

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 📝 API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- International Skating Union (ISU) for providing the data archive
- Alibaba Cloud for AI and cloud infrastructure technologies
- The figure skating community for inspiration and support

## 📞 Support

For questions and support:
- Create an issue in this repository
- Contact the development team
- Check the documentation at `/docs`

---

**Data on Ice** - Transforming skating data into compelling stories with the power of AI.
