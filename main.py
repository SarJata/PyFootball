import sys
import math
import random
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Global State ---
window_width, window_height = 1000, 700

# Physics Constants
PLAYER_SPEED = 0.06
BALL_FRICTION = 0.98
KICK_STRENGTH = 0.5
KICK_RADIUS = 3.0
FIELD_W = 40
FIELD_H = 28

# Game State
ball_pos = [0.0, 0.0]
ball_vel = [0.0, 0.0]
red_score = 0
white_score = 0

game_state = 'intro' # 'intro' (credits/start), 'playing'
start_time = 0
import sys
import math
import random
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Global State ---
window_width, window_height = 1000, 700

# Physics Constants
PLAYER_SPEED = 0.25
BALL_FRICTION = 0.985
KICK_STRENGTH = 1.3
KICK_RADIUS = 3.0
FIELD_W = 40
FIELD_H = 28

# Game State
ball_pos = [0.0, 0.0]
ball_vel = [0.0, 0.0]
red_score = 0
white_score = 0

game_state = 'intro' # 'intro' (credits/start), 'playing'
start_time = 0
GAME_DURATION = 4 * 60 * 1000 # 4 minutes
HALF_TIME_DURATION = 2 * 60 * 1000 # 2 minutes

side_multiplier = 1 # 1 for first half, -1 for second half
half_time_occurred = False

# Input State
key_states = {
    'w': False, 'a': False, 's': False, 'd': False, 'space': False
}

class Agent:
    def __init__(self, team, role, home_x, home_z, is_user=False):
        self.team = team # 'red' or 'white'
        self.role = role # 'goalie', 'def', 'mid', 'att'
        self.home_x = home_x
        self.home_z = home_z
        self.x = home_x
        self.z = home_z
        self.is_user = is_user
        
        # Randomize stats slightly
        self.speed = PLAYER_SPEED * random.uniform(0.9, 1.1)
        self.aggressiveness = random.uniform(0.0, 1.0) 
        
        # Define Zone Thresholds
        self.chase_threshold = 12.0
        if self.role == 'goalie': self.chase_threshold = 6.0
        elif self.role == 'def': self.chase_threshold = 10.0
        elif self.role == 'mid': self.chase_threshold = 14.0
        elif self.role == 'att': self.chase_threshold = 14.0

    def update(self):
        global ball_pos, ball_vel, agents, key_states
        
        # --- USER CONTROL LOGIC ---
        if self.is_user:
            # Movement
            move_dx, move_dz = 0, 0
            if key_states['w']: move_dz -= 1
            if key_states['s']: move_dz += 1
            if key_states['a']: move_dx -= 1
            if key_states['d']: move_dx += 1
            
            # Normalize
            dist = math.sqrt(move_dx*move_dx + move_dz*move_dz)
            if dist > 0:
                self.x += (move_dx / dist) * self.speed * 1.2 # User is slightly faster
                self.z += (move_dz / dist) * self.speed * 1.2
            
            # Clamp to field
            self.x = max(-FIELD_W+1, min(FIELD_W-1, self.x))
            self.z = max(-FIELD_H+1, min(FIELD_H-1, self.z))
            
            # Kick
            dx = ball_pos[0] - self.x
            dz = ball_pos[1] - self.z
            dist_to_ball = math.sqrt(dx*dx + dz*dz)
            
            if key_states['space'] and dist_to_ball < KICK_RADIUS:
                self.kick(hard=True)
                key_states['space'] = False # Consume key press
            
            return # Skip AI logic for user

        # --- AI LOGIC ---
        
        # 1. Determine Target Position
        target_x = self.home_x
        target_z = self.home_z
        
        # Calculate distance to ball
        dx = ball_pos[0] - self.x
        dz = ball_pos[1] - self.z
        dist_to_ball = math.sqrt(dx*dx + dz*dz)
        
        # --- Max 3 Chasers Logic ---
        # Find teammates and rank them by distance to ball
        teammates = [a for a in agents if a.team == self.team and not a.is_user]
        teammates.sort(key=lambda a: math.sqrt((ball_pos[0]-a.x)**2 + (ball_pos[1]-a.z)**2))
        
        try:
            rank = teammates.index(self) # 0 is closest
        except ValueError:
            rank = 99 # Should not happen unless self is user (handled above)
        
        should_chase = False
        
        # Only top 3 closest are allowed to consider chasing
        if rank < 3:
            # The absolute closest ALWAYS chases (to prevent stalling)
            if rank == 0:
                should_chase = True
            # The 2nd and 3rd closest chase ONLY if within their personal threshold
            elif dist_to_ball < self.chase_threshold:
                should_chase = True
        
        # Goalie restriction: Goalie rarely leaves box even if closest
        if self.role == 'goalie' and dist_to_ball > 10.0:
            should_chase = False
        
        if should_chase:
            bias = 0.8 
            target_x = ball_pos[0]
            target_z = ball_pos[1]
            
            # Goalie stays near goal
            if self.role == 'goalie':
                target_x = self.home_x 
                target_z = max(-5, min(5, ball_pos[1])) 
        
        # Move towards target
        move_dx = target_x - self.x
        move_dz = target_z - self.z
        
        # --- Improved Collision Avoidance ---
        sep_x, sep_z = 0, 0
        collision_radius = 3.5 
        
        for other in agents:
            if other is self: continue
            dist_x = self.x - other.x
            dist_z = self.z - other.z
            dist = math.sqrt(dist_x*dist_x + dist_z*dist_z)
            
            if dist < collision_radius and dist > 0.001:
                # Stronger repulsion force
                force = (collision_radius - dist) / dist 
                sep_x += dist_x * force
                sep_z += dist_z * force
        
        # Apply separation heavily
        move_dx += sep_x * 8.0 
        move_dz += sep_z * 8.0
        
        move_dist = math.sqrt(move_dx*move_dx + move_dz*move_dz)
        
        if move_dist > 0.1:
            self.x += (move_dx / move_dist) * self.speed
            self.z += (move_dz / move_dist) * self.speed
            
        # Clamp to field
        self.x = max(-FIELD_W+1, min(FIELD_W-1, self.x))
        self.z = max(-FIELD_H+1, min(FIELD_H-1, self.z))
        
        # 2. Kick Logic
        if dist_to_ball < KICK_RADIUS:
            if random.random() < 0.1: 
                self.kick(hard=True)
            elif random.random() < 0.3: 
                self.kick(hard=False)

    def kick(self, hard):
        global ball_vel, side_multiplier
        
        # Target Goal
        if self.team == 'red':
            goal_x = 40 * side_multiplier
        else:
            goal_x = -40 * side_multiplier
        
        # Add noise to shot
        noise_z = random.uniform(-10, 10)
        
        k_dx = goal_x - self.x
        k_dz = (0 + noise_z) - self.z
        k_len = math.sqrt(k_dx*k_dx + k_dz*k_dz)
        
        if k_len == 0: k_len = 1
        
        power = KICK_STRENGTH if hard else KICK_STRENGTH * 0.3
        
        ball_vel[0] = (k_dx / k_len) * power
        ball_vel[1] = (k_dz / k_len) * power


# --- Setup Teams ---
agents = []

def setup_teams():
    global agents, side_multiplier
    agents = []
    
    # Helper to flip X if side_multiplier is -1
    def gx(x): return x * side_multiplier
    
    # Red Team 
    # Normally starts on Left (-X) and attacks Right (+X).
    # If side_multiplier is -1, they start on Right (+X) and attack Left (-X).
    
    # Goalie
    agents.append(Agent('red', 'goalie', gx(-36), 0))
    # Defenders
    agents.append(Agent('red', 'def', gx(-25), -10))
    agents.append(Agent('red', 'def', gx(-25), -3))
    agents.append(Agent('red', 'def', gx(-25), 3))
    agents.append(Agent('red', 'def', gx(-25), 10))
    # Midfielders
    agents.append(Agent('red', 'mid', gx(-10), -12))
    agents.append(Agent('red', 'mid', gx(-10), -4))
    agents.append(Agent('red', 'mid', gx(-10), 4))
    agents.append(Agent('red', 'mid', gx(-10), 12))
    # Attackers
    # USER PLAYER: First Red Attacker
    agents.append(Agent('red', 'att', gx(2), -5, is_user=True))
    agents.append(Agent('red', 'att', gx(2), 5))

    # White Team
    # Normally starts on Right (+X) and attacks Left (-X).
    
    # Goalie
    agents.append(Agent('white', 'goalie', gx(36), 0))
    # Defenders
    agents.append(Agent('white', 'def', gx(25), -10))
    agents.append(Agent('white', 'def', gx(25), -3))
    agents.append(Agent('white', 'def', gx(25), 3))
    agents.append(Agent('white', 'def', gx(25), 10))
    # Midfielders
    agents.append(Agent('white', 'mid', gx(10), -12))
    agents.append(Agent('white', 'mid', gx(10), -4))
    agents.append(Agent('white', 'mid', gx(10), 4))
    agents.append(Agent('white', 'mid', gx(10), 12))
    # Attackers
    agents.append(Agent('white', 'att', gx(-2), -5))
    agents.append(Agent('white', 'att', gx(-2), 5))

def reset_game(scorer):
    global ball_pos, ball_vel
    ball_pos = [0, 0]
    ball_vel = [0, 0]
    setup_teams()
    print(f"Score! Red: {red_score} - White: {white_score}")

# --- OpenGL Boilerplate ---
def init():
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 30.0, 10.0, 0.0])

def reshape(w, h):
    global window_width, window_height
    window_width, window_height = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = w / h if h > 0 else 1
    view_size = 45.0
    if w >= h:
        glOrtho(-view_size * aspect, view_size * aspect, -view_size, view_size, -100.0, 100.0)
    else:
        glOrtho(-view_size, view_size, -view_size / aspect, view_size / aspect, -100.0, 100.0)
    glMatrixMode(GL_MODELVIEW)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def draw_field():
    glColor3f(0.1, 0.6, 0.1)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-FIELD_W, 0, -FIELD_H-2); glVertex3f(FIELD_W, 0, -FIELD_H-2)
    glVertex3f(FIELD_W, 0, FIELD_H+2); glVertex3f(-FIELD_W, 0, FIELD_H+2)
    glEnd()
    
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex3f(-FIELD_W+2, 0.1, -FIELD_H); glVertex3f(FIELD_W-2, 0.1, -FIELD_H)
    glVertex3f(FIELD_W-2, 0.1, FIELD_H); glVertex3f(-FIELD_W+2, 0.1, FIELD_H)
    glEnd()
    glBegin(GL_LINES)
    glVertex3f(0, 0.1, -FIELD_H); glVertex3f(0, 0.1, FIELD_H)
    glEnd()

def draw_goal(x_pos):
    glColor3f(0.9, 0.9, 0.9)
    glLineWidth(4.0)
    z_width = 8; height = 5
    glPushMatrix()
    glTranslatef(x_pos, 0, 0)
    glBegin(GL_LINES)
    glVertex3f(0, 0, -z_width); glVertex3f(0, height, -z_width)
    glVertex3f(0, 0, z_width); glVertex3f(0, height, z_width)
    glVertex3f(0, height, -z_width); glVertex3f(0, height, z_width)
    glEnd()
    glPopMatrix()

def draw_scoreboard():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    
    score_text = f"RED: {red_score}   |   WHITE: {white_score}"
    text_width = len(score_text) * 9
    draw_text(window_width/2 - text_width/2, window_height - 30, score_text)
    
    elapsed = glutGet(GLUT_ELAPSED_TIME) - start_time
    remaining = max(0, GAME_DURATION - elapsed)
    mins = int(remaining / 60000)
    secs = int((remaining % 60000) / 1000)
    
    period = "1st Half" if not half_time_occurred else "2nd Half"
    time_text = f"{period} - {mins:02d}:{secs:02d}"
    
    draw_text(window_width/2 - 50, window_height - 55, time_text)
    
    # Controls Help
    draw_text(10, window_height - 30, "Controls: WASD to Move, SPACE to Kick")

    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_credits():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Background
    glColor3f(0.1, 0.1, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(window_width, 0)
    glVertex2f(window_width, window_height)
    glVertex2f(0, window_height)
    glEnd()
    
    glColor3f(1.0, 1.0, 1.0)
    
    lines = [
        "Dayananda Sagar Academy of Technology and Management",
        "Dept. of CSE",
        "",
        "Submitted by:",
        "D - 1DT23CS048",
        "A - 1DT23CS048",
        "A - 1DT23CS048",
        "S - 1DT23CS048",
        "",
        "Press SPACE or ENTER to Start Match"
    ]
    
    start_y = window_height / 2 + 120
    line_height = 30
    
    for i, line in enumerate(lines):
        w = len(line) * 9
        draw_text(window_width/2 - w/2, start_y - i*line_height, line)
        
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    global game_state
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    if game_state == 'playing':
        glLoadIdentity()
        glRotatef(35.264, 1.0, 0.0, 0.0)
        glRotatef(45.0, 0.0, 1.0, 0.0)
        
        draw_field()
        draw_goal(-FIELD_W+2)
        draw_goal(FIELD_W-2)
        
        # Draw Agents
        for a in agents:
            glPushMatrix()
            glTranslatef(a.x, 1.0, a.z)
            
            if a.is_user:
                glColor3f(0.2, 0.2, 1.0) # Blue for User
            elif a.team == 'red': 
                glColor3f(0.9, 0.1, 0.1)
            else: 
                glColor3f(0.9, 0.9, 0.9) # White
                
            glutSolidCube(1.8)
            glPopMatrix()
        
        # Draw Ball (Yellow)
        glPushMatrix()
        glTranslatef(ball_pos[0], 1.0, ball_pos[1])
        glColor3f(1.0, 1.0, 0.0)
        glutSolidSphere(1.0, 16, 16)
        glPopMatrix()
        
        draw_scoreboard()
        
    elif game_state == 'intro':
        draw_credits()
    
    glutSwapBuffers()

def keyboard(key, x, y):
    global game_state, start_time, red_score, white_score, side_multiplier, half_time_occurred, ball_pos, ball_vel, key_states
    
    if game_state == 'intro':
        if key == b' ' or key == b'\r': # Space or Enter
            game_state = 'playing'
            start_time = glutGet(GLUT_ELAPSED_TIME)
            # Reset Game State
            red_score = 0
            white_score = 0
            side_multiplier = 1
            half_time_occurred = False
            ball_pos = [0, 0]
            ball_vel = [0, 0]
            setup_teams()
            print("Match Started!")
            
    elif game_state == 'playing':
        try:
            k = key.decode('utf-8').lower()
            if k in key_states:
                key_states[k] = True
            if k == ' ':
                key_states['space'] = True
        except:
            pass

def keyboard_up(key, x, y):
    global key_states
    try:
        k = key.decode('utf-8').lower()
        if k in key_states:
            key_states[k] = False
        if k == ' ':
            key_states['space'] = False
    except:
        pass

def update(value):
    global ball_pos, ball_vel, red_score, white_score, game_state, start_time, half_time_occurred, side_multiplier
    
    current_time = glutGet(GLUT_ELAPSED_TIME)
    
    if game_state == 'playing':
        elapsed = current_time - start_time
        
        # Halftime Check
        if not half_time_occurred and elapsed > HALF_TIME_DURATION:
            half_time_occurred = True
            side_multiplier = -1
            setup_teams() # Switch sides
            ball_pos = [0, 0]
            ball_vel = [0, 0]
            print("Halftime! Switching Sides.")
            
        # Game Over Check
        if elapsed > GAME_DURATION:
            game_state = 'intro'
            print("Match Ended. Returning to Credits.")
        
        # Update Agents
        for a in agents:
            a.update()
        
        # Ball Physics
        ball_pos[0] += ball_vel[0]
        ball_pos[1] += ball_vel[1]
        ball_vel[0] *= BALL_FRICTION
        ball_vel[1] *= BALL_FRICTION
        
        # Wall Bounce
        if ball_pos[1] > FIELD_H or ball_pos[1] < -FIELD_H:
            ball_vel[1] *= -1
            ball_pos[1] = max(-FIELD_H, min(FIELD_H, ball_pos[1]))
        
        # Goals
        if ball_pos[0] > FIELD_W:
            red_score += 1
            reset_game('red')
        elif ball_pos[0] < -FIELD_W:
            white_score += 1
            reset_game('white')
            
    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

if __name__ == "__main__":
    setup_teams()
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"11v11 AI Football Simulation")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutTimerFunc(0, update, 0)
    print("Simulation Loaded. Press SPACE to start.")
    glutMainLoop()
