from gym.envs.registration import register

register(
    id='CarEnv-v0',
    entry_point='car_env.envs:CarEnv',
)