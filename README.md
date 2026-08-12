# 💪 VitaCoach AI

AI-powered fitness assistant built with **LangChain, OpenAI GPT-4o-mini and Streamlit**.

VitaCoach AI provides personalized fitness recommendations through a conversational interface, using user profile context and specialized tools for controlled calculations and exercise lookup.

## ✨ Features

- 💬 Conversational fitness assistant
- 👤 User profile and session context
- ⚖️ BMI calculation
- 🔥 Daily calorie / TDEE calculation based on activity level
- 🏋️ Exercise lookup from a controlled exercise database
- 🧠 Natural-language extraction of user parameters
- 🔧 LangChain agent with specialized tool routing
- ❓ Clarification of missing user data
- 🛡️ Basic safety handling for health-related requests

## 🏗️ Architecture

```text
User
  ↓
Streamlit UI
  ↓
LangChain Agent + GPT-4o-mini
  ↓
Context / Tool Selection
  ↓
┌─────────────┬──────────────┬───────────────┬───────────────┐
│ BMI Tool    │ Calorie Tool │ Exercise Tool │ Profile Tool  │
└─────────────┴──────────────┴───────────────┴───────────────┘
  ↓
Personalized Response
```

The LLM coordinates the interaction and selects the appropriate tool, while deterministic calculations and controlled exercise lookup are handled by specialized tools.

## 🧩 Current Prototype Scope

The prototype supports:

- profile creation from natural-language input;
- recognition of basic activity levels;
- BMI and calorie calculations using stored profile data;
- calorie recalculation when activity level changes;
- exercise search by muscle group and training environment;
- conversation context within the current Streamlit session.

The exercise database is currently limited and stored directly in the application code.

A future improvement is to move exercise content to a managed external database with an administration interface, allowing a fitness expert or content operator to add, edit, disable and approve exercises without changing application code.

## 🛠️ Technologies

- Python
- LangChain
- OpenAI GPT-4o-mini
- Streamlit

## 🚀 Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the Streamlit application:

```bash
streamlit run app.py
```

## ⚠️ Current Limitations

VitaCoach AI is an **educational prototype** and is not intended to replace professional medical, nutritional or fitness advice.

Current limitations include:

- limited exercise database;
- session-based rather than persistent user profiles;
- dependency on natural-language recognition and correct tool routing;
- basic safety rules that require stronger validation for production use;
- no persistent secure storage for user data;
- no production monitoring or automated evaluation yet.

## 🗺️ Next Steps

Key improvements required for further development:

### P0 — Safety & Reliability

- pre-agent safety validation;
- stronger recommendation guardrails;
- input validation;
- error handling and monitoring.

### P1 — Quality & Data

- persistent user profiles;
- secure data storage and access control;
- managed Exercise DB with content administration;
- automated evaluation and regression testing;
- logging and observability.

### P2 — Scale

- authentication and user accounts;
- performance and load testing;
- token and cost monitoring;
- expansion of the controlled exercise database;
- deployment and CI/CD improvements.

## 🎯 Product Direction

The next product improvement is a **managed Exercise DB**.

Instead of storing a limited set of exercises directly in application code, exercise content should be maintained through an Admin UI by a fitness expert or content operator.

Target outcomes:

- **≥95% coverage** of supported exercise test scenarios;
- **100% controlled content** for specific exercise recommendations;
- exercise content updates **without code changes or application redeployment**.

## 💡 Key Learning

Building VitaCoach AI demonstrated that the quality of an AI product depends not only on the language model itself, but on the system of controls around it.

**A good AI product is not just a good model — it is a controlled system around the model.**

Context management, tool routing, deterministic tools, validation and iterative testing are essential for making AI responses more predictable, reliable and safe.
