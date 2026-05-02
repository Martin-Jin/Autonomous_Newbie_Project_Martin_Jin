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
    DANGER_OBSTACLE_M = 1.5
    SAFETY_CORRECTION_M = 1 # minimum distance to attempt correction when too close
    CAUTION_OBSTACLE_M = speed_mps * 2
    CAUTION_OBSTACLE_M = max(min(CAUTION_OBSTACLE_M, 4), 2)

    MILD_HEADING_DEG = 3.0 # tolerance for low heading error
    LARGE_HEADING_DEG = 15.0 # tolerance for large heading error
    SAFETY_CORRECTION_HEADING_DEG = 45 # Vehicle should have at least turned this much if trying to avoid obstacle when too close

    MILD_OFFSET_M = 0.15 # tolerance for low off set error
    LARGE_OFFSET_M = 0.40 # tolerance for large off set error
    SAFETY_OFFSET_M = 0.2 # if vehicle almost completes turn, can keep turning even when close to obstacle

    HIGH_SPEED_MPS = 3.0
    CLOSE_CORRECTION_SPEED_MPS = 1.5 # Acceptable speed to try avoiding an obstacle when too close
    CAUTION_CORRECTION_SPEED_MPS = 2 # Acceptable speed to try avoiding an obstacle when close

    centered = abs(lane_offset_m) <= MILD_OFFSET_M # within low off set error considered straight
    small_heading_error = abs(heading_error_deg) <= MILD_HEADING_DEG # like wise for heading error

    well_aligned = False
    aligned = False
    partially_aligned = False
    conflict = False

    steering = "STRAIGHT"
    speed_action = "ACCELERATE"

    # Determine the orientation the vehicle, for when approaching an obstacle
    if left_clear and not right_clear:
        desired = "LEFT"
    elif right_clear and not left_clear:
        desired = "RIGHT"
    elif left_clear and right_clear:
        desired = "LEFT"  # default bias
    else:
        return "STRAIGHT", "STOP"

    if desired == "LEFT":
        # VERY GOOD: Turning left + facing left + left offset
        if heading_error_deg < -MILD_HEADING_DEG and lane_offset_m < -MILD_OFFSET_M:
            well_aligned = True
            print("WELL ALIGNED")

        # GOOD: Facing towards strongly towards the left
        if heading_error_deg < -SAFETY_CORRECTION_HEADING_DEG:
            aligned = True

        # PARTIAL: one helping, one neutral
        elif heading_error_deg < -MILD_HEADING_DEG or lane_offset_m < -MILD_OFFSET_M:
            partially_aligned = True

        # CONFLICT: both wrong direction
        elif heading_error_deg > MILD_HEADING_DEG and lane_offset_m > MILD_OFFSET_M:
            conflict = True

    elif desired == "RIGHT":
        if heading_error_deg > MILD_HEADING_DEG and lane_offset_m > MILD_OFFSET_M:
            well_aligned = True

        if heading_error_deg > SAFETY_CORRECTION_HEADING_DEG:
            aligned = True

        elif heading_error_deg > MILD_HEADING_DEG or lane_offset_m > MILD_OFFSET_M:
            partially_aligned = True

        elif heading_error_deg < -MILD_HEADING_DEG and lane_offset_m < -MILD_OFFSET_M:
            conflict = True

    if not sensor_valid:
        return "STRAIGHT", "STOP"
    
    # ----------- OBSTACLE AVOIDANCE LOGIC -----------
    # When TOO CLOSE to an obstacle
    if obstacle_distance_m <= DANGER_OBSTACLE_M:
        print("CAR TOO CLOSE")

        steering = desired

        # STOP if e stop or too close 
        if e_stop or (obstacle_distance_m < SAFETY_CORRECTION_M and abs(lane_offset_m) < SAFETY_OFFSET_M and not well_aligned): 
            print("TOO CLOSE STOP")
            steering = "STRAIGHT"
            speed_action = "STOP"
            return steering, speed_action

        if (well_aligned or aligned) and speed_mps <= CLOSE_CORRECTION_SPEED_MPS:
            speed_action = "SLOW"

        elif conflict or partially_aligned:
            speed_action = "STOP"
        else:
            speed_action = "STOP"

        return steering, speed_action

    # If close but NOT too close
    elif obstacle_distance_m <= CAUTION_OBSTACLE_M:
        print("CAR CLOSE TO OBSTACLE")

        # Turn left if right not clear
        if left_clear and not right_clear:
            steering = "LEFT"
            speed_action = "SLOW"       

        # Turn right if left not clear
        elif right_clear and not left_clear:
            steering = "RIGHT"
            speed_action = "SLOW"

        # Turn left is both ways clear
        else:
            steering = "LEFT"
            speed_action = "SLOW"

        # STOP if going too fast to correct
        if speed_mps > CAUTION_CORRECTION_SPEED_MPS:
            speed_action = "STOP"

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
    elif heading_error_deg > LARGE_HEADING_DEG or lane_offset_m > LARGE_OFFSET_M:
        print("STEER LEFT, LARGE HEADING ERROR RIGHT")
        steering = "LEFT"
        # if high speed then slow down
        if (speed_mps <= HIGH_SPEED_MPS): speed_action = "ACCELERATE"
        else: speed_action = "SLOW"

    elif heading_error_deg < -LARGE_HEADING_DEG or lane_offset_m < -LARGE_OFFSET_M:
        print("STEER RIGHT, LARGE HEADING ERROR LEFT")
        steering = "RIGHT"
        # if high speed then slow down
        if (speed_mps <= HIGH_SPEED_MPS): speed_action = "ACCELERATE"
        else: speed_action = "SLOW"

    return steering, speed_action
