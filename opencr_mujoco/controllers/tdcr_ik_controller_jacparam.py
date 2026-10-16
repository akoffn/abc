import os
from opencr_mujoco.controllers.tdcr_ik_controller import TDCRIKController


class TDCRIKControllerC2(TDCRIKController):
    """C2: 单变量变体，只改 Jacobian 估计相关的一个参数。"""

    def __init__(self, *args, **kwargs):
        param = os.environ.get("C2_PARAM", "settle").lower()
        value = os.environ.get("C2_VALUE", None)

        if value is not None:
            if param == "settle":
                kwargs.setdefault("settle_horizon_s", float(value))
            elif param == "eps":
                kwargs.setdefault("jacobian_perturbation_mm", float(value))
            elif param == "cols":
                kwargs.setdefault("jacobian_cols_per_refresh", int(value))
            else:
                raise ValueError("未知 C2_PARAM: " + param)

        super().__init__(*args, **kwargs)
