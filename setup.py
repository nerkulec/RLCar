from setuptools import setup

setup(name='CarEnv-v0',
      version='0.0.1',
      install_requires=['gym', 'pyglet', 'numpy'],
      include_package_data=True,
      package_data={
            '': ['*.txt']
      }
)