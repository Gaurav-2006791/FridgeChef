# Fridge Chef 🍳

Fridge Chef is an AI-powered recipe generator that transforms the ingredients you already have into delicious and practical meals. The application uses a FastAPI backend, a modern responsive frontend, and OpenAI's GPT model to generate personalized recipes.

---

## Features

- 🍽️ AI-powered recipe generation
- 🔐 User Authentication (Sign Up & Sign In)
- 🏠 Landing Page
- 📋 Dashboard
- 🥗 Nutrition Information
- 👨‍🍳 Chef Tips
- 📱 Responsive UI
- ⚡ FastAPI Backend
- 🤖 OpenAI GPT Integration
- 🐳 Docker Support
- ☁️ AWS App Runner Ready

---

## Project Structure

```
FridgeChef/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│
├── frontend/
│   ├── landing.html
│   ├── signup.html
│   ├── auth.html
│   ├── dashboard.html
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── Dockerfile
├── README.md
└── .gitignore
```

---

## Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap 5

### Backend
- FastAPI
- Python
- Pydantic

### AI
- OpenAI GPT API

### Cloud
- Docker
- AWS App Runner

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Gaurav-2006791/FridgeChef.git
```

Go into the project:

```bash
cd FridgeChef
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Create a `.env` file inside the backend folder:

```env
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_MODEL=gpt-4o-mini
```

Run the backend:

```bash
uvicorn backend.main:app --reload
```

---

## API Endpoints

### Health Check

```
GET /health
```

### Generate Recipe

```
POST /generate
```

---

## Docker

Build the image:

```bash
docker build -t fridge-chef .
```

Run the container:

```bash
docker run -p 8000:8000 --env-file backend/.env fridge-chef
```

---

## Deployment

This application is designed to be deployed on **AWS App Runner** using Docker.

Deployment Steps:

1. Push the project to GitHub.
2. Connect GitHub to AWS App Runner.
3. Select the repository.
4. Configure Docker deployment.
5. Add environment variables:
   - OPENAI_API_KEY
   - OPENAI_MODEL
6. Deploy.
7. Access the public HTTPS URL.

---

## Future Enhancements

- Save Favorite Recipes
- Recipe History
- Shopping List
- Image-based Ingredient Recognition
- Voice Input
- Multi-language Support

---

## Author

**Gaurav Pandey**

GitHub: https://github.com/Gaurav-2006791

---

## License

This project is licensed under the MIT License.