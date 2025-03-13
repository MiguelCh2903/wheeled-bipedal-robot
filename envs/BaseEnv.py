import time

import numpy as np
from gymnasium import Env
from gymnasium.core import ActType
from gymnasium.spaces import Box

from config import *
from utils.udp import UDPConnectionManager


class BaseEnv(Env):
    def __init__(self):
        self.current_state = np.zeros(6, np.float32)

        # Action and obs spaces definition
        self.action_space = Box(low=-1, high=1, shape=(6,))
        self.observation_space = Box(low=-1, high=1, shape=(12,))
        self.udp = UDPConnectionManager(max_deque_len=MAX_DEQUE_LEN)
        self.udp.bind(HOST, PORT)
        self.udp.listen()
        pass

    def step(self, action: ActType):
        self.current_state += action * ACTION_FACTOR
        self.current_state = np.clip(self.current_state, -1, 1, dtype=np.float32)
        self.udp.send_data(self.current_state.tobytes())
        time.sleep(0.01)
        obs, rew = self.udp.get_data()
        return obs, rew, False, False, {}

    def reset(self, seed:int=None, options=None):
        super().reset(seed=seed)
        pass

    def close(self):
        self.udp.close()
        pass
