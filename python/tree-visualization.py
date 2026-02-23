import turtle as tu


roo = tu.Turtle() 
wn = tu.Screen() 
wn.bgcolor("#0f0f14")
wn.title("Fractal Tree Pattern")
roo.left(90) 
roo.speed(20)


def  draw(len, limit=10): 
    if(len < 10):
        return
    else:
        roo.pensize(2)
        roo.pencolor("#b4dc64")
        roo.forward(len) 
        roo.left(30) 
        draw(3*len/4) 
        roo.right(60) 
        draw(3*len/4) 
        roo.left(30) 
        roo.pensize(2)
        roo.backward(len) 
        
if __name__ == "__main__":
    roo.penup()           
    roo.goto(0, -200)     
    roo.pendown()
    draw (70)
    roo.right(90)
    roo.speed(2000)
    tu.done()             