# -*- coding: utf-8 -*-

from pydantic import BaseModel

class Joycon(BaseModel):
    right_y: int
    right_x: int
    right_a: int
    right_b: int
    right_r: int
    right_zr: int
    right_horizontal: int
    right_vertical: int
    right_accel_x: int
    right_accel_y: int
    right_accel_z: int
    right_gyro_x: float
    right_gyro_y: float
    right_gyro_z: float
    right_battery_charging: int
    right_battery_level: int
    right_home: int
    left_down: int
    left_up: int
    left_right: int
    left_left: int
    left_l: int
    left_zl: int
    left_horizontal: int
    left_vertical: int
    left_accel_x: int
    left_accel_y: int
    left_accel_z: int
    left_gyro_x: float
    left_gyro_y: float
    left_gyro_z: float
    left_battery_charging: int
    left_battery_level: int
    