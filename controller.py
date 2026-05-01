# controller.py
#
# Faulty decision logic for the 2026 Autonomous Newbie Project.
# Recruits will mainly modify this file.
#
# Sign convention:
# lane_offset_m:
#   negative = vehicle is left of lane center
#   positive = vehicle is right of lane center
#
# heading_error_deg:
#   negative = vehicle heading points left of desired direction
#   positive = vehicle heading points right of desired direction
#
# Steering output semantics:
# "LEFT" means command the vehicle to steer / move left.
# "RIGHT" means command the vehicle to steer / move right.
# Therefore:
# - positive lane_offset_m means vehicle is right of center, so LEFT is corrective
# - positive heading_error_deg means vehicle points right of desired direction, so LEFT is corrective

VALID_STEERING = {"LEFT", "RIGHT", "STRAIGHT"}
VALID_SPEED = {"ACCELERATE", "SLOW", "STOP"}


def controller(
    obstacle_distance_m, # how far a specified obstacle is
    lane_offset_m, # off set from course in meters
    heading_error_deg, # heading error in degrees
    speed_mps, # speed in meters / second
    e_stop, # emergency stop
    left_clear, # left is clear to turn
    right_clear, # right is clear to turn
    sensor_valid
):
    """
    Returns:
        (steering, speed_action)

        steering:
            "LEFT", "RIGHT", "STRAIGHT"

        speed_action:
            "ACCELERATE", "SLOW", "STOP"
    """
    # Tolerances used for each property
    DANGER_OBSTACLE_M = 1.0
    CAUTION_OBSTACLE_M = 2.0

    MILD_HEADING_DEG = 3.0 # tolerance for low heading error
    LARGE_HEADING_DEG = 15.0 # tolerance for large heading error

    MILD_OFFSET_M = 0.15 # tolerance for low off set error
    LARGE_OFFSET_M = 0.40 # tolerance for large off set error

    HIGH_SPEED_MPS = 3.0

    centered = abs(lane_offset_m) <= MILD_OFFSET_M # within low off set error considered straight
    small_heading_error = abs(heading_error_deg) <= MILD_HEADING_DEG # like wise for heading error

    steering = "STRAIGHT"
    speed_action = "ACCELERATE"

    if not sensor_valid:
        return "STRAIGHT", "STOP"
    
    # ----------- OBSTACLE AVOIDANCE LOGIC -----------
    # When TOO CLOSE to an obstacle
    if obstacle_distance_m <= DANGER_OBSTACLE_M:
        print("CAR TOO CLOSE")
        # Stop vehicle if too close, and emergency stop is enabled
        if e_stop:
            steering = "STRAIGHT"
            speed_action = "STOP"

        # If no clear roads then stop
        elif not left_clear and not right_clear:
            steering = "STRAIGHT"
            speed_action = "STOP"

        # If left clear turn left slowly
        elif left_clear and not right_clear:
            steering = "LEFT"
            speed_action = "SLOW"

        # if right clear turn slowly
        elif right_clear and not left_clear:
            steering = "RIGHT"
            speed_action = "SLOW"

        # Other wise if BOTH ways clear
        # First ensure vehicle is aligned and on staright path
        elif heading_error_deg > MILD_HEADING_DEG or lane_offset_m > MILD_OFFSET_M:
            steering = "LEFT"
            speed_action = "SLOW"

        elif heading_error_deg < -MILD_HEADING_DEG or lane_offset_m < -MILD_OFFSET_M:
            steering = "RIGHT"
            speed_action = "SLOW"

        # Then turn left to avoid obstacle
        else:
            steering = "LEFT"
            speed_action = "SLOW"

    # If close but NOT too close
    elif obstacle_distance_m <= CAUTION_OBSTACLE_M:
        print("CAR CLOSE TO OBSTACLE")
        # Stop if no where to turn
        if not left_clear and not right_clear:
            steering = "STRAIGHT"
            speed_action = "STOP"

        # Turn left if right not clear
        elif left_clear and not right_clear:
            steering = "LEFT"
            speed_action = "SLOW"

        # Turn right if left not clear
        elif right_clear and not left_clear:
            steering = "RIGHT"
            speed_action = "SLOW"

        # If both ways clear, first adjust to align vehichle 
        elif heading_error_deg > MILD_HEADING_DEG or lane_offset_m > MILD_OFFSET_M:
            steering = "LEFT"
            speed_action = "SLOW"

        elif heading_error_deg < -MILD_HEADING_DEG or lane_offset_m < -MILD_OFFSET_M:
            steering = "RIGHT"
            speed_action = "SLOW"

        #TODO go straight if there is an obstacle ahead??
        else:
            steering = "STRAIGHT"
            speed_action = "SLOW"

    # ----------- IF THERE IS NO OBSTACLES -----------
    # If aligned (within tolerance specified) just go straight
    elif centered and small_heading_error: 
        print("Mostly centered can go straight")
        steering = "STRAIGHT"
        speed_action = "ACCELERATE"

    # LOW HEADING / OFFSET ERROR CORRECTION
    elif (heading_error_deg > MILD_HEADING_DEG and heading_error_deg < LARGE_HEADING_DEG) or (lane_offset_m > MILD_OFFSET_M and lane_offset_m < LARGE_OFFSET_M):
        print("STEER LEFT, small HEADING ERROR RIGHT")
        steering = "LEFT"
        # if high speed then slow down
        if (speed_mps <= HIGH_SPEED_MPS): speed_action = "ACCELERATE"
        else: speed_action = "SLOW"

    elif (heading_error_deg < -MILD_HEADING_DEG and heading_error_deg > -LARGE_HEADING_DEG) or (lane_offset_m < -MILD_OFFSET_M and lane_offset_m > -LARGE_OFFSET_M):
        print("STEER RIGHT, small HEADING ERROR left")
        steering = "RIGHT"
        # if high speed then slow down
        if (speed_mps <= HIGH_SPEED_MPS): speed_action = "ACCELERATE"
        else: speed_action = "SLOW"

    # LARGE HEADING / OFFSET ERROR CORRECTION
    if heading_error_deg > LARGE_HEADING_DEG or lane_offset_m > LARGE_OFFSET_M:
        print("STEER LEFT, LARGE HEADING ERROR RIGHT")
        steering = "LEFT"
        # if high speed then slow down
        if (speed_mps <= HIGH_SPEED_MPS): speed_action = "ACCELERATE"
        else: speed_action = "SLOW"

    if heading_error_deg < -LARGE_HEADING_DEG or lane_offset_m < -LARGE_OFFSET_M:
        print("STEER RIGHT, LARGE HEADING ERROR LEFT")
        steering = "RIGHT"
        # if high speed then slow down
        if (speed_mps <= HIGH_SPEED_MPS): speed_action = "ACCELERATE"
        else: speed_action = "SLOW"

    #TODO Could consider different combinations, of low off set + high heading error and what to do

    return steering, speed_action
