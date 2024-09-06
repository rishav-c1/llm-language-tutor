# Lang: Leveraging LLMs for Adaptive Real-time Multimodal Language Learning

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm 6+

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/rishav-c1/lang-spanish-learning.git
   cd lang-spanish-learning
   ```

2. Set up the backend:
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```
   cd ../frontend
   npm install
   ```

4. Create a `.env` file in the backend directory with the following contents:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
   GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_credentials_file
   ```

### Running the Application

1. Start the backend server:
   ```
   cd backend
   uvicorn main:app --reload
   ```

2. In a new terminal, start the frontend development server:
   ```
   cd frontend
   npm start
   ```

3. Open your browser and navigate to `http://localhost:3000` to use the application.
