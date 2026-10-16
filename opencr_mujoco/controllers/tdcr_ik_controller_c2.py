import os
import numpy as np
from collections import deque
from opencr_mujoco.controllers.tdcr_ik_controller import TDCRIKController


class TDCRIKControllerC2(TDCRIKController):
    """C1 + cond_J 增益调度：退化时降增益，恢复后自动升回。"""
    def __init__(self, *args, gain_hi=40.0, gain_lo=20.0,
                 cond_in=160.0, cond_out=70.0, win=20, warmup=50,
                 ramp_up_steps=50, ramp_down_steps=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.gain_hi = float(os.environ.get("C2_GAIN_HI", gain_hi))
        self.gain_lo = float(os.environ.get("C2_GAIN_LO", gain_lo))
        self.cond_in = float(os.environ.get("C2_COND_IN", cond_in))
        self.cond_out = float(os.environ.get("C2_COND_OUT", cond_out))
        self.warmup = int(warmup)
        self._rate_up   = (self.gain_hi - self.gain_lo) / max(1, int(ramp_up_steps))
        self._rate_down = (self.gain_hi - self.gain_lo) / max(1, int(ramp_down_steps))
        self._cond_win = deque(maxlen=int(win))
        self._step = 0
        self._target_gain = self.gain_hi
        self.current_gain = self.gain_hi
        self.gain_switches = []

    def _update_gain(self):
        self._step += 1
        if self._step <= self.warmup:
            return
        try:
            c = float(np.linalg.cond(self.jacobian_pos @ self.jacobian_pos.T))
        except Exception:
            c = np.nan
        if not np.isfinite(c) or c <= 0:
            return
        self._cond_win.append(c)
        if len(self._cond_win) < self._cond_win.maxlen:
            return
        c_mean = sum(self._cond_win) / len(self._cond_win)
        if self._target_gain == self.gain_hi and c_mean > self.cond_in:
            self._target_gain = self.gain_lo
            self.gain_switches.append((self._step, self.gain_lo))
        elif self._target_gain == self.gain_lo and c_mean < self.cond_out:
            self._target_gain = self.gain_hi
            self.gain_switches.append((self._step, self.gain_hi))
        if self.current_gain < self._target_gain:
            self.current_gain = min(self._target_gain, self.current_gain + self._rate_up)
        elif self.current_gain > self._target_gain:
            self.current_gain = max(self._target_gain, self.current_gain - self._rate_down)

    def compute_target_qpos(self, *args, **kwargs):
        self._update_gain()
        return super().compute_target_qpos(*args, **kwargs)
