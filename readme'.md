# 11v11 AI Football Simulation

A simple 3D football (soccer) simulation built in Python using **PyOpenGL** and **GLUT**.  
This project models a basic AI-driven 11v11 match with one user-controlled player.

---

## Features

- **User Control:** Move a single player using `WASD` and kick with `SPACE`.
- **AI Players:** Teams are filled with AI agents for goalies, defenders, midfielders, and attackers.  
- **Basic Physics:** Ball movement with friction, collision avoidance, and simple goal detection.  
- **Game Flow:** Includes first half, halftime switch, second half, and game timer.  
- **Scoreboard & Controls Display:** Shows score, remaining time, and player controls.  
- **3D Field & Models:** Minimalistic rendering of field, players, and goals.

---

## Controls

| Key   | Action         |
|-------|----------------|
| W     | Move forward   |
| A     | Move left      |
| S     | Move backward  |
| D     | Move right     |
| SPACE | Kick ball      |

---

## Installation

1. **Clone the repository:**

```bash
git clone <repo-url>
cd <repo-folder>
```

2. **Install dependencies:**

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

3. **Run the simulation:**

```bash
python main.py
```

---

## How It Works

- **Agents:** Each player has a role (`goalie`, `def`, `mid`, `att`) and AI logic for chasing the ball and avoiding collisions.
- **User Player:** One attacker is user-controlled. Movement and kicking are responsive but limited to the field boundaries.
- **Ball Mechanics:** Simple 2D physics on the X-Z plane, including friction and bounce off field boundaries.
- **AI Decision Logic:**  
  - Top 3 closest teammates can chase the ball.  
  - Goalies rarely leave the goal area.  
  - Randomized aggression and speed give variation.

---

## Credits

- **Developed by:**  
  - D - 1DT23CS048  
  - A - 1DT23CS048  
  - A - 1DT23CS048  
  - S - 1DT23CS048  

- **Technologies Used:** Python, PyOpenGL, GLUT  

- **Disclaimer:** This is a learning project and not intended as a professional-grade football simulation.  

---

## Screenshots

*(Add screenshots here if desired)*