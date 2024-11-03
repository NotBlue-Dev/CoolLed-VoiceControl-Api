# Project Title

A brief description of your project, its purpose, and what it does.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Installation

To set up the project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the application, use the following command:

```bash
uvicorn src.server:app --reload
```

This will start the FastAPI server, and you can access the API at `http://127.0.0.1:8000`.

## API Endpoints

### Write Message

- **Endpoint:** `/write`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "value": "Your text here",
    "color": "Optional color"
  }
  ```

### Image Message

- **Endpoint:** `/image`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "value": "image_filename.png"
  }
  ```

### Animation Message

- **Endpoint:** `/anim`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "value": "animation_filename.gif"
  }
  ```

### Speed Control

- **Endpoint:** `/speed`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "value": 100
  }
  ```

### Mode Control

- **Endpoint:** `/mode`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "value": 1
  }
  ```

### Brightness Control

- **Endpoint:** `/brightness`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "value": 5
  }
  ```

### State Control

- **Endpoint:** `/state`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "value": "On"  // or "Off"
  }
  ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [CrimsonClyde](https://git.team23.org/CrimsonClyde) for his reverse engineering work on the CoolLED devices.