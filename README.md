# Resume Analyzer

A Flask web application that analyzes resumes against a target career role. Users upload a PDF or DOCX resume (or paste the text), specify a target role, and receive AI-generated feedback covering current skills, skill gaps, a learning roadmap, and tailored interview questions. Past analyses are saved to each user's account for later review.

## Features

- **Resume ingestion**: Accepts `.pdf` and `.docx` uploads, or pasted resume text as a fallback
- **AI-powered analysis**: Identifies relevant skills, missing skills, and a phased learning roadmap for the target role
- **Interview preparation**: Generates technical and behavioral interview questions with answering tips
- **User accounts**: Signup and login with hashed passwords
- **Report history**: Every analysis is saved and can be revisited from the History page

## Tech Stack

- **Backend:** Python, Flask
- **AI:** Groq API (open-weight LLMs, with fallback across several models)
- **Database:** MySQL via SQLAlchemy and PyMySQL
- **Document parsing:** PyPDF2, python-docx
- **Frontend:** Jinja2 templates with HTML/CSS in `static/` and `templates/`

## Project Structure

```
Resume_Analyzer/
├── app.py            # Flask routes: auth, dashboard, history, password reset
├── ai.py             # Groq client and resume analysis logic
├── db.py             # SQLAlchemy engine and session setup
├── models.py         # User and Reports ORM models
├── requirements.txt  # Python dependencies
├── templates/        # Jinja2 HTML templates
└── static/           # CSS and client-side assets
```

## Previews 

![Image 1](Assets/image_1.png)
![Image 2](Assets/image_2.png)

## Prerequisites

- Python 3.9 or higher
- MySQL server
- A Groq API key ([console.groq.com](https://console.groq.com))

## Installation

1. **Clone the repository**

```bash
   git clone https://github.com/satviklandge/Resume_Analyzer.git
   cd Resume_Analyzer
```

2. **Create and activate a virtual environment**

```bash
   python -m venv venv
   source venv/bin/activate        # macOS/Linux
   venv\Scripts\activate           # Windows
```

3. **Install dependencies**

```bash
   pip install -r requirements.txt
```

4. **Configure environment variables**

   Create a `.env` file in the project root:

```env
   SECRET_KEY=your-long-random-secret-key
   GROQ_API_KEY=your-groq-api-key
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/resume_analyzer
```

   > Adjust `DATABASE_URL` to match the variable name used in `db.py`.

5. **Create the database**

```sql
   CREATE DATABASE resume_analyzer;
```

   Tables are created automatically on first run.

## Usage

Start the development server:

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

1. Sign up for an account and log in.
2. On the dashboard, enter your target role (for example, "Data Analyst").
3. Upload your resume as a PDF or DOCX, or paste its text.
4. Submit to receive your analysis.
5. Visit **History** to review previous reports.

## Routes

| Route              | Methods    | Description                                   |
| ------------------ | ---------- | --------------------------------------------- |
| `/`                | GET        | Redirects to dashboard or login               |
| `/signup`          | GET, POST  | Create a new account                          |
| `/login`           | GET, POST  | Authenticate and start a session              |
| `/dashboard`       | GET, POST  | Submit a resume for analysis                  |
| `/history`         | GET        | View saved analysis reports                   |
| `/forgot-password` | GET, POST  | Password reset request (see note below)       |
| `/logout`          | GET        | End the session                               |

## Notes

- **Password reset:** The `/forgot-password` page validates the email address and displays a confirmation message, but does not yet send an email. Email delivery is a planned improvement.
- **Analysis output:** The model is instructed to return strict JSON, which the app parses into skills, missing skills, roadmap phases, interview questions, and overall feedback.
- **Resume text:** Only the extracted text is stored, not the original file.

## Roadmap

- [ ] Send real password reset emails
- [ ] Export analysis reports as PDF
- [ ] Support additional file formats
- [ ] Compare multiple resumes against the same role

## License

Specify a license here (for example, MIT).

## Author

**Chhayank Landge**
GitHub: [@satviklandge](https://github.com/satviklandge)
