import gym
from gym import spaces
import pyglet
from pyglet import shapes
from pyglet.gl import glScalef, glTranslatef
import numpy as np
import math

from car import Car, max_vel, max_acc
from racing_track import Map, tile_width
from util import Vec

class Spec: # remove when env properly registered
  def __init__(self, id):
    self.id = id

class CarEnv(gym.Env):
  metadata = {'render.modes': ['human', 'trajectories']}

  def __init__(self, file_name = 'maps/map1.txt', num_rays = 12, draw_rays = True):
    super().__init__()
    self.action_space = spaces.Box(-1, 1, shape=(2,), dtype=np.float32)
    self.map = Map(file_name)
    self.car = Car()
    # self.observation_space = spaces.Box(low= np.array([0, 0, -1, -1], dtype=np.float32),
    #   high=np.array([self.map.width, self.map.height, 1, 1], dtype=np.float32),
    #   shape=(4,), dtype=np.float32)
    num_features = 2
    self.num_rays = num_rays
    self.observation_space = spaces.Box(
      low=np.concatenate([np.array([-1, -1], dtype=np.float32), np.zeros(num_features*self.num_rays, dtype=np.float32)]),
      high=np.concatenate([np.array([1, 1], dtype=np.float32), np.ones(num_features*self.num_rays, dtype=np.float32)]),
      dtype=np.float32, shape=(2+num_features*self.num_rays,)
    )
    self.window = None
    self.spec = Spec('RLCar-v0')
    self.color = None
    self.trajectories = [[]]
    self.heatmap = []
    self.batch = None
    self.draw_rays = draw_rays
    self.opacity = None
    
  def get_obs(self):
    obs = [
      np.array([self.car.vel.x, self.car.vel.y]),
      self.map.get_closest(self.car.pos, '#', rays=self.num_rays, batch=self.draw_rays and self.batch or None),
      # self.map.get_closest(self.car.pos, 'O'),
      # self.map.get_closest(self.car.pos, 'C'),
      self.map.get_closest(self.car.pos, 'M', rays=self.num_rays)
    ]
    return np.concatenate(obs)

  def step(self, action):
    action = action*max_acc
    car = self.car
    if self.color is not None:
      prev_pos = Vec(car.pos.x, car.pos.y)
    car.update(action, self.ground)
    if self.color is not None and self.batch is not None:
      line = shapes.Line(prev_pos.x*tile_width, prev_pos.y*tile_width, car.pos.x*tile_width, car.pos.y*tile_width, color=self.color, batch=self.batch)
      line.opacity = self.opacity or 63
      self.trajectories[-1].append(line)
    self.ground = self.map[car.pos]
    obs = self.get_obs()
    # obs = np.array([car.pos.x, car.pos.y, car.vel.x, car.vel.y])*np.array([1, 1, 1/max_vel, 1/max_vel])
    self.steps += 1
    if self.steps >= 200:
      reward = -100 # or -150 or -50 or 0 or 50 ??
      done = True
    elif self.ground == ' ' or self.ground == 'O':
      reward = -1
      done = False
    elif self.ground == '#':
      reward = -100
      done = True
    elif self.ground == 'C':
      reward = -100
      done = False
    elif self.ground == 'M':
      reward = 1000
      done = True
    else:
      raise Exception('Unsupported ground')

    if done and self.ground != 'M':
      reward -= math.sqrt((car.pos.x-self.map.M.x)**2+(car.pos.y-self.map.M.y)**2)
    
    if done:
      self.trajectories.append([])
    
    return obs, reward, done, {}
    
  def reset(self):
    self.car = Car()
    self.ground = ' '
    self.steps = 0
    return self.get_obs()
  
  def set_color(self, color):
    self.color = color    
    
  def render(self, mode='human', close=False):
    if mode == 'human':
      if self.window is None:
        self.window = pyglet.window.Window(self.map.width*tile_width, self.map.height*tile_width)
        glTranslatef(-1, 1, 0)
        glScalef(2/self.map.width/tile_width, -2/self.map.height/tile_width, 1)
        self.batch = pyglet.graphics.Batch()
        self.circle = shapes.Circle(self.car.pos.x*tile_width, self.car.pos.y*tile_width, tile_width/4, color=(255, 128, 128), batch=self.batch)
        self.map.draw(self.batch)
      self.circle.x = self.car.pos.x*tile_width
      self.circle.y = self.car.pos.y*tile_width
      self.window.clear()
      # Draw board
      self.batch.draw()
      # Draw car
      self.circle.draw()
      self.window.flip()
    if mode == 'trajectories':
      if self.window is None:
        self.window = pyglet.window.Window(self.map.width*tile_width, self.map.height*tile_width)
        glTranslatef(-1, 1, 0)
        glScalef(2/self.map.width/tile_width, -2/self.map.height/tile_width, 1)
        self.batch = pyglet.graphics.Batch()
        self.map.draw(self.batch)
      self.window.clear()
      self.batch.draw()
      self.window.flip()
    
  def close(self):
    super().close()
    if self.window is not None:
      self.window.close()
      self.window = None