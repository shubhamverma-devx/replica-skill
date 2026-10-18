"""Exercise motions for the RepRise library.

Angle conventions, all relative to the parent bone, degrees, clockwise positive:

    torso      180 upright; higher leans the chest forward (the figure faces right)
    thigh        0 straight down; negative swings the knee forward
    shin         0 straight; positive folds the heel back
    upper arm  180 hanging; lower raises the arm forward, higher swings it back
    forearm      0 straight; negative flexes the elbow

Every motion starts and ends on the same pose so the loop is seamless.
"""

STAND = {}

MOTIONS = {
    "marching_in_place": dict(
        title="Marching in Place",
        duration=1.6,
        keyframes=[
            (0.00, {"legNearU": 0, "legNearL": 0, "legFarU": 0, "legFarL": 0,
                    "armNearU": 192, "armFarU": 168}),
            (0.25, {"legNearU": -62, "legNearL": 78, "legFarU": 6, "legFarL": 4,
                    "armNearU": 222, "armFarU": 132, "armFarL": -28}),
            (0.50, {"legNearU": 0, "legNearL": 0, "legFarU": 0, "legFarL": 0,
                    "armNearU": 192, "armFarU": 168}),
            (0.75, {"legFarU": -62, "legFarL": 78, "legNearU": 6, "legNearL": 4,
                    "armFarU": 138, "armNearU": 246, "armNearL": -28}),
            (1.00, {"legNearU": 0, "legNearL": 0, "legFarU": 0, "legFarL": 0,
                    "armNearU": 192, "armFarU": 168}),
        ],
        root_motion=[(0.0, 0, 0, 0), (0.25, 0, -6, 0), (0.5, 0, 0, 0),
                     (0.75, 0, -6, 0), (1.0, 0, 0, 0)],
    ),

    "arm_circles": dict(
        title="Arm Circles",
        duration=2.4,
        keyframes=[
            (0.00, {"armNearU": 192, "armFarU": 168}),
            (0.25, {"armNearU": 102, "armFarU": 78}),
            (0.50, {"armNearU": 12, "armFarU": -12}),
            (0.75, {"armNearU": -78, "armFarU": -102}),
            (1.00, {"armNearU": -168, "armFarU": -192}),
        ],
    ),

    "bodyweight_squat": dict(
        title="Bodyweight Squat",
        duration=2.4,
        keyframes=[
            (0.00, {"torso": 180, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "armNearU": 192, "armFarU": 168}),
            (0.45, {"torso": 196, "legNearU": -70, "legNearL": 72, "legFarU": -70,
                    "legFarL": 72, "armNearU": 96, "armFarU": 86,
                    "footNear": -78, "footFar": -78}),
            (0.60, {"torso": 196, "legNearU": -70, "legNearL": 72, "legFarU": -70,
                    "legFarL": 72, "armNearU": 96, "armFarU": 86,
                    "footNear": -78, "footFar": -78}),
            (1.00, {"torso": 180, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "armNearU": 192, "armFarU": 168}),
        ],
        root_motion=[(0.0, 0, 0, 0), (0.45, -12, 50, 0), (0.6, -12, 50, 0),
                     (1.0, 0, 0, 0)],
    ),

    "push_up": dict(
        title="Push-Up",
        duration=2.2,
        root=(281, 300), root_rot=90,
        keyframes=[
            (0.00, {"torso": 180, "armNearU": 90, "armNearL": 0, "armFarU": 90,
                    "armFarL": 0, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (0.45, {"torso": 180, "armNearU": 126, "armNearL": -62, "armFarU": 126,
                    "armFarL": -62, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (0.60, {"torso": 180, "armNearU": 126, "armNearL": -62, "armFarU": 126,
                    "armFarL": -62, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (1.00, {"torso": 180, "armNearU": 90, "armNearL": 0, "armFarU": 90,
                    "armFarL": 0, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
        ],
        root_motion=[(0.0, 0, 0, 90), (0.45, 0, 0, 97), (0.6, 0, 0, 97),
                     (1.0, 0, 0, 90)],
    ),

    "reverse_lunge": dict(
        title="Reverse Lunge",
        duration=2.6,
        keyframes=[
            (0.00, {"torso": 180, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0}),
            (0.40, {"torso": 184, "legNearU": -16, "legNearL": 30, "legFarU": 34,
                    "legFarL": 74, "footFar": -140, "armNearU": 200, "armFarU": 160}),
            (0.60, {"torso": 184, "legNearU": -16, "legNearL": 30, "legFarU": 34,
                    "legFarL": 74, "footFar": -140, "armNearU": 200, "armFarU": 160}),
            (1.00, {"torso": 180, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0}),
        ],
        root_motion=[(0.0, 0, 0, 0), (0.4, -8, 46, 0), (0.6, -8, 46, 0),
                     (1.0, 0, 0, 0)],
    ),

    "forearm_plank": dict(
        title="Forearm Plank",
        duration=3.0,
        root=(292, 300), root_rot=90,
        keyframes=[
            (0.00, {"torso": 180, "armNearU": 86, "armNearL": -86, "armFarU": 86,
                    "armFarL": -86, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (0.50, {"torso": 183, "armNearU": 86, "armNearL": -86, "armFarU": 86,
                    "armFarL": -86, "legNearU": -2, "legNearL": 0, "legFarU": -2,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (1.00, {"torso": 180, "armNearU": 86, "armNearL": -86, "armFarU": 86,
                    "armFarL": -86, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
        ],
        root_motion=[(0.0, 0, 0, 90), (0.5, 0, 0, 91.2), (1.0, 0, 0, 90)],
    ),

    "mountain_climber": dict(
        title="Mountain Climber",
        duration=1.6,
        root=(281, 300), root_rot=90,
        keyframes=[
            (0.00, {"torso": 180, "armNearU": 90, "armNearL": 0, "armFarU": 90,
                    "armFarL": 0, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (0.25, {"torso": 180, "armNearU": 90, "armNearL": 0, "armFarU": 90,
                    "armFarL": 0, "legNearU": -146, "legNearL": 120, "legFarU": 4,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (0.50, {"torso": 180, "armNearU": 90, "armNearL": 0, "armFarU": 90,
                    "armFarL": 0, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
            (0.75, {"torso": 180, "armNearU": 90, "armNearL": 0, "armFarU": 90,
                    "armFarL": 0, "legFarU": -146, "legFarL": 120, "legNearU": 4,
                    "legNearL": 0, "footNear": -58, "footFar": -58}),
            (1.00, {"torso": 180, "armNearU": 90, "armNearL": 0, "armFarU": 90,
                    "armFarL": 0, "legNearU": 0, "legNearL": 0, "legFarU": 0,
                    "legFarL": 0, "footNear": -58, "footFar": -58}),
        ],
    ),

    "hamstring_stretch": dict(
        title="Standing Hamstring Stretch",
        duration=3.2,
        keyframes=[
            (0.00, {"torso": 180, "legNearU": 0, "legNearL": 0}),
            (0.35, {"torso": 226, "legNearU": -26, "legNearL": 2, "footNear": -132,
                    "legFarU": 8, "legFarL": 22, "armNearU": 148, "armFarU": 140,
                    "armNearL": -10, "armFarL": -10}),
            (0.70, {"torso": 229, "legNearU": -28, "legNearL": 2, "footNear": -132,
                    "legFarU": 8, "legFarL": 22, "armNearU": 152, "armFarU": 144,
                    "armNearL": -10, "armFarL": -10}),
            (1.00, {"torso": 180, "legNearU": 0, "legNearL": 0}),
        ],
        root_motion=[(0.0, 0, 0, 0), (0.35, -6, 16, 0), (0.7, -6, 16, 0),
                     (1.0, 0, 0, 0)],
    ),

    "chest_opener": dict(
        title="Chest Opener",
        duration=2.8,
        keyframes=[
            (0.00, {"torso": 182, "armNearU": 112, "armNearL": -74,
                    "armFarU": 100, "armFarL": -74}),
            (0.45, {"torso": 174, "armNearU": 258, "armNearL": -22,
                    "armFarU": 240, "armFarL": -22}),
            (0.65, {"torso": 174, "armNearU": 258, "armNearL": -22,
                    "armFarU": 240, "armFarL": -22}),
            (1.00, {"torso": 182, "armNearU": 112, "armNearL": -74,
                    "armFarU": 100, "armFarL": -74}),
        ],
    ),
}
