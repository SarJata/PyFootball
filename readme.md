# PyFootball: 1v1 Arcade Football Simulation

**PyFootball** is a lightweight, 3D arcade-style football (soccer) simulation developed using **Python**, **PyOpenGL**, and **GLUT**. 

This project demonstrates the implementation of basic game physics, AI behavior, and real-time rendering without relying on heavy game engines. It features a competitive 1v1 gameplay mode where two players compete on a large field, supported by automated goalkeepers and tactical mechanics.

---

## Project Overview

The simulation strips down the complexities of standard football to focus on core mechanics: positioning, ball control, and timing. 

### Key Features

*   **1v1 Competitive Gameplay:** A focused match between two user-controlled agents (Red vs. White).
*   **Ball Physics & Control:** Implements a "sticky" ball mechanic for dribbling, requiring opponents to actively tackle to gain possession.
*   **Tactical Mechanics:** 
    *   **Tackling:** Players can knock the ball loose from an opponent, triggering a temporary cooldown for the victim.
    *   **Shooting:** The same input key is used for powerful shots when in possession.
*   **AI Goalkeepers:** Each team is supported by an automated goalkeeper that tracks the ball and clears it from the goal area.
*   **Dynamic Camera:** Features a high-angle, tactical view to allow players to strategize positioning on the large field.
*   **Game Loop:** Includes a scoring system, kickoff resets, and a match timer.

---

## Controls

The game is designed for local multiplayer on a single keyboard.

| Team | Movement | Action (Kick / Tackle) |
| :--- | :--- | :--- |
| **Red Team** (Left) | `W`, `A`, `S`, `D` | `Left Shift` |
| **White Team** (Right) | `Arrow Keys` | `Right Shift` |

*   **Kick:** Press `Shift` while possessing the ball to shoot in your facing direction.
*   **Tackle:** Press `Shift` when near an opponent with the ball to steal it.

---

## Installation & Usage

### Prerequisites
*   Python 3.x
*   `pip` package manager

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd PyFootball
    ```

2.  **Install dependencies:**
    This project requires `PyOpenGL` for rendering.
    ```bash
    pip install PyOpenGL PyOpenGL_accelerate
    ```

3.  **Run the simulation:**
    ```bash
    python main.py
    ```

---

*Note: This project serves as an educational exploration of computer graphics and game logic implementation in Python.*
