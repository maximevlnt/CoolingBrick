# Perforated Clay Brick for Air Cooling through Evaporation

This project involves the characterization and test bench setup of a perforated clay brick designed to cool air by evaporating moisture. The goal is to test and analyze the performance of the brick under different conditions.

## Prerequisites

Before you start, ensure you have the following installed on your machine:

- [Python](https://www.python.org/downloads/) (recommended version: 3.x)
- [pip](https://pip.pypa.io/en/stable/), the Python package manager
- [virtualenv](https://virtualenv.pypa.io/en/latest/) (optional but recommended for creating virtual environments)

## Installation

### 1. Unzip the Project

Download and unzip the project folder to your local machine.

### 2. Create and Activate a Virtual Environment

Open a terminal and navigate to the unzipped project folder. Then, run the following commands based on your operating system:

#### On Windows:

```bash
python -m venv venv
.\venv\Scripts\activate
```

#### On MAC/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```
### 3. Add QT Platform Variable (Optional for Specific Environments)
If you are working with a graphical user interface (GUI) library that requires Qt (e.g., PyQt or PySide) and encounter issues related to the display.
Follow these steps :

#### MAC/Linux

Open the activiation script
```bash
nano venv/bin/activate
```
Add the following line at the end of the file
```bash
export QT_QPA_PLATFORM=xcb
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
### 5. Running the Code
```bash
python main.py
```

## Usage 

Describe here how to use the project in more detail, including any configuration options, input data required, or expected outputs.

## Contributing

If you'd like to contribute to this project, please fork the repository, make your changes, and submit a pull request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.



