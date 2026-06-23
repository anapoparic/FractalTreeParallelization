import turtle as tu


roo = tu.Turtle() 
wn = tu.Screen() 
wn.bgcolor("white")
wn.title("Fractal Tree Pattern")
roo.left(90) 
roo.speed(20)


def  draw(len, limit=10): 
    if(len < 10):
        return
    else:
        roo.pensize(2)
        roo.pencolor("#1db82b")
        roo.forward(len)
        roo.left(30)
        draw(0.67*len)
        roo.right(60)
        draw(0.67*len)
        roo.left(30) 
        roo.pensize(2)
        roo.backward(len) 
        
if __name__ == "__main__":
    roo.penup()
    roo.goto(0, -280)
    roo.pendown()
    draw(120)
    roo.hideturtle()
    tu.done()             