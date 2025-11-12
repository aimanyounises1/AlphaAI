# AlphaAI - Local Multi-Agent RAG System

A powerful multi-agent RAG (Retrieval-Augmented Generation) system combining GraphRAG, AutoGen agents, and Ollama LLMs with an interactive Chainlit UI. Run everything locally and offline for complete privacy and control.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

![AlphaAI Overview](/images/image.png)

## 🌟 Features

- **🤖 Agentic RAG**: Integrates GraphRAG's knowledge search with AutoGen agents via function calling
- **💻 Offline LLM Support**: Uses local models from Ollama for both inference and embedding - completely free and private
- **🔌 Non-OpenAI Function Calling**: Extends AutoGen to support function calling with non-OpenAI LLMs via LiteLLM proxy
- **🎨 Interactive UI**: Chainlit interface for continuous conversations, multi-threading, and user input settings
- **📊 Knowledge Graphs**: Automatically builds and visualizes knowledge graphs from your data
- **🗄️ Supabase Integration**: Full-stack database and authentication with PostgreSQL
- **🐳 Docker Ready**: Complete Docker Compose setup for easy deployment
- **🔒 Privacy First**: All processing happens locally - your data never leaves your machine

## 🏗️ Architecture

AlphaAI combines several powerful technologies:

- **GraphRAG**: For knowledge graph generation and advanced RAG capabilities
- **AutoGen**: Multi-agent orchestration and conversation management
- **Ollama**: Local LLM inference (Mistral, Llama3, etc.)
- **LiteLLM**: Proxy server enabling function calling with local models
- **Chainlit**: Modern web UI for chat interactions
- **Supabase**: Self-hosted backend with PostgreSQL, Auth, and Real-time
- **Docker**: Containerized deployment for consistency

## 📋 Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Ollama installed locally
- 16GB+ RAM recommended
- CUDA-capable GPU (optional, for faster inference)

## 🚀 Quick Start

### 1. Install Ollama and Models

Visit [Ollama's website](https://ollama.com/) for installation instructions.

```bash
# Install and pull required models
ollama pull mistral-large
ollama pull llama3
ollama pull nomic-embed-text

# Start Ollama server
ollama serve
```

### 2. Clone and Setup Environment

```bash
git clone https://github.com/aimanyounises1/AlphaAI.git
cd AlphaAI

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Option A: Run with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f rag_agents

# Access the UI
open http://localhost:8002
```

### 4. Option B: Run Locally

```bash
# Create conda environment
conda create -n RAG_agents python=3.12
conda activate RAG_agents

# Install dependencies
pip install -r requirements.txt

# Initialize GraphRAG
mkdir -p ./input
python -m graphrag.index --init --root .
cp settings.yaml ./

# Create embeddings and knowledge graph
python -m graphrag.index --root .

# Start LiteLLM proxy (in separate terminal)
litellm --model ollama_chat/llama3

# Run the application
chainlit run appUI.py
```

## 📁 Project Structure

```
AlphaAI/
├── agents/              # AutoGen agent configurations
├── chat/                # Chat management and conversation handlers
├── database/            # Database connection and models
├── file_handlers/       # Document processing utilities
├── graph/               # Knowledge graph management
│   ├── graph_handler.py
│   ├── visualization.py
│   ├── communities.py
│   └── centrality.py
├── input/               # Input documents for processing
├── tasks/               # Task initialization and management
├── appUI.py             # Main Chainlit application
├── agents_creation.py   # Agent factory and configuration
├── config.py            # Application configuration
├── settings.yaml        # GraphRAG settings
├── docker-compose.yml   # Docker orchestration
└── requirements.txt     # Python dependencies
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# GraphRAG
GRAPHRAG_API_KEY=your_api_key_here

# Ollama
OLLAMA_API_BASE=http://localhost:11434

# Supabase
SUPABASE_URL=http://kong:8000
POSTGRES_PASSWORD=your_secure_password

# Ports
STUDIO_PORT=3000
CHAINLIT_PORT=8002
LITELLM_PORT=8001
```

### GraphRAG Settings

Edit `settings.yaml` to configure:
- LLM model selection
- Embedding model
- Chunk sizes and overlap
- Community detection parameters
- Query types (local vs global)

## 🎯 Usage

### Basic Chat

1. Open http://localhost:8002 in your browser
2. Type your question or query
3. AlphaAI will:
   - Search the knowledge graph
   - Retrieve relevant context
   - Generate informed responses
   - Cite sources

### Adding Documents

```bash
# Add documents to the input folder
cp your_document.txt ./input/

# Rebuild the knowledge graph
python -m graphrag.index --root .
```

### Query Types

**Local Search**: For specific, targeted questions
```bash
# Finds specific facts and relationships
"What is the relationship between X and Y?"
```

**Global Search**: For broad, analytical questions
```bash
# Provides comprehensive overviews
"Summarize the main themes in the documents"
```

## 🧩 Components

### GraphRAG

Creates knowledge graphs from unstructured text:
- Entity extraction
- Relationship mapping
- Community detection
- Hierarchical clustering

### AutoGen Agents

Multi-agent system for:
- Task decomposition
- Collaborative problem-solving
- Function calling
- Response synthesis

### Chainlit UI

Modern chat interface featuring:
- Real-time streaming responses
- File uploads
- Conversation history
- User settings
- Message threading

## 🐳 Docker Services

The Docker Compose setup includes:

- **rag_agents**: Main application container
- **studio**: Supabase Studio UI
- **kong**: API gateway
- **auth**: GoTrue authentication
- **rest**: PostgREST API
- **realtime**: Real-time subscriptions
- **storage**: File storage service
- **db**: PostgreSQL database
- **vector**: pgvector for embeddings
- **analytics**: Logflare analytics

## 📊 Knowledge Graph Visualization

Access the knowledge graph visualization:

```bash
# Generate visualization
open graph.html
```

Features:
- Interactive node exploration
- Community highlighting
- Relationship filtering
- Centrality metrics
- Export capabilities

## 🔧 Advanced Configuration

### Custom Agents

Create custom agents in `agents_creation.py`:

```python
from autogen import AssistantAgent

custom_agent = AssistantAgent(
    name="MyAgent",
    system_message="Your agent's role",
    llm_config=llm_config
)
```

### Custom Tools

Add tools for agents to call:

```python
@tool
def my_custom_tool(query: str) -> str:
    """Tool description for the agent"""
    # Implementation
    return result
```

## 🔍 Troubleshooting

### Ollama Connection Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
pkill ollama && ollama serve
```

### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose up --build -d

# Check logs
docker-compose logs -f
```

### GraphRAG Indexing Errors

```bash
# Clear cache and reindex
rm -rf cache/
python -m graphrag.index --root . --verbose
```

### Memory Issues

For large documents, adjust `settings.yaml`:

```yaml
parallelization:
  num_threads: 4  # Reduce if needed

chunks:
  size: 256  # Reduce chunk size
```

## 📈 Performance Optimization

### GPU Acceleration

Enable GPU support in Ollama:

```bash
# NVIDIA GPUs
ollama serve --gpu

# Check GPU usage
nvidia-smi
```

### Model Selection

Choose models based on your hardware:

```yaml
# Fast, lower memory (settings.yaml)
llm:
  model: mistral:7b

# Better quality, more memory
llm:
  model: mistral-large:latest
```

### Caching

Enable caching for faster repeated queries:

```python
# In config.py
ENABLE_CACHE = True
CACHE_TTL = 3600
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [GraphRAG](https://github.com/microsoft/graphrag) by Microsoft
- [AutoGen](https://github.com/microsoft/autogen) by Microsoft
- [Ollama](https://ollama.ai) for local LLM inference
- [Chainlit](https://chainlit.io) for the amazing UI framework
- [Supabase](https://supabase.com) for the backend infrastructure
- [LiteLLM](https://github.com/BerriAI/litellm) for LLM proxy capabilities

## 📚 Further Reading

- [GraphRAG Documentation](https://microsoft.github.io/graphrag/)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Ollama Model Library](https://ollama.ai/library)
- [Chainlit Documentation](https://docs.chainlit.io/)

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search existing GitHub issues
3. Create a new issue with:
   - System information
   - Error logs
   - Steps to reproduce

## 🗺️ Roadmap

- [ ] Multi-modal support (images, PDFs)
- [ ] Advanced visualization options
- [ ] Custom embedding models
- [ ] Distributed processing
- [ ] API endpoint for external integrations
- [ ] Mobile-responsive UI
- [ ] Voice interaction support
- [ ] Multi-language support

---

**Built with ❤️ for the AI community**
