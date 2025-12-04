import sys
import math
import random
import time
import ctypes
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Global State ---
window_width, window_height = 1200, 800

# Physics Constants
PLAYER_SPEED = 0.5
BALL_FRICTION = 0.98
KICK_STRENGTH = 2.5
FIELD_W = 90  # Drastically increased size
FIELD_H = 60
GOAL_WIDTH = 36 # Increased from 20

# Game State
ball_pos = [0.0, 0.0]
ball_vel = [0.0, 0.0]
ball_owner = None # The agent currently possessing the ball

red_score = 0
white_score = 0

game_state = 'intro' # 'intro', 'playing'
start_time = 0
GAME_DURATION = 4 * 60 * 1000 # 4 minutes

# Input State
key_states = {
    'w': False, 'a': False, 's': False, 'd': False,
    'up': False, 'down': False, 'left': False, 'right': False
}

# Windows Key Codes
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1

def is_key_pressed(vk_code):
    # Check if key is currently down (high bit set)
    return (ctypes.windll.user32.GetKeyState(vk_code) & 0x8000) != 0

class Agent:
    def __init__(self, team, x, z, role='player'):
        self.team = team
        self.x = x
        self.z = z
        self.role = role # 'player' or 'goalie'
        self.speed = PLAYER_SPEED
        # Default facing direction
        self.dir_x = 1.0 if team == 'red' else -1.0
        self.dir_z = 0.0
        self.tackle_cooldown = 0

    def update(self):
        global ball_pos, ball_vel, ball_owner
        
        if self.tackle_cooldown > 0:
            self.tackle_cooldown -= 1

        # --- Movement ---
        move_dx, move_dz = 0, 0
        
        if self.role == 'player':
            # User Control
            if self.team == 'red':
                if key_states['w']: move_dz -= 1
                if key_states['s']: move_dz += 1
                if key_states['a']: move_dx -= 1
                if key_states['d']: move_dx += 1
            else: # white
                if key_states['up']: move_dz -= 1
                if key_states['down']: move_dz += 1
                if key_states['left']: move_dx -= 1
                if key_states['right']: move_dx += 1
                
            # Normalize and Move
            dist = math.sqrt(move_dx*move_dx + move_dz*move_dz)
            if dist > 0:
                # Apply speed penalty if carrying the ball
                current_speed = self.speed
                if ball_owner == self:
                    current_speed *= 0.85 # 15% slower when dribbling
                
                self.x += (move_dx / dist) * current_speed
                self.z += (move_dz / dist) * current_speed
                # Update facing direction
                self.dir_x = move_dx / dist
                self.dir_z = move_dz / dist
        
        elif self.role == 'goalie':
            # Dumb Goalie Logic
            # Stay on goal line X, track ball Z
            goal_x = -FIELD_W + 5 if self.team == 'red' else FIELD_W - 5
            
            # Move towards ball Z, clamped to goal width
            target_z = max(-GOAL_WIDTH/2, min(GOAL_WIDTH/2, ball_pos[1]))
            
            # Simple P-controller movement
            dz = target_z - self.z
            if abs(dz) > 0.5:
                # NERFED: Reduced speed multiplier from 0.6 to 0.35
                move_z = math.copysign(self.speed * 0.35, dz) 
                self.z += move_z
                self.dir_z = math.copysign(1, move_z)
            
            # Keep X fixed mostly, maybe slight wobble
            self.x = goal_x
            self.dir_x = 1.0 if self.team == 'red' else -1.0
            
            # Auto-kick if ball is close
            dist_to_ball = math.sqrt((self.x - ball_pos[0])**2 + (self.z - ball_pos[1])**2)
            if dist_to_ball < 4.0 and ball_owner is None:
                # Kick away from goal
                self.kick(force_dir_x = 1.0 if self.team == 'red' else -1.0)

        # Clamp to field
        self.x = max(-FIELD_W+2, min(FIELD_W-2, self.x))
        self.z = max(-FIELD_H+2, min(FIELD_H-2, self.z))
        
        # --- Ball Interaction ---
        dist_to_ball = math.sqrt((self.x - ball_pos[0])**2 + (self.z - ball_pos[1])**2)
        
        # 1. Pick up ball (Stick)
        # If ball is free and we touch it, we take it.
        # Added cooldown check so you don't instantly re-grab after being tackled
        if ball_owner is None and dist_to_ball < 3.0 and self.tackle_cooldown == 0:
            ball_owner = self
            ball_vel = [0, 0]
            
        # 2. Handle Shift Actions (Tackle / Kick)
        is_shift = False
        if self.team == 'red':
            is_shift = is_key_pressed(VK_LSHIFT)
        else:
            is_shift = is_key_pressed(VK_RSHIFT)
            
        if is_shift and self.role == 'player':
            # Case A: I have the ball -> Kick/Shoot
            if ball_owner == self:
                self.kick()
                
            # Case B: Opponent has ball and I am close -> Tackle
            elif ball_owner is not None and ball_owner != self:
                # Increased tackle range slightly
                if dist_to_ball < 6.0: 
                    self.tackle(ball_owner)
        
        # 3. Dribble (if I own the ball)
        if ball_owner == self:
            # Keep ball slightly in front of player
            ball_pos[0] = self.x + self.dir_x * 2.0
            ball_pos[1] = self.z + self.dir_z * 2.0
            ball_vel = [0, 0]

    def kick(self, force_dir_x=None):
        global ball_owner, ball_vel
        ball_owner = None
        # Kick in facing direction or forced direction
        dx = force_dir_x if force_dir_x is not None else self.dir_x
        dz = self.dir_z
        
        ball_vel[0] = dx * KICK_STRENGTH
        ball_vel[1] = dz * KICK_STRENGTH
        
        # Add slight cooldown to prevent instant re-grab
        self.tackle_cooldown = 10
        
    def tackle(self, victim):
        global ball_owner, ball_vel
        # Steal/Knock loose
        ball_owner = None
        
        # Apply cooldown to victim so they can't instantly grab it back
        victim.tackle_cooldown = 60 # 1 second cooldown
        
        # Ball pops out in tackler's direction slightly
        ball_vel[0] = self.dir_x * 0.5
        ball_vel[1] = self.dir_z * 0.5

# --- Setup ---
agents = []

def setup_teams(kickoff_team=None):
    global agents, ball_owner, ball_pos, ball_vel
    agents = []
    ball_owner = None
    ball_pos = [0, 0]
    ball_vel = [0, 0]
    
    # Red Team
    # Player
    red_x = -5 if kickoff_team == 'red' else -30
    agents.append(Agent('red', red_x, 0, role='player'))
    # Goalie
    agents.append(Agent('red', -FIELD_W+5, 0, role='goalie'))
    
    # White Team
    # Player
    white_x = 5 if kickoff_team == 'white' else 30
    agents.append(Agent('white', white_x, 0, role='player'))
    # Goalie
    agents.append(Agent('white', FIELD_W-5, 0, role='goalie'))
    
    # Give ball to kickoff team
    if kickoff_team == 'red':
        ball_owner = agents[0] # Red Player
    elif kickoff_team == 'white':
        ball_owner = agents[2] # White Player (index 2 is white player)

def reset_game(scorer):
    global ball_pos, ball_vel, ball_owner
    ball_pos = [0, 0]
    ball_vel = [0, 0]
    ball_owner = None
    
    # If Red scores, White gets kickoff
    kickoff_team = 'white' if scorer == 'red' else 'red'
    
    setup_teams(kickoff_team)
    print(f"Goal! {scorer.upper()} scores! {kickoff_team.upper()} Kickoff.")

# --- OpenGL Boilerplate ---
def init():
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 50.0, 10.0, 0.0])

def reshape(w, h):
    global window_width, window_height
    window_width, window_height = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = w / h if h > 0 else 1
    
    # Increased view size to see the larger field
    view_size = 80.0 
    
    # Fix: Increase Z-range significantly to prevent clipping
    if w >= h:
        glOrtho(-view_size * aspect, view_size * aspect, -view_size, view_size, -500.0, 500.0)
    else:
        glOrtho(-view_size, view_size, -view_size / aspect, view_size / aspect, -500.0, 500.0)
    glMatrixMode(GL_MODELVIEW)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def draw_field():
    # Grass
    glColor3f(0.1, 0.6, 0.1)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-FIELD_W, 0, -FIELD_H-2); glVertex3f(FIELD_W, 0, -FIELD_H-2)
    glVertex3f(FIELD_W, 0, FIELD_H+2); glVertex3f(-FIELD_W, 0, FIELD_H+2)
    glEnd()
    
    # Lines
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex3f(-FIELD_W+2, 0.1, -FIELD_H); glVertex3f(FIELD_W-2, 0.1, -FIELD_H)
    glVertex3f(FIELD_W-2, 0.1, FIELD_H); glVertex3f(-FIELD_W+2, 0.1, FIELD_H)
    glEnd()
    
    # Center Line
    glBegin(GL_LINES)
    glVertex3f(0, 0.1, -FIELD_H); glVertex3f(0, 0.1, FIELD_H)
    glEnd()
    
    # Center Circle
    glBegin(GL_LINE_LOOP)
    for i in range(36):
        angle = 2 * math.pi * i / 36
        glVertex3f(math.cos(angle)*10, 0.1, math.sin(angle)*10)
    glEnd()

def draw_goal(x_pos):
    # Goal Posts
    glColor3f(0.9, 0.9, 0.9)
    glLineWidth(6.0)
    z_width = GOAL_WIDTH / 2
    height = 8
    
    glPushMatrix()
    glTranslatef(x_pos, 0, 0)
    
    # Frame
    glBegin(GL_LINES)
    glVertex3f(0, 0, -z_width); glVertex3f(0, height, -z_width)
    glVertex3f(0, 0, z_width); glVertex3f(0, height, z_width)
    glVertex3f(0, height, -z_width); glVertex3f(0, height, z_width)
    glEnd()
    
    # Netting (Visual only)
    glLineWidth(1.0)
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_LINES)
    for i in range(10):
        t = i / 10.0
        # Vertical net lines
        z = -z_width + (z_width * 2 * t)
        glVertex3f(0, height, z); glVertex3f(-5 if x_pos > 0 else 5, 0, z)
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
    
    time_text = f"{mins:02d}:{secs:02d}"
    draw_text(window_width/2 - 20, window_height - 55, time_text)
    
    # Controls Help
    help_text = "RED: WASD + L-Shift (Tackle/Kick)  |  WHITE: Arrows + R-Shift (Tackle/Kick)"
    draw_text(window_width/2 - (len(help_text)*9)/2, 20, help_text)

    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_intro():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST) # Fix: Disable depth test for 2D overlay
    
    # Background
    glColor3f(0.1, 0.1, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(window_width, 0)
    glVertex2f(window_width, window_height); glVertex2f(0, window_height)
    glEnd()
    
    glColor3f(1, 1, 1)
    
    lines = [
        "Dayananda Sagar Academy of Technology and Management",
        "Dept of CSE",
        "",
        "Submitted by:",
        "Darshan - 1DT23CS048",
        "Angad - 1DT23CS0XX",
        "Ayush - 1DT23CS0XX",
        "Bhargav - 1DT23CS0XX",
        "",
        "Press SPACE to Start Match"
    ]
    
    start_y = window_height / 2 + 100
    line_height = 30
    
    for i, line in enumerate(lines):
        w = len(line) * 9
        draw_text(window_width/2 - w/2, start_y - i*line_height, line)
    
    glEnable(GL_DEPTH_TEST) # Restore depth test
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
        # Top-down view for "Foosball/Tactical" feel
        # Eye at (0, 100, 50), looking at (0,0,0), Up (0,1,0)
        gluLookAt(0, 100, 50, 0, 0, 0, 0, 1, 0)
        
        draw_field()
        draw_goal(-FIELD_W+2)
        draw_goal(FIELD_W-2)
        
        # Draw Agents
        for a in agents:
            glPushMatrix()
            glTranslatef(a.x, 1.5, a.z)
            
            if a.team == 'red': 
                glColor3f(0.9, 0.1, 0.1)
            else: 
                glColor3f(0.9, 0.9, 0.9)
                
            glutSolidCube(3.0)
            
            # Direction Indicator
            glBegin(GL_LINES)
            glColor3f(1, 1, 0)
            glVertex3f(0, 0, 0)
            glVertex3f(a.dir_x*3, 0, a.dir_z*3)
            glEnd()
            
            glPopMatrix()
        
        # Draw Ball
        glPushMatrix()
        glTranslatef(ball_pos[0], 1.5, ball_pos[1])
        glColor3f(1.0, 0.0, 1.0) # Hot Pink for high contrast
        glutSolidSphere(1.5, 16, 16)
        glPopMatrix()
        
        draw_scoreboard()
        
    elif game_state == 'intro':
        draw_intro()
    
    glutSwapBuffers()

def keyboard(key, x, y):
    global game_state, start_time, red_score, white_score, ball_pos, ball_vel, key_states, ball_owner
    
    try:
        k = key.decode('utf-8').lower()
    except:
        return

    if game_state == 'intro':
        if k == ' ':
            game_state = 'playing'
            start_time = glutGet(GLUT_ELAPSED_TIME)
            red_score = 0
            white_score = 0
            setup_teams()
            
    elif game_state == 'playing':
        if k in key_states:
            key_states[k] = True

def keyboard_up(key, x, y):
    global key_states
    try:
        k = key.decode('utf-8').lower()
        if k in key_states:
            key_states[k] = False
    except:
        pass

def special(key, x, y):
    global key_states
    if key == GLUT_KEY_UP: key_states['up'] = True
    if key == GLUT_KEY_DOWN: key_states['down'] = True
    if key == GLUT_KEY_LEFT: key_states['left'] = True
    if key == GLUT_KEY_RIGHT: key_states['right'] = True

def special_up(key, x, y):
    global key_states
    if key == GLUT_KEY_UP: key_states['up'] = False
    if key == GLUT_KEY_DOWN: key_states['down'] = False
    if key == GLUT_KEY_LEFT: key_states['left'] = False
    if key == GLUT_KEY_RIGHT: key_states['right'] = False

def update(value):
    global ball_pos, ball_vel, red_score, white_score, game_state, ball_owner
    
    if game_state == 'playing':
        elapsed = glutGet(GLUT_ELAPSED_TIME) - start_time
        if elapsed > GAME_DURATION:
            game_state = 'intro'
        
        # Update Agents
        for a in agents:
            a.update()
        
        # Ball Physics (only if not owned)
        if ball_owner is None:
            ball_pos[0] += ball_vel[0]
            ball_pos[1] += ball_vel[1]
            ball_vel[0] *= BALL_FRICTION
            ball_vel[1] *= BALL_FRICTION
            
            # Wall Bounce
            if ball_pos[1] > FIELD_H or ball_pos[1] < -FIELD_H:
                ball_vel[1] *= -0.8
                ball_pos[1] = max(-FIELD_H, min(FIELD_H, ball_pos[1]))
            if ball_pos[0] > FIELD_W or ball_pos[0] < -FIELD_W:
                # Goal Check
                if abs(ball_pos[1]) < GOAL_WIDTH:
                    if ball_pos[0] > FIELD_W:
                        red_score += 1
                        reset_game('red')
                    else:
                        white_score += 1
                        reset_game('white')
                else:
                    # Bounce off back wall if not goal
                    ball_vel[0] *= -0.8
                    ball_pos[0] = max(-FIELD_W, min(FIELD_W, ball_pos[0]))

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

if __name__ == "__main__":
    print("Starting application...")
    try:
        glutInit(sys.argv)
        print("GLUT Initialized.")
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(window_width, window_height)
        window = glutCreateWindow(b"1v1 Football")
        print(f"Window created: {window}")
        if not window:
            print("Failed to create window!")
            sys.exit(1)
        init()
        print("OpenGL Initialized.")
        glutDisplayFunc(display)
        glutReshapeFunc(reshape)
        glutKeyboardFunc(keyboard)
        glutKeyboardUpFunc(keyboard_up)
        glutSpecialFunc(special)
        glutSpecialUpFunc(special_up)
        glutTimerFunc(0, update, 0)
        print("Entering Main Loop...")
        glutMainLoop()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
