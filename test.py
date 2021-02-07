from car_env import CarEnv
import numpy as np

env = CarEnv()

state = env.reset()
done = False
while not done:
    env.render()
    action = np.array([1, 0])
    obs, reward, done, _ = env.step(action)