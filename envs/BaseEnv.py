from gymnasium import Env
from gymnasium.core import ActType
from gymnasium.spaces import Box

from config import *
from utils.udp import UDPConnectionManager


class BaseEnv(Env):
    def __init__(self):
        # Action and obs spaces definition
        self.action_space = Box(low=-1, high=1, shape=(6,))
        self.observation_space = Box(low=-1, high=1, shape=(12,))
        udp = UDPConnectionManager(max_deque_len=MAX_DEQUE_LEN)
        udp.connect(HOST, PORT)
        udp.listen()
        pass

    def step(self, action: ActType):
        pass

    def reset(self, seed:int=None, options=None):
        super().reset(seed=seed)
        pass

    def close(self):
        pass
