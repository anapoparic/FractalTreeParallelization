import turtle as tu

# Parameters matching the asymmetric implementation
TRUNK_LENGTH = 120
LEFT_RATIO   = 0.67
RIGHT_RATIO  = 0.57
LEFT_ANGLE   = 35
RIGHT_ANGLE  = 25
MIN_LENGTH   = 3.0

t = tu.Turtle()
wn = tu.Screen()
wn.bgcolor("#0f0f14")
wn.title("Asymmetric Fractal Tree  |  L_ratio=0.67 L_angle=35°  R_ratio=0.57 R_angle=25°")
t.left(90)
t.speed(20)


def draw(length):
    if length < MIN_LENGTH:
        return

    t.pencolor("#b46dc8")
    t.pensize(2)

    t.forward(length)

    # Left branch
    t.left(LEFT_ANGLE)
    draw(length * LEFT_RATIO)
    t.right(LEFT_ANGLE)

    # Right branch
    t.right(RIGHT_ANGLE)
    draw(length * RIGHT_RATIO)
    t.left(RIGHT_ANGLE)

    t.backward(length)


if __name__ == "__main__":
    t.penup()
    t.goto(0, -280)
    t.pendown()
    draw(TRUNK_LENGTH)
    tu.done()
